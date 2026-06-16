"""Web download backend: yt-dlp, aria2, ffmpeg m3u8, candidate inspection, batch orchestrator."""
from __future__ import annotations

import asyncio
import json
import importlib.util
import os
import re
import functools
import shutil
import subprocess
import threading as _threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError, as_completed
from contextlib import contextmanager, nullcontext
from dataclasses import replace
from html import unescape
from pathlib import Path
from random import uniform
from threading import Event, Lock
from time import monotonic, sleep
from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, build_opener, urlopen, ProxyHandler

from .models import (
    CancelledError, DownloadError, DownloadOptions, DownloadTask,
    ProgressCallback, TelegramConfig, Token,
)
from . import _shared as _s
from .progress import (
    _emit, _emit_task_start, _emit_task_done, _emit_file_select,
    _emit_web_transfer_progress, _make_result,
    _build_download_log_message, _format_byte_rate, _format_eta_seconds,
    _format_progress_percent, _parse_ffmpeg_time,
    _estimate_download_rate, _normalize_progress_text,
    _resolve_web_percent_text, _resolve_web_speed_text,
)
from .source_parser import (
    _check_cancel,
    _coerce_tasks, validate_download_request,
    normalize_proxy_url, parse_task_lines,
    classify_source, _resolve_candidate_indices,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ARIA2_PROGRESS_RE = re.compile(r'\((?P<percent>\d+(?:\.\d+)?)%\).*?\bDL:(?P<speed>[^\s\]]+)(?:.*?\bETA:(?P<eta>[^\s\]]+))?', re.IGNORECASE)
MEDIA_URL_RE = re.compile(r"""(?P<url>(?:https?:)?//[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
RELATIVE_MEDIA_RE = re.compile(r"""(?P<url>/[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
_ARIA2_ETA_RE = re.compile(r'(\d+)([hms])')
_DOUYIN_PLAYWM_RE = re.compile(r'/playwm(?=[/?])')
ARIA2_VERSION = '1.37.0'
ARIA2_SOURCE_URL = 'https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip'
COOKIE_RETRY_BROWSERS = ('chrome', 'firefox', 'edge')
COOKIE_FILE_NAMES = (
    'douyin.cookies.txt',
    'douyin-cookies.txt',
    'cookies.txt',
    'video-downloader-cookies.txt',
)
DOUYIN_HOSTS = {'douyin.com', 'www.douyin.com', 'iesdouyin.com', 'www.iesdouyin.com', 'v.douyin.com'}


class _PausedDownload(RuntimeError):
    pass


def _run_async(coro):
    """Run an async coroutine safely, even if an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


@functools.lru_cache(maxsize=1)
def _ffmpeg_path() -> str:
    return shutil.which('ffmpeg') or ''
_console_capture_lock = Lock()
_INTER_TASK_DELAY_RANGE = (0.5, 1.5)


# ---------------------------------------------------------------------------
# Aria2 helpers
# ---------------------------------------------------------------------------
@contextmanager
def _capture_aria2_console_progress(progress_cb: ProgressCallback | None, file_name: str):
    if progress_cb is None:
        yield
        return
    # os.dup2 redirects process-level file descriptors, so concurrent captures
    # must be serialized to avoid mixing aria2 progress between tasks.
    with _console_capture_lock:
        saved_stdout = os.dup(1)
        saved_stderr = os.dup(2)
        read_fd, write_fd = os.pipe()
        stop = Event()

        def reader() -> None:
            buffer = ''
            try:
                with os.fdopen(read_fd, 'rb', closefd=True) as pipe:
                    while not stop.is_set():
                        chunk = pipe.read(512)
                        if not chunk:
                            break
                        buffer += chunk.decode('utf-8', errors='ignore')
                        parts = re.split(r'[\r\n]+', buffer)
                        buffer = parts.pop() if parts else ''
                        for part in parts:
                            _emit_aria2_progress(progress_cb, file_name, part)
                    if buffer:
                        _emit_aria2_progress(progress_cb, file_name, buffer)
            except OSError:
                pass

        thread = _threading.Thread(target=reader, daemon=True)
        try:
            os.dup2(write_fd, 1)
            os.dup2(write_fd, 2)
            os.close(write_fd)
            thread.start()
            yield
        finally:
            os.dup2(saved_stdout, 1)
            os.dup2(saved_stderr, 2)
            os.close(saved_stdout)
            os.close(saved_stderr)
            stop.set()
            thread.join(timeout=1)


def _emit_aria2_progress(progress_cb: ProgressCallback | None, file_name: str, raw_line: str) -> None:
    text = _normalize_progress_text(raw_line)
    if not text or '[#' not in text:
        return
    match = ARIA2_PROGRESS_RE.search(text)
    if not match:
        return
    percent = match.group('percent') or ''
    speed = _normalize_aria2_speed(match.group('speed') or '')
    eta = _normalize_aria2_eta(match.group('eta') or '')
    clean_name = _s.sanitize_filename_component(file_name or 'video', fallback='video')
    parts = [f'name={clean_name}', f'speed={speed}']
    if percent:
        parts.append(f'percent={percent}')
    if eta:
        parts.append(f'eta={eta}')
    _emit(progress_cb, '__HYL_PROGRESS__|web_aria2|' + '|'.join(parts))
    _emit(progress_cb, _build_download_log_message(clean_name, speed, '', eta))


def _normalize_aria2_speed(text: str) -> str:
    speed = str(text or '').strip()
    if not speed:
        return ''
    return speed if speed.endswith('/s') else f'{speed}/s'


def _normalize_aria2_eta(text: str) -> str:
    value = str(text or '').strip()
    if not value:
        return ''
    total = 0
    for amount, unit in _ARIA2_ETA_RE.findall(value.lower()):
        number = int(amount)
        if unit == 'h':
            total += number * 3600
        elif unit == 'm':
            total += number * 60
        else:
            total += number
    return _format_eta_seconds(total) if total > 0 else value


# ---------------------------------------------------------------------------
# Web backend guard
# ---------------------------------------------------------------------------
def _require_web_backend() -> None:
    if importlib.util.find_spec('yt_dlp') is None:
        raise DownloadError('未安装 yt-dlp，无法解析网页视频')


def _options_proxy_url(options: DownloadOptions | None) -> str:
    return normalize_proxy_url(getattr(options, 'proxy_url', '') if options is not None else '')


def _urlopen_with_proxy(request: Request, timeout: int, proxy_url: str = ''):
    proxy = normalize_proxy_url(proxy_url)
    if not proxy:
        return urlopen(request, timeout=timeout)
    opener = build_opener(ProxyHandler({'http': proxy, 'https': proxy}))
    return opener.open(request, timeout=timeout)


# ---------------------------------------------------------------------------
# Speed tracking
# ---------------------------------------------------------------------------
class _SpeedTracker:
    """Wraps a progress callback and records max download speed from web_status markers."""
    def __init__(self, delegate: ProgressCallback | None):
        self._delegate = delegate
        self.max_speed: float = 0.0
        self._lock = Lock()

    def emit(self, message: str) -> None:
        if self._delegate:
            self._delegate(message)
        if not message.startswith('__HYL_PROGRESS__|web_status|'):
            return
        parts = message.split('|')
        speed_str = ''
        for part in parts:
            if part.startswith('speed='):
                speed_str = part.split('=', 1)[1]
                break
        speed = _parse_speed_bytes(speed_str)
        if speed > 0:
            with self._lock:
                if speed > self.max_speed:
                    self.max_speed = speed


def _parse_speed_bytes(text: str) -> float:
    """Parse speed string like '2.5 MiB/s' to bytes/sec."""
    text = str(text or '').strip()
    if not text:
        return 0.0
    parts = text.split()
    if not parts:
        return 0.0
    try:
        value = float(parts[0])
    except ValueError:
        return 0.0
    if len(parts) < 2:
        return value
    unit = parts[1].lower()
    multipliers = {'b/s': 1, 'kib/s': 1024, 'mib/s': 1024**2, 'gib/s': 1024**3}
    return value * multipliers.get(unit, 1)


def _cookie_browser_name(value: object) -> str:
    if isinstance(value, (tuple, list)) and value:
        return str(value[0] or '').strip().lower()
    if isinstance(value, str):
        return value.strip().lower()
    return ''


def _needs_browser_cookie_retry(source_url: str, exc: Exception) -> bool:
    text = str(exc or '').lower()
    if not text:
        return False
    if 'fresh cookies' in text:
        return True
    host = urlparse(str(source_url or '')).netloc.lower()
    return ('douyin.com' in host or 'iesdouyin.com' in host) and 'cookie' in text


def _iter_cookie_retry_browsers(base_opts: dict[str, object]) -> list[str]:
    browsers: list[str] = []
    preferred = _cookie_browser_name(base_opts.get('cookiesfrombrowser'))
    if preferred:
        browsers.append(preferred)
    for browser in COOKIE_RETRY_BROWSERS:
        if browser not in browsers:
            browsers.append(browser)
    return browsers


def _iter_cookie_file_candidates() -> list[Path]:
    roots: list[Path] = [
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parents[2],
    ]
    user_home = Path.home()
    roots.extend(user_home / name for name in ('Downloads', 'Desktop', 'Documents'))
    unique: dict[str, Path] = {}
    for root in roots:
        for file_name in COOKIE_FILE_NAMES:
            candidate = root / file_name
            if candidate.is_file() and candidate.stat().st_size > 0:
                unique.setdefault(str(candidate.resolve()), candidate.resolve())
    return list(unique.values())


def _can_retry_with_cookie_file(source_url: str, exc: Exception) -> bool:
    text = str(exc or '').lower()
    if not text:
        return False
    if 'could not copy' in text and 'cookie database' in text:
        return True
    host = urlparse(str(source_url or '')).netloc.lower()
    return ('douyin.com' in host or 'iesdouyin.com' in host) and 'cookie' in text


def _is_cookie_access_blocked_error(exc: Exception) -> bool:
    text = str(exc or '').lower()
    return 'could not copy chrome cookie database' in text or (
        'permission denied' in text and 'cookie' in text
    )


def _is_douyin_url(url: str) -> bool:
    host = urlparse(str(url or '')).netloc.lower()
    return host in DOUYIN_HOSTS


def _normalize_douyin_play_url(url: str) -> str:
    text = str(url or '').strip()
    if not text:
        return ''
    return _DOUYIN_PLAYWM_RE.sub('/play', text)


def _is_douyin_direct_play_url(url: str) -> bool:
    parsed = urlparse(str(url or ''))
    return parsed.scheme in {'http', 'https'} and '/aweme/v1/play/' in parsed.path


def _fetch_douyin_share_html(url: str, proxy_url: str = '') -> str:
    request = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    )
    with _urlopen_with_proxy(request, 20, proxy_url) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return response.read().decode(charset, errors='ignore')


def _extract_douyin_page_json(html_text: str) -> dict[str, object] | None:
    marker = 'window._ROUTER_DATA = '
    start = str(html_text or '').find(marker)
    if start < 0:
        return None
    start = str(html_text).find('{', start)
    if start < 0:
        return None
    depth = 0
    end = None
    for index, ch in enumerate(str(html_text)[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        return None
    try:
        parsed = json.loads(str(html_text)[start:end])
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _find_douyin_item_list(data: object) -> list[dict[str, object]]:
    if isinstance(data, dict):
        if isinstance(data.get('videoInfoRes'), dict):
            items = data['videoInfoRes'].get('item_list')
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        for value in data.values():
            found = _find_douyin_item_list(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_douyin_item_list(item)
            if found:
                return found
    return []


def _extract_douyin_share_candidates(source_url: str, options: DownloadOptions | None = None) -> list[str]:
    if not _is_douyin_url(source_url):
        return []
    try:
        html = _fetch_douyin_share_html(source_url, _options_proxy_url(options))
    except (OSError, ValueError, TimeoutError):
        return []
    page_data = _extract_douyin_page_json(html)
    if not page_data:
        return []
    for item in _find_douyin_item_list(page_data):
        video = item.get('video')
        if not isinstance(video, dict):
            continue
        play_addr = video.get('play_addr')
        if not isinstance(play_addr, dict):
            continue
        urls = play_addr.get('url_list')
        if not isinstance(urls, list):
            continue
        candidates: list[str] = []
        for raw in urls:
            candidate = _normalize_douyin_play_url(str(raw or ''))
            if candidate:
                candidates.append(candidate)
        if candidates:
            return list(dict.fromkeys(candidates))
    return []


def _download_direct_media_file(
    media_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    *,
    referer_url: str = '',
    token: Token | None = None,
) -> dict[str, object]:
    proxy_url = _options_proxy_url(options)
    suffix = Path(urlparse(str(media_url or '')).path).suffix.lower() or '.mp4'
    if suffix not in {'.mp4', '.mov', '.m4v', '.webm'}:
        suffix = '.mp4'
    base_stem = _s.ensure_unique_stem(output_root, _s.sanitize_filename_component(task.target_title or 'video'))
    output_path = _s.ensure_unique_path(output_root / f'{base_stem}{suffix}')
    max_reconnects = 3
    downloaded_total = 0
    reconnect_count = 0
    for reconnect_attempt in range(max_reconnects + 1):
        headers = _s._build_web_headers(referer_url)
        if downloaded_total > 0:
            headers['Range'] = f'bytes={downloaded_total}-'
        request = Request(media_url, headers=headers)
        downloaded = 0
        started_at = monotonic()
        last_emit_at = started_at
        should_reconnect = False
        try:
            with _urlopen_with_proxy(request, 60, proxy_url) as response:
                # Verify server actually supports range requests
                if downloaded_total > 0 and getattr(response, 'status', 200) != 206:
                    downloaded_total = 0
                mode = 'ab' if downloaded_total > 0 else 'wb'
                with output_path.open(mode) as fh:
                    raw_total = int(response.headers.get('Content-Length') or 0)
                    # For 206 responses, Content-Length is remaining bytes; compute full size
                    # If Content-Length is missing (some servers), progress percentage won't be shown
                    total_bytes = downloaded_total + raw_total if downloaded_total > 0 else raw_total
                    while True:
                        if token is not None:
                            _check_cancel(token)
                        _wait_if_paused(token, progress_cb)
                        if token and token.reconnect.is_set():
                            token.reconnect.clear()
                            should_reconnect = True
                            break
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        fh.write(chunk)
                        downloaded += len(chunk)
                        now = monotonic()
                        effective_downloaded = downloaded_total + downloaded
                        if effective_downloaded < total_bytes and now - last_emit_at < 0.35:
                            continue
                        elapsed = max(now - started_at, 1e-6)
                        speed_text = _format_byte_rate(downloaded / elapsed)
                        percent_text = ''
                        eta_text = ''
                        if total_bytes > 0:
                            percent_text = f'{effective_downloaded * 100.0 / total_bytes:.2f}'
                            if effective_downloaded > 0 and effective_downloaded < total_bytes:
                                remaining = total_bytes - effective_downloaded
                                eta_text = _format_eta_seconds(int(remaining / max(downloaded / elapsed, 1e-6)))
                        _emit_web_transfer_progress(progress_cb, output_path.name, percent_text, speed_text, eta_text)
                        last_emit_at = now
        except CancelledError:
            raise
        except Exception:
            if output_path.exists() and output_path.stat().st_size <= 0:
                output_path.unlink(missing_ok=True)
            raise
        downloaded_total += downloaded
        if not should_reconnect:
            break
        reconnect_count += 1
        if reconnect_count > max_reconnects:
            raise DownloadError('重连次数已达上限')
        _emit(progress_cb, f'重连中... (第{reconnect_count}次)')
    _emit(progress_cb, f'网页 OK -> {output_path.name}')
    return {
        'success': True,
        'files': [output_path],
    }


def _build_cookie_retry_failure_message(source_url: str, exc: Exception) -> str:
    host = urlparse(str(source_url or '')).netloc or '当前站点'
    detail = str(exc or '').strip()
    return (
        f'{detail}\n'
        f'{host} 需要 fresh cookies，但当前浏览器 Cookies 无法读取。\n'
        '可按 GitHub 上 yt-dlp/yt-dlp#7271 的常见做法处理：\n'
        '1. 彻底关闭 Chrome/Edge 后重试\n'
        '2. 用 --disable-features=LockProfileCookieDatabase 启动 Chrome/Edge\n'
        '3. 导出 30 分钟内新鲜的 Netscape 格式 cookies.txt，放到工具目录/桌面/下载/文档\n'
        '4. 或安装 yt-dlp-ChromeCookieUnlock 插件'
    )


def _run_ytdlp_with_cookie_retry(
    source_url: str,
    base_opts: dict[str, object],
    progress_cb: ProgressCallback | None,
    runner,
):
    initial_opts = dict(base_opts)
    initial_browser = _cookie_browser_name(initial_opts.get('cookiesfrombrowser'))
    try:
        return runner(initial_opts)
    except CancelledError:
        raise
    except Exception as exc:
        if not _needs_browser_cookie_retry(source_url, exc):
            raise
        last_exc = exc
    host = urlparse(str(source_url or '')).netloc or '当前站点'
    for browser in _iter_cookie_retry_browsers(initial_opts):
        if browser == initial_browser:
            continue
        retry_opts = dict(base_opts)
        retry_opts['cookiesfrombrowser'] = (browser,)
        _emit(progress_cb, f'检测到 {host} 需要浏览器 Cookies，尝试使用 {browser} 重试')
        try:
            return runner(retry_opts)
        except CancelledError:
            raise
        except Exception as exc:
            last_exc = exc
    if _can_retry_with_cookie_file(source_url, last_exc):
        for cookie_file in _iter_cookie_file_candidates():
            retry_opts = dict(base_opts)
            retry_opts.pop('cookiesfrombrowser', None)
            retry_opts['cookiefile'] = str(cookie_file)
            _emit(progress_cb, f'浏览器 Cookies 读取失败，尝试 cookies.txt -> {cookie_file}')
            try:
                return runner(retry_opts)
            except CancelledError:
                raise
            except Exception as exc:
                last_exc = exc
        message = _build_cookie_retry_failure_message(source_url, last_exc)
        _emit(progress_cb, message)
        raise DownloadError(message)
    raise last_exc if not _is_cookie_access_blocked_error(last_exc) else DownloadError(
        _build_cookie_retry_failure_message(source_url, last_exc)
    )


def _speed_to_concurrency(bytes_per_sec: float) -> int:
    """Map download speed to recommended concurrent task count (1-8)."""
    if bytes_per_sec <= 0:
        return 3
    mbps = bytes_per_sec / (1024 * 1024)
    if mbps >= 10:
        return 8
    if mbps >= 5:
        return 6
    if mbps >= 2:
        return 4
    if mbps >= 0.5:
        return 3
    return 2


# ---------------------------------------------------------------------------
# Web orchestration
# ---------------------------------------------------------------------------
def _run_web_task(task, output_root, options, progress_cb, token):
    _wait_if_paused(token, progress_cb)
    return _download_web_task(task, output_root, options, progress_cb, token=token)


def _wait_if_paused(token: Token | None, progress_cb: ProgressCallback | None = None) -> None:
    """Block until pause is cleared. Raises CancelledError if cancel is set."""
    if token is None or not token.pause.is_set():
        return
    _emit(progress_cb, '下载已暂停')
    while token.pause.is_set():
        _check_cancel(token)
        sleep(0.2)
    _emit(progress_cb, '下载已恢复')


def _check_paused_non_blocking(token: Token | None) -> bool:
    """Non-blocking pause check. Returns True if paused (caller should skip work)."""
    return token is not None and token.pause.is_set()


def _download_web_entries(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
    token: Token | None = None,
) -> dict[int, dict[str, object]]:
    """Download web entries. Uses sequential loop for concurrency=1, thread pool otherwise."""
    if not web_entries:
        return {}
    max_workers = max(1, min(options.max_concurrent_downloads, len(web_entries)))
    if max_workers <= 1:
        return _download_web_sequential(web_entries, output_root, options, progress_cb, total_tasks, completed_count, token=token)
    return _download_web_concurrent(web_entries, output_root, options, progress_cb, total_tasks, completed_count, max_workers, token=token)


def _download_web_sequential(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
    token: Token | None = None,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    remaining = len(web_entries)
    for index, task in web_entries:
        _check_cancel(token)
        _wait_if_paused(token, progress_cb)
        _emit_task_start(progress_cb, index, total_tasks, task)
        try:
            results[index] = _download_web_task(task, output_root, options, progress_cb, token=token)
        except CancelledError:
            results[index] = _make_result(task, False, [], '下载已取消')
            completed_count += 1
            _emit_task_done(progress_cb, completed_count, total_tasks)
            raise
        except Exception as exc:
            results[index] = _make_result(task, False, [], str(exc))
        completed_count += 1
        _emit_task_done(progress_cb, completed_count, total_tasks)
        remaining -= 1
        if remaining > 0 and _INTER_TASK_DELAY_RANGE[1] > 0:
            delay = uniform(*_INTER_TASK_DELAY_RANGE)
            sleep(delay)
    return results


def _download_web_concurrent(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
    max_workers: int,
    token: Token | None = None,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    task_by_index = {index: task for index, task in web_entries}
    for index, task in web_entries:
        _emit_task_start(progress_cb, index, total_tasks, task)
    executor = ThreadPoolExecutor(max_workers=max_workers)
    cancelled = False
    future_map: dict[object, int] = {}
    try:
        future_map = {
            executor.submit(_run_web_task, task, output_root, options, progress_cb, token): index
            for index, task in web_entries
        }
        pending = set(future_map)
        while pending:
            _check_cancel(token)
            _wait_if_paused(token, progress_cb)
            try:
                future = next(as_completed(tuple(pending), timeout=0.2))
            except FutureTimeoutError:
                continue
            pending.remove(future)
            index = future_map[future]
            try:
                results[index] = future.result()
            except CancelledError as exc:
                results[index] = _make_result(task_by_index[index], False, [], str(exc))
                raise
            except Exception as exc:
                results[index] = _make_result(task_by_index[index], False, [], str(exc))
            completed_count += 1
            _emit_task_done(progress_cb, completed_count, total_tasks)
    except CancelledError:
        cancelled = True
        for future in future_map:
            if not future.done():
                future.cancel()
        raise
    finally:
        executor.shutdown(wait=not cancelled, cancel_futures=cancelled)
    return results


def _download_web_auto(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    initial_completed: int,
    token: Token | None = None,
) -> dict[int, dict[str, object]]:
    if not web_entries:
        return {}
    sample_count = min(2, len(web_entries))
    probe_speeds: list[float] = []
    results: dict[int, dict[str, object]] = {}
    completed = initial_completed
    for i in range(sample_count):
        tracker = _SpeedTracker(progress_cb)
        index, task = web_entries[i]
        _wait_if_paused(token, progress_cb)
        _emit_task_start(progress_cb, index, total_tasks, task)
        try:
            results[index] = _download_web_task(task, output_root, options, tracker.emit, token=token)
        except CancelledError:
            results[index] = _make_result(task, False, [], '下载已取消')
            raise
        except Exception as exc:
            results[index] = _make_result(task, False, [], str(exc))
        completed += 1
        _emit_task_done(progress_cb, completed, total_tasks)
        if tracker.max_speed > 0:
            probe_speeds.append(tracker.max_speed)
    remaining = web_entries[sample_count:]
    if not remaining:
        return results
    best_speed = max(probe_speeds) if probe_speeds else 0.0
    concurrency = _speed_to_concurrency(best_speed)
    _emit(progress_cb, f'自动模式: 采样 {sample_count} 个任务, 峰值速度 {_format_byte_rate(best_speed)}, 并发数设为 {concurrency}')
    concurrent_opts = replace(options, max_concurrent_downloads=concurrency)
    results.update(_download_web_entries(
        remaining, output_root, concurrent_opts, progress_cb, total_tasks, completed, token=token,
    ))
    return results


# ---------------------------------------------------------------------------
# Candidate expansion
# ---------------------------------------------------------------------------
def _expand_web_all_candidates(
    tasks: list[DownloadTask],
    progress_cb: ProgressCallback | None,
    options: DownloadOptions | None = None,
) -> list[DownloadTask]:
    """Expand web tasks into individual candidate tasks when download_all_candidates is set.

    Each web URL that resolves to multiple yt-dlp entries is replaced by one task per
    entry so the UI shows the real video count instead of "1 总计".
    """
    expanded: list[DownloadTask] = []
    for task in tasks:
        if task.source_kind != 'web':
            expanded.append(task)
            continue
        try:
            candidates = _extract_ytdlp_entry_candidates(task.source_url, options)
        except Exception:
            candidates = []
        if len(candidates) <= 1:
            expanded.append(task)
            continue
        _emit(progress_cb, f'展开候选: {task.source_url} → {len(candidates)} 个独立任务')
        for candidate_url in candidates:
            expanded.append(DownloadTask(
                source_url=candidate_url,
                source_kind='web',
                target_title=_s.guess_task_title(candidate_url),
                output_subdir=task.output_subdir,
            ))
    return expanded


def _resolve_web_task_output_dir(output_root: Path, task: DownloadTask) -> Path:
    subdir = _s.sanitize_filename_component(task.output_subdir, fallback='').strip()
    if not subdir:
        return output_root
    return output_root / subdir


# ---------------------------------------------------------------------------
# Batch orchestrator (main public entry point)
# ---------------------------------------------------------------------------
def download_batch(
    tasks: Iterable[str] | Iterable[DownloadTask],
    output_dir: str | Path,
    telegram_config: TelegramConfig | None,
    options: DownloadOptions | None = None,
    progress_cb: ProgressCallback | None = None,
    *,
    token: Token | None = None,
) -> list[dict[str, object]]:
    """Download a batch of tasks (Telegram and/or web).

    Args:
        tasks: URLs as strings or pre-built DownloadTask objects.
        output_dir: Root directory for downloaded files.
        telegram_config: Telegram API credentials (required for Telegram tasks).
        options: Download configuration (concurrency, proxy, filters, etc.).
        progress_cb: Callback for progress messages (``__HYL_PROGRESS__|`` markers).
        token: Control token for cancel/pause/reconnect signals.

    Returns:
        List of result dicts, one per task, each containing at least
        ``success``, ``source_url``, ``error``, ``files``.

    Raises:
        ValueError: If validation fails (missing output dir, bad config, etc.).
        CancelledError: If the token's cancel flag is set during execution.
    """
    from .telegram_backend import _download_telegram_entries

    task_list = _coerce_tasks(tasks)
    config = telegram_config
    download_options = options or DownloadOptions()
    errors = validate_download_request(
        task_list,
        str(output_dir),
        config,
        recent_limit=download_options.telegram_recent_limit,
        telegram_download_all_messages=download_options.telegram_download_all_messages,
        date_from=download_options.telegram_date_from,
        date_to=download_options.telegram_date_to,
        telegram_include_videos=download_options.telegram_include_videos,
        telegram_include_photos=download_options.telegram_include_photos,
    )
    if errors:
        raise ValueError('\n'.join(errors))
    output_root = Path(output_dir).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)
    results: dict[int, dict[str, object]] = {}
    total_tasks = len(task_list)
    try:
        telegram_entries = [(index, task) for index, task in enumerate(task_list) if task.source_kind.startswith('telegram')]
        if telegram_entries:
            telegram_results = _run_async(
                _download_telegram_entries(
                    telegram_entries,
                    output_root,
                    config,
                    download_options,
                    progress_cb,
                    total_tasks=total_tasks,
                )
            )
            results.update(telegram_results)
        web_entries = [(index, task) for index, task in enumerate(task_list) if not task.source_kind.startswith('telegram')]
        if not web_entries:
            return [results[index] for index in range(len(task_list))]
        if download_options.max_concurrent_downloads <= 0 and len(web_entries) > 1:
            results.update(_download_web_auto(web_entries, output_root, download_options, progress_cb, total_tasks, len(results), token=token))
        else:
            results.update(_download_web_entries(web_entries, output_root, download_options, progress_cb, total_tasks, len(results), token=token))
    except CancelledError:
        for index in range(len(task_list)):
            if index not in results:
                results[index] = _make_result(task_list[index], False, [], '下载已取消')
        raise
    return [results[index] for index in range(len(task_list))]


# ---------------------------------------------------------------------------
# Candidate inspection
# ---------------------------------------------------------------------------
def _is_m3u8_url(url: str) -> bool:
    return str(url or '').lower().split('?', 1)[0].endswith('.m3u8')


def _download_web_candidate(
    candidate_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
    token: Token | None = None,
) -> dict[str, object]:
    if _is_douyin_direct_play_url(candidate_url):
        return _download_direct_media_file(
            candidate_url,
            task,
            output_root,
            options,
            progress_cb,
            referer_url=task.source_url,
            token=token,
        )
    if _is_m3u8_url(candidate_url) and ffmpeg_path:
        try:
            return _download_url_with_ytdlp(
                candidate_url,
                output_root,
                options,
                progress_cb,
                title_hint=task.target_title,
                referer_url=task.source_url,
                token=token,
            )
        except CancelledError:
            raise
        except Exception as exc:
            _emit(progress_cb, f'yt-dlp 下载 m3u8 失败，改用 ffmpeg 兜底: {exc}')
            return _download_m3u8_with_ffmpeg(
                candidate_url,
                task,
                output_root,
                options,
                progress_cb,
                ffmpeg_path=ffmpeg_path,
                referer_url=task.source_url,
                token=token,
            )
    return _download_url_with_ytdlp(
        candidate_url,
        output_root,
        options,
        progress_cb,
        title_hint=task.target_title,
        referer_url=task.source_url,
        token=token,
    )


def _download_web_candidates(
    candidates: list[str],
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
    *,
    download_all: bool = False,
    token: Token | None = None,
) -> tuple[list[Path], Exception | None]:
    downloaded_files: list[Path] = []
    last_error: Exception | None = None
    total_candidates = len(candidates)
    for candidate_index, candidate in enumerate(candidates, start=1):
        _emit_file_select(progress_cb, candidate, candidate_index, total_candidates)
        try:
            downloaded = _download_web_candidate(
                candidate,
                task,
                output_root,
                options,
                progress_cb,
                ffmpeg_path=ffmpeg_path,
                token=token,
            )
            files = [Path(item) for item in downloaded['files']]
            if not options.web_download_all_candidates and not download_all:
                return files, None
            downloaded_files.extend(files)
        except CancelledError:
            raise
        except Exception as exc:
            last_error = exc
    return downloaded_files, last_error


def inspect_web_media_batch(
    urls: Iterable[str] | str,
    progress_cb: ProgressCallback | None = None,
    options: DownloadOptions | None = None,
) -> list[dict[str, object]]:
    """Scan multiple web URLs for downloadable media candidates.

    Args:
        urls: Newline-separated string or iterable of URL strings.
        progress_cb: Progress callback for scan status updates.
        options: Download options (proxy, etc.).

    Returns:
        List of result dicts with keys: source_url, success,
        candidate_count, candidates, source, error.
    """
    items = parse_task_lines(urls) if isinstance(urls, str) else [_s._normalize_url_text(item) for item in urls]
    web_urls = [url for url in items if url and classify_source(url) == 'web']
    results: list[dict[str, object]] = []
    total = len(web_urls)
    for index, url in enumerate(web_urls, start=1):
        _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_start|index={index}|total={total}|url={url}')
        try:
            result = inspect_web_media_candidates(url, options)
            _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_done|count={result["candidate_count"]}|index={index}|total={total}|url={url}')
        except Exception as exc:
            result = {
                'source_url': url,
                'success': False,
                'candidate_count': 0,
                'candidates': [],
                'source': '',
                'error': str(exc),
            }
            _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_done|count=0|index={index}|total={total}|url={url}')
        results.append(result)
    return results


def inspect_web_media_candidates(source_url: str, options: DownloadOptions | None = None) -> dict[str, object]:
    """Inspect a single web URL for downloadable media candidates.

    Tries in order: Douyin share page, yt-dlp extraction, HTML media regex,
    and finally yt-dlp direct media support.

    Args:
        source_url: The web page URL to inspect.
        options: Download options (proxy, etc.).

    Returns:
        Dict with keys: source_url, success, candidate_count,
        candidates (list of URLs), source (detection method), error.
    """
    candidates, source = _collect_web_media_candidates(source_url, options)
    return {
        'source_url': source_url,
        'success': True,
        'candidate_count': len(candidates),
        'candidates': candidates,
        'source': source,
        'error': '',
    }


def _download_web_task(task: DownloadTask, output_root: Path, options: DownloadOptions, progress_cb: ProgressCallback | None, token: Token | None = None) -> dict[str, object]:
    output_root = _resolve_web_task_output_dir(output_root, task)
    output_root.mkdir(parents=True, exist_ok=True)
    first_error = None
    douyin_candidates = _extract_douyin_share_candidates(task.source_url, options)
    if douyin_candidates:
        downloaded_files, last_error = _download_web_candidates(
            douyin_candidates,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=_ffmpeg_path(),
            download_all=options.web_download_all_candidates,
            token=token,
        )
        if downloaded_files:
            return _make_result(task, True, downloaded_files, '')
        first_error = last_error
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(task.source_url, options)
    except Exception:
        ytdlp_candidates = []
    if len(ytdlp_candidates) > 1:
            try:
                ffmpeg_path = _ffmpeg_path()
                if options.web_download_all_candidates:
                    downloaded_files, last_error = _download_web_candidates(
                        ytdlp_candidates,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                        token=token,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
                elif options.web_candidate_indices is not None:
                    selected = _select_candidates(ytdlp_candidates, options.web_candidate_mode, options.web_candidate_indices)
                    downloaded_files, last_error = _download_web_candidates(
                        selected,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                        download_all=True,
                        token=token,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
                else:
                    downloaded_files, last_error = _download_web_candidates(
                        ytdlp_candidates,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                        token=token,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
            except CancelledError:
                raise
            except Exception as exc:
                first_error = exc
    try:
        downloaded = _download_url_with_ytdlp(
            task.source_url,
            output_root,
            options,
            progress_cb,
            title_hint=task.target_title,
            referer_url=task.source_url,
            token=token,
        )
        return _make_result(task, True, downloaded['files'], '')
    except CancelledError:
        raise
    except Exception as exc:
        first_error = exc
        if _is_cookie_access_blocked_error(exc):
            raise DownloadError(_build_cookie_retry_failure_message(task.source_url, exc)) from exc
    try:
        candidates = _extract_media_candidates(_fetch_webpage_html(task.source_url, _options_proxy_url(options)), task.source_url)
    except Exception as exc:
        raise DownloadError(f'{first_error}; 网页兜底解析失败: {exc}') from exc
    if not candidates:
        raise DownloadError(f'{first_error}; 网页中未找到可下载媒体地址')
    ffmpeg_path = _ffmpeg_path()
    if options.web_download_all_candidates:
        downloaded_files, last_error = _download_web_candidates(
            candidates,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
            token=token,
        )
        if downloaded_files:
            return _make_result(task, True, downloaded_files, '')
        raise DownloadError(f'{first_error}; 全部候选下载失败: {last_error}')
    if options.web_candidate_indices is not None:
        selected = _select_candidates(candidates, options.web_candidate_mode, options.web_candidate_indices)
        downloaded_files, last_error = _download_web_candidates(
            selected,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
            download_all=True,
            token=token,
        )
        if downloaded_files:
            return _make_result(task, True, downloaded_files, '')
        raise DownloadError(f'{first_error}; 所选候选下载失败: {last_error}')
    downloaded_files, last_error = _download_web_candidates(
        candidates,
        task,
        output_root,
        options,
        progress_cb,
        ffmpeg_path=ffmpeg_path,
        token=token,
    )
    if downloaded_files:
        return _make_result(task, True, downloaded_files, '')
    raise DownloadError(f'{first_error}; 兜底媒体地址下载失败: {last_error}')


def _pick_candidates(candidates: list[str], indices: list[int]) -> list[str]:
    """Pick candidates by 1-based indices. Raises DownloadError if any index is out of range."""
    if not indices:
        return candidates
    selected: list[str] = []
    total = len(candidates)
    for idx in indices:
        pos = idx - 1
        if pos < 0 or pos >= total:
            raise DownloadError(f'网页候选序号 {idx} 超出范围，共找到 {total} 个候选')
        selected.append(candidates[pos])
    return selected


def _select_candidates(candidates: list[str], mode: str, raw_indices: list[int] | None) -> list[str]:
    """Apply mode + indices to a candidate list. Returns the selected candidates."""
    if mode in {'before', 'after'} and raw_indices and len(raw_indices) != 1:
        raise DownloadError('before/after 只需填写一个序号，如 before3 或 after5')
    total = len(candidates)
    resolved = _resolve_candidate_indices(mode, raw_indices, total)
    if resolved is None:
        return candidates
    if mode == 'exclude':
        resolved = _inverse_indices(total, resolved)
    return _pick_candidates(candidates, resolved)


def _inverse_indices(total: int, exclude: list[int]) -> list[int]:
    """Return all 1-based indices from 1..total except those in `exclude`."""
    exclude_set = set(exclude)
    return [i for i in range(1, total + 1) if i not in exclude_set]


def _collect_web_media_candidates(source_url: str, options: DownloadOptions | None = None) -> tuple[list[str], str]:
    douyin_candidates = _extract_douyin_share_candidates(source_url, options)
    if douyin_candidates:
        return douyin_candidates, 'douyin-share'
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(source_url, options)
    except Exception:
        ytdlp_candidates = []
    if ytdlp_candidates:
        return ytdlp_candidates, 'yt-dlp'
    try:
        html_candidates = _extract_media_candidates(_fetch_webpage_html(source_url, _options_proxy_url(options)), source_url)
    except (OSError, ValueError, TimeoutError):
        html_candidates = []
    if html_candidates:
        return html_candidates, 'html'
    if _supports_ytdlp_direct_media(source_url, options):
        return [source_url], 'page'
    return [], ''


# ---------------------------------------------------------------------------
# yt-dlp engine
# ---------------------------------------------------------------------------
def _download_url_with_ytdlp(
    source_url: str,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    title_hint: str = '',
    referer_url: str = '',
    token: Token | None = None,
) -> dict[str, object]:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    http_headers = _s._build_web_headers(referer_url)
    proxy_url = _options_proxy_url(options)
    probe_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'http_headers': http_headers,
    }
    if proxy_url:
        probe_opts['proxy'] = proxy_url
    if options.web_use_browser_cookies:
        probe_opts['cookiesfrombrowser'] = ('chrome',)
    info = _run_ytdlp_with_cookie_retry(
        source_url,
        probe_opts,
        progress_cb,
        lambda opts: YoutubeDL(opts).extract_info(source_url, download=False),
    )
    title = _s.sanitize_filename_component(str(title_hint or info.get('title') or 'video'))
    media_id = _s.sanitize_filename_component(str(info.get('id') or 'video'))
    if title_hint:
        base_stem = title
    else:
        base_stem = (
            options.filename_template
            .replace('%(title)s', title)
            .replace('%(id)s', media_id)
            .replace('.%(ext)s', '')
        )
    unique_stem = _s.ensure_unique_stem(output_root, base_stem)
    ydl_opts = {
        'format': 'bv*+ba/b',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'windowsfilenames': True,
        'overwrites': bool(options.overwrite),
        'outtmpl': str(output_root / f'{unique_stem}.%(ext)s'),
        'progress_hooks': [_make_web_progress_hook(progress_cb, token)],
        'concurrent_fragment_downloads': 16,
        'continuedl': True,
        'extractor_retries': 3,
        'file_access_retries': 5,
        'fragment_retries': 20,
        'retries': 20,
        'socket_timeout': 60,
        'http_chunk_size': 10 * 1024 * 1024,
        'throttledratelimit': 500 * 1024,
        'http_headers': http_headers,
        'buffersize': 1024 * 1024,
        'http_no_compression': False,
    }
    if proxy_url:
        ydl_opts['proxy'] = proxy_url
    ffmpeg = _ffmpeg_path() or None
    if ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'] = [
            {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
            {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
        ]
    aria2c = _s._resolve_aria2c_path()
    if aria2c:
        ydl_opts['external_downloader'] = aria2c
        ydl_opts['external_downloader_args'] = [
            '-x', '16',
            '-s', '16',
            '-k', '2M',
            '--continue=true',
            '--max-tries=10',
            '--retry-wait=3',
            '--timeout=60',
            '--connect-timeout=30',
            '--lowest-speed-limit=100K',
            '--file-allocation=falloc',
            '--summary-interval=1',
            '--console-log-level=notice',
            '--enable-http-pipelining=true',
            '--async-dns=true',
            '--max-connection-per-server=16',
            '--min-split-size=1M',
            '--disk-cache=64M',
            '--auto-file-renaming=false',
            '--allow-overwrite=true',
        ]
        if proxy_url:
            ydl_opts['external_downloader_args'].extend([f'--all-proxy={proxy_url}'])
        if referer_url:
            safe_referer = referer_url.replace('"', '%22').replace('\\', '%5C').replace('\n', '').replace('\r', '')
            ydl_opts['external_downloader_args'].extend([
                f'--user-agent={_s.WEB_USER_AGENT}',
                f'--header=Referer: {safe_referer}',
            ])
        _emit(progress_cb, f'网页加速: 使用 aria2c -> {aria2c}')
    if options.web_use_browser_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
    max_reconnects = 3
    reconnect_count = 0
    capture_aria2_progress = bool(aria2c and progress_cb and options.max_concurrent_downloads <= 1)
    while True:
        try:
            # aria2 console capture redirects process-level stdout/stderr; in
            # concurrent mode that would serialize all active downloads.
            capture_context = (
                _capture_aria2_console_progress(progress_cb, unique_stem)
                if capture_aria2_progress
                else nullcontext()
            )
            with capture_context:
                def _download_once(run_opts: dict[str, object]):
                    with YoutubeDL(run_opts) as ydl:
                        return ydl.extract_info(source_url, download=True)

                _run_ytdlp_with_cookie_retry(source_url, ydl_opts, progress_cb, _download_once)
        except _PausedDownload:
            _wait_if_paused(token, progress_cb)
            continue
        except CancelledError:
            if token and token.reconnect.is_set():
                token.reconnect.clear()
                reconnect_count += 1
                if reconnect_count > max_reconnects:
                    raise DownloadError('重连次数已达上限')
                _emit(progress_cb, f'重连中... (第{reconnect_count}次)')
                continue
            raise
        except Exception:
            created = sorted(_s._find_completed_downloads(output_root, unique_stem))
            if created:
                _maybe_fill_missing_embedded_thumbnails(created, source_url, progress_cb, ffmpeg or '', proxy_url)
                _emit(progress_cb, f'网页 OK -> {created[0].name}')
                return {
                    'success': True,
                    'files': created,
                }
            raise
        # extract_info returned normally — check if reconnect flag was set
        # (yt-dlp may catch CancelledError internally and return normally)
        if token and token.reconnect.is_set():
            token.reconnect.clear()
            reconnect_count += 1
            if reconnect_count > max_reconnects:
                raise DownloadError('重连次数已达上限')
            _emit(progress_cb, f'重连中... (第{reconnect_count}次)')
            continue
        break
    created = sorted(_s._find_completed_downloads(output_root, unique_stem))
    if not created:
        raise DownloadError('网页视频下载完成，但未找到输出文件')
    _maybe_fill_missing_embedded_thumbnails(created, source_url, progress_cb, ffmpeg or '', proxy_url)
    _emit(progress_cb, f'网页 OK -> {created[0].name}')
    return {
        'success': True,
        'files': created,
    }


def _fetch_webpage_html(url: str, proxy_url: str = '') -> str:
    request = Request(
        url,
        headers={
            'User-Agent': _s.WEB_USER_AGENT,
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': url,
        },
    )
    with _urlopen_with_proxy(request, 20, proxy_url) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return response.read().decode(charset, errors='ignore')


def _extract_media_candidates(html_text: str, page_url: str) -> list[str]:
    normalized = unescape(str(html_text or ''))
    normalized = normalized.replace('\\/', '/').replace('\\u002F', '/').replace('\\u002f', '/')
    unique: dict[str, None] = {}
    for pattern in (MEDIA_URL_RE, RELATIVE_MEDIA_RE):
        for match in pattern.finditer(normalized):
            raw_url = match.group('url')
            if not raw_url:
                continue
            if raw_url.startswith('//'):
                candidate = f'{urlparse(page_url).scheme}:{raw_url}'
            else:
                candidate = urljoin(page_url, raw_url)
            unique.setdefault(candidate, None)
    return list(unique.keys())


def _extract_ytdlp_entry_candidates(page_url: str, options: DownloadOptions | None = None) -> list[str]:
    _require_web_backend()
    from yt_dlp import YoutubeDL
    ydl_opts: dict[str, object] = {'quiet': True, 'skip_download': True}
    proxy_url = _options_proxy_url(options)
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    info = _run_ytdlp_with_cookie_retry(
        page_url,
        ydl_opts,
        None,
        lambda opts: YoutubeDL(opts).extract_info(page_url, download=False),
    )
    entries = info.get('entries')
    if not isinstance(entries, Iterable):
        return []
    unique: dict[str, None] = {}
    _collect_ytdlp_entry_candidates(entries, page_url, unique)
    return list(unique.keys())


def _collect_ytdlp_entry_candidates(entries: object, page_url: str, unique: dict[str, None]) -> None:
    if not isinstance(entries, Iterable) or isinstance(entries, (str, bytes, dict)):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        nested_entries = entry.get('entries')
        if nested_entries is not None:
            _collect_ytdlp_entry_candidates(nested_entries, page_url, unique)
        for key in ('url', 'webpage_url', 'original_url'):
            candidate = _normalize_web_candidate_url(entry.get(key), page_url)
            if candidate:
                unique.setdefault(candidate, None)
                break


def _collect_ytdlp_candidate_entries(entries: object, page_url: str, collected: list[dict[str, object]]) -> None:
    if not isinstance(entries, Iterable) or isinstance(entries, (str, bytes, dict)):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        nested_entries = entry.get('entries')
        if nested_entries is not None:
            _collect_ytdlp_candidate_entries(nested_entries, page_url, collected)
        for key in ('url', 'webpage_url', 'original_url'):
            candidate = _normalize_web_candidate_url(entry.get(key), page_url)
            if candidate:
                collected.append(entry)
                break


def _normalize_thumbnail_url(raw_url: object, page_url: str) -> str:
    if not isinstance(raw_url, str):
        return ''
    cleaned = raw_url.strip()
    if not cleaned:
        return ''
    if cleaned.startswith('//'):
        return f'{urlparse(page_url).scheme}:{cleaned}'
    return urljoin(page_url, cleaned)


def _collect_thumbnail_urls_from_info(info: object, page_url: str, unique: dict[str, None]) -> None:
    if not isinstance(info, dict):
        return
    thumbnail = _normalize_thumbnail_url(info.get('thumbnail'), page_url)
    if thumbnail:
        unique.setdefault(thumbnail, None)
    thumbnails = info.get('thumbnails')
    if isinstance(thumbnails, Iterable) and not isinstance(thumbnails, (str, bytes, dict)):
        for item in thumbnails:
            if not isinstance(item, dict):
                continue
            thumb_url = _normalize_thumbnail_url(item.get('url'), page_url)
            if thumb_url:
                unique.setdefault(thumb_url, None)


def _select_ytdlp_thumbnail_entry(
    info: object,
    page_url: str,
    resolved_url: str,
    candidate_index: int | None,
) -> object:
    if not isinstance(info, dict):
        return info
    entries = info.get('entries')
    if not isinstance(entries, Iterable) or isinstance(entries, (str, bytes, dict)):
        return info
    collected: list[dict[str, object]] = []
    _collect_ytdlp_candidate_entries(entries, page_url, collected)
    normalized_resolved = _normalize_web_candidate_url(resolved_url, page_url)
    if normalized_resolved:
        for entry in collected:
            for key in ('url', 'webpage_url', 'original_url'):
                candidate = _normalize_web_candidate_url(entry.get(key), page_url)
                if candidate == normalized_resolved:
                    return entry
    if candidate_index is not None and 1 <= candidate_index <= len(collected):
        return collected[candidate_index - 1]
    if len(collected) == 1:
        return collected[0]
    return info


def _extract_thumbnail_urls(
    source_url: str,
    resolved_url: str,
    candidate_index: int | None,
    proxy_url: str = '',
) -> list[str]:
    _require_web_backend()
    from yt_dlp import YoutubeDL
    ydl_opts: dict[str, object] = {'quiet': True, 'skip_download': True, 'noplaylist': True}
    proxy = normalize_proxy_url(proxy_url)
    if proxy:
        ydl_opts['proxy'] = proxy

    info = _run_ytdlp_with_cookie_retry(
        source_url,
        ydl_opts,
        None,
        lambda opts: YoutubeDL(opts).extract_info(source_url, download=False),
    )
    unique: dict[str, None] = {}
    selected_info = _select_ytdlp_thumbnail_entry(info, source_url, resolved_url, candidate_index)
    _collect_thumbnail_urls_from_info(selected_info, source_url, unique)
    if not unique and selected_info is not info:
        _collect_thumbnail_urls_from_info(info, source_url, unique)
    return list(unique.keys())


def _guess_thumbnail_suffix(url: str, content_type: str = '') -> str:
    lowered_type = str(content_type or '').lower()
    type_map = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/webp': '.webp',
    }
    for prefix, suffix in type_map.items():
        if lowered_type.startswith(prefix):
            return suffix
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {'.jpg', '.jpeg', '.png', '.webp'} else '.jpg'


def _download_thumbnail_file(url: str, thumb_dir: Path, stem: str, referer_url: str, proxy_url: str = '') -> Path:
    request = Request(
        url,
        headers={
            **_s._build_web_headers(referer_url),
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        },
    )
    with _urlopen_with_proxy(request, 20, proxy_url) as response:
        suffix = _guess_thumbnail_suffix(url, response.headers.get('Content-Type', ''))
        thumb_path = thumb_dir / f'{stem}{suffix}'
        thumb_path.write_bytes(response.read())
        return thumb_path


def _extract_video_frame_thumbnail(video_path: Path, thumb_dir: Path, stem: str, ffmpeg: str) -> Path:
    thumb_path = thumb_dir / f'{stem}.jpg'
    subprocess.run(
        [
            ffmpeg,
            '-y',
            '-i', str(video_path),
            '-vf', 'thumbnail',
            '-frames:v', '1',
            str(thumb_path),
        ],
        capture_output=True,
        check=True,
        timeout=300,
    )
    return thumb_path


def _video_has_embedded_thumbnail(video_path: Path, ffmpeg_path: str) -> bool:
    ffprobe = Path(ffmpeg_path).with_name('ffprobe') if ffmpeg_path else Path('ffprobe')
    try:
        result = subprocess.run(
            [
                str(ffprobe),
                '-v', 'error',
                '-select_streams', 'v',
                '-show_entries', 'stream=disposition',
                '-of', 'json',
                str(video_path),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except Exception:
        return False
    try:
        payload = json.loads(result.stdout.decode(errors='ignore') or '{}')
    except Exception:
        return False
    streams = payload.get('streams')
    if not isinstance(streams, list):
        return False
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        disposition = stream.get('disposition')
        if isinstance(disposition, dict) and disposition.get('attached_pic') == 1:
            return True
    return False


def _maybe_fill_missing_embedded_thumbnails(
    files: list[Path],
    source_url: str,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str,
    proxy_url: str = '',
) -> None:
    video_exts = {'.mp4', '.mkv', '.webm', '.mov', '.m4v'}
    if not ffmpeg_path:
        return
    for video_path in files:
        if video_path.suffix.lower() not in video_exts or not video_path.is_file():
            continue
        if _video_has_embedded_thumbnail(video_path, ffmpeg_path):
            continue
        _emit(progress_cb, f'封面缺失，自动补封面: {video_path.name}')
        result = embed_thumbnail(video_path, source_url, progress_cb=progress_cb, proxy_url=proxy_url)
        if result.get('success'):
            _emit(progress_cb, f'封面补全成功: {video_path.name}')
        else:
            _emit(progress_cb, f'封面补全失败，保留原视频: {video_path.name} -> {result.get("error", "")}')


def _supports_ytdlp_direct_media(source_url: str, options: DownloadOptions | None = None) -> bool:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    ydl_opts: dict[str, object] = {'quiet': True, 'skip_download': True, 'noplaylist': True}
    proxy_url = _options_proxy_url(options)
    if proxy_url:
        ydl_opts['proxy'] = proxy_url
    info = _run_ytdlp_with_cookie_retry(
        source_url,
        ydl_opts,
        None,
        lambda opts: YoutubeDL(opts).extract_info(source_url, download=False),
    )
    if not isinstance(info, dict):
        return False
    return bool(info.get('url') or info.get('formats') or info.get('id') or info.get('title'))


def _normalize_web_candidate_url(raw_url: object, page_url: str) -> str:
    text = str(raw_url or '').strip()
    if not text:
        return ''
    if text.startswith('//'):
        return f'{urlparse(page_url).scheme}:{text}'
    if text.startswith('/'):
        return urljoin(page_url, text)
    parsed = urlparse(text)
    if parsed.scheme in {'http', 'https'} and parsed.netloc:
        return text
    return ''


# ---------------------------------------------------------------------------
# FFmpeg m3u8
# ---------------------------------------------------------------------------
def _download_m3u8_with_ffmpeg(
    media_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
    referer_url: str = '',
    token: Token | None = None,
) -> dict[str, object]:
    ffmpeg = ffmpeg_path or _ffmpeg_path()
    if not ffmpeg:
        raise DownloadError('未检测到 ffmpeg，无法直接下载 m3u8')
    proxy_url = _options_proxy_url(options)
    base_stem = _s.ensure_unique_stem(output_root, _s.sanitize_filename_component(task.target_title or 'video'))
    output_path = _s.ensure_unique_path(output_root / f'{base_stem}.mp4')
    total_duration = _probe_stream_duration(media_url, ffmpeg, proxy_url=proxy_url)
    max_reconnects = 3
    reconnect_count = 0
    for reconnect_attempt in range(max_reconnects + 1):
        overwrite_flag = '-y' if options.overwrite or reconnect_attempt > 0 else '-n'
        command = [
            ffmpeg,
            overwrite_flag,
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_on_network_error', '1',
            '-reconnect_on_http_error', '429,500,502,503,504',
            '-reconnect_delay_max', '15',
            '-rw_timeout', '30000000',
            '-multiple_requests', '1',
            '-user_agent', _s.WEB_USER_AGENT,
            '-headers', _s._build_ffmpeg_header_text(referer_url),
            '-i', media_url,
            '-c', 'copy',
            '-progress', 'pipe:1',
            '-nostats',
            '-loglevel', 'error',
            str(output_path),
        ]
        if proxy_url:
            command[2:2] = ['-http_proxy', proxy_url]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.stdout is None:
            raise RuntimeError('ffmpeg Popen 没有 stdout')
        started = monotonic()
        last_emit = 0.0
        should_reconnect = False
        for line in proc.stdout:
            if token and token.cancel.is_set():
                _terminate_ffmpeg(proc)
                raise CancelledError('ffmpeg 下载已取消')
            try:
                _wait_if_paused(token, progress_cb)
            except CancelledError:
                _terminate_ffmpeg(proc)
                raise
            if token and token.reconnect.is_set():
                token.reconnect.clear()
                _terminate_ffmpeg(proc)
                should_reconnect = True
                break
            line = line.strip()
            if not line.startswith('out_time='):
                continue
            time_val = line.split('=', 1)[1].strip()
            if time_val == '00:00:00.000000':
                continue
            now = monotonic()
            if now - last_emit < 0.5:
                continue
            last_emit = now
            seconds = _parse_ffmpeg_time(time_val)
            elapsed = max(now - started, 1e-6)
            speed_text = _format_byte_rate(_estimate_download_rate(elapsed, seconds)) if seconds > 0 else ''
            percent_text = ''
            eta_text = ''
            if total_duration and total_duration > 0 and seconds > 0:
                percent_text = _format_progress_percent(min(seconds / total_duration * 100, 99.9))
                remaining = max(0, total_duration - seconds)
                if seconds > 0:
                    eta_sec = int(remaining * elapsed / seconds)
                    eta_text = _format_eta_seconds(eta_sec)
            _emit(progress_cb, _build_download_log_message(output_path.name, speed_text, percent_text, eta_text))
            _emit_web_transfer_progress(progress_cb, output_path.name, percent_text.replace('%', ''), speed_text, eta_text)
        if not should_reconnect:
            proc.wait()
            if proc.returncode != 0:
                stderr = (proc.stderr.read() if proc.stderr else '').strip()
                raise DownloadError(stderr or 'ffmpeg 下载失败')
            break
        reconnect_count += 1
        if reconnect_count > max_reconnects:
            raise DownloadError('重连次数已达上限')
        _emit(progress_cb, f'重新下载中... (第{reconnect_count}次)')
    _emit(progress_cb, f'网页 OK -> {output_path.name}')
    return {
        'success': True,
        'files': [output_path],
    }


def _terminate_ffmpeg(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def _probe_stream_duration(url: str, ffmpeg_path: str = '', proxy_url: str = '') -> float | None:
    """Get stream duration via ffprobe. Returns seconds or None."""
    ffprobe = Path(ffmpeg_path).with_name('ffprobe') if ffmpeg_path else 'ffprobe'
    if ffmpeg_path:
        ffprobe = str(ffprobe)
    try:
        command = [ffprobe, '-v', 'quiet']
        proxy = normalize_proxy_url(proxy_url)
        if proxy:
            command.extend(['-http_proxy', proxy])
        command.extend(['-show_entries', 'format=duration', '-of', 'csv=p=0', url])
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Progress hook
# ---------------------------------------------------------------------------
def _make_web_progress_hook(progress_cb: ProgressCallback | None, token: Token | None = None):
    def hook(status: dict[str, Any]) -> None:
        if token and token.cancel.is_set():
            raise CancelledError('yt-dlp 下载已取消')
        if token and token.reconnect.is_set():
            raise CancelledError('手动重连')
        # Use non-blocking pause check to avoid blocking yt-dlp's download thread
        if _check_paused_non_blocking(token):
            raise _PausedDownload('下载已暂停')
        state = str(status.get('status') or '')
        if state == 'downloading':
            filename = Path(str(status.get('filename') or '')).name
            percent = _resolve_web_percent_text(status)
            speed = _resolve_web_speed_text(status)
            eta = _normalize_progress_text(status.get('_eta_str', ''))
            text = _build_download_log_message(filename, speed, percent, eta)
            normalized_percent = percent.replace('%', '').strip()
            try:
                _emit(progress_cb, f'__HYL_PROGRESS__|web_percent|percent={float(normalized_percent)}')
            except ValueError:
                pass
            _emit_web_transfer_progress(progress_cb, filename, normalized_percent, speed, eta)
            _emit(progress_cb, text)
        elif state == 'finished':
            filename = Path(str(status.get('filename') or '')).name
            _emit(progress_cb, f'网页处理完成 {filename}')
    return hook


# ---------------------------------------------------------------------------
# Embed thumbnail
# ---------------------------------------------------------------------------
def embed_thumbnail(
    video_path: str | Path,
    source_url: str,
    progress_cb: ProgressCallback | None = None,
    candidate_index: int | None = None,
    thumbnail_mode: str = 'web_then_frame',
    proxy_url: str = '',
) -> dict[str, object]:
    """Download thumbnail via yt-dlp and embed it into an existing mp4.

    If *source_url* is a page with multiple video candidates (same as the
    download pipeline), pass ``candidate_index`` (1-based) to pick one.

    Args:
        video_path: Path to the video file to embed thumbnail into.
        source_url: Web URL to fetch the thumbnail from.
        progress_cb: Progress callback for status messages.
        candidate_index: 1-based index when source_url has multiple candidates.
        thumbnail_mode: 'web_then_frame', 'web', or 'frame'.
        proxy_url: HTTP/SOCKS5 proxy for thumbnail download.

    Returns:
        Dict with 'success' (bool), 'files' (list of paths), and optionally
        'error' (str), 'candidate_count' (int), 'candidates' (list).
    """
    video_path = Path(video_path)
    direct_frame = thumbnail_mode == 'frame'
    if not video_path.is_file():
        return {'success': False, 'error': f'文件不存在: {video_path}'}
    if not direct_frame and not source_url.strip():
        direct_frame = True  # 无源链接，直接从视频抽帧

    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return {'success': False, 'error': '未检测到 ffmpeg'}

    import tempfile
    thumb_tmp = tempfile.TemporaryDirectory(dir=video_path.parent, prefix='.thumb_tmp_')
    thumb_dir = Path(thumb_tmp.name)
    stem = video_path.stem
    try:
        if direct_frame:
            _emit(progress_cb, f'直接抽取视频帧作为封面: {video_path.name}')
            try:
                thumb_file = _extract_video_frame_thumbnail(video_path, thumb_dir, stem, ffmpeg)
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr.decode(errors='replace') if exc.stderr else ''
                return {'success': False, 'error': f'视频帧提取失败: {stderr[:200]}'}
        else:
            _require_web_backend()
            from yt_dlp import YoutubeDL

            thumb_file = None
            image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
            resolved_url = source_url

            # Step 0: resolve page URL → actual video candidate URL
            _emit(progress_cb, f'正在解析链接: {source_url}')
            try:
                candidates, _source = _collect_web_media_candidates(source_url, DownloadOptions(proxy_url=proxy_url))
                if candidates:
                    if candidate_index is not None and 1 <= candidate_index <= len(candidates):
                        resolved_url = candidates[candidate_index - 1]
                        _emit(progress_cb, f'候选 {candidate_index}/{len(candidates)}: {resolved_url}')
                    elif len(candidates) == 1:
                        resolved_url = candidates[0]
                    else:
                        # Multiple candidates but no index specified – inform user
                        labels = [f'  [{i+1}] {u}' for i, u in enumerate(candidates[:10])]
                        return {
                            'success': False,
                            'error': f'该页面有 {len(candidates)} 个视频，请指定序号\n' + '\n'.join(labels),
                            'candidate_count': len(candidates),
                            'candidates': candidates,
                        }
            except Exception:
                pass  # Fall through with original source_url

            _emit(progress_cb, f'正在抓取封面: {source_url}')
            try:
                for thumb_url in _extract_thumbnail_urls(source_url, resolved_url, candidate_index, proxy_url):
                    try:
                        thumb_file = _download_thumbnail_file(thumb_url, thumb_dir, stem, source_url, proxy_url)
                        break
                    except Exception:
                        continue
            except Exception:
                thumb_file = None
            if not thumb_file:
                _emit(progress_cb, f'页面封面缺失，尝试媒体地址: {resolved_url}')
                ydl_opts = {
                    'skip_download': True,
                    'writethumbnail': True,
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': str(thumb_dir / f'{stem}.%(ext)s'),
                    'noplaylist': True,
                    'http_headers': _s._build_web_headers(source_url),
                }
                proxy = normalize_proxy_url(proxy_url)
                if proxy:
                    ydl_opts['proxy'] = proxy
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(resolved_url, download=True)
                for f in thumb_dir.iterdir():
                    if f.suffix.lower() in image_exts:
                        thumb_file = f
                        break
            if not thumb_file:
                _emit(progress_cb, f'外部封面缺失，改用视频首帧: {video_path.name}')
                try:
                    thumb_file = _extract_video_frame_thumbnail(video_path, thumb_dir, stem, ffmpeg)
                except subprocess.CalledProcessError as exc:
                    stderr = exc.stderr.decode(errors='replace') if exc.stderr else ''
                    actual = [f.name for f in thumb_dir.iterdir()]
                    return {'success': False, 'error': f'未找到封面文件，目录内容: {actual}；首帧提取失败: {stderr[:200]}'}
        # Convert to jpg if needed
        if thumb_file.suffix.lower() != '.jpg':
            jpg_thumb = thumb_dir / f'{stem}.jpg'
            subprocess.run(
                [ffmpeg, '-y', '-i', str(thumb_file), str(jpg_thumb)],
                capture_output=True, check=True,
                timeout=300,
            )
            thumb_file.unlink(missing_ok=True)
            thumb_file = jpg_thumb

        _emit(progress_cb, f'封面已下载，正在嵌入: {video_path.name}')

        # Step 2: embed thumbnail into mp4
        tmp_out = video_path.parent / f'{stem}_cover_tmp.mp4'
        subprocess.run(
            [
                ffmpeg, '-y',
                '-i', str(video_path),
                '-i', str(thumb_file),
                '-map', '0', '-map', '1',
                '-c', 'copy',
                '-disposition:v:1', 'attached_pic',
                str(tmp_out),
            ],
            capture_output=True, check=True,
            timeout=300,
        )
        # Replace original (atomic on same filesystem)
        os.replace(str(tmp_out), str(video_path))

        _emit(progress_cb, f'封面嵌入成功: {video_path.name}')
        return {'success': True, 'files': [str(video_path)]}

    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors='replace') if exc.stderr else ''
        return {'success': False, 'error': f'ffmpeg 错误: {stderr[:200]}'}
    except Exception as exc:
        return {'success': False, 'error': str(exc)}
    finally:
        thumb_tmp.cleanup()
