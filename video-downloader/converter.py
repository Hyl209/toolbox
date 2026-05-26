from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time, timezone
from threading import Event, Lock
import threading as _threading
from html import unescape
import importlib.util
import re
import shutil
import ssl
import subprocess
from dataclasses import dataclass, replace
from collections.abc import Iterable
from pathlib import Path
from time import monotonic
from typing import Callable, Literal
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SourceKind = Literal['telegram_message', 'telegram_chat', 'web']
ProgressCallback = Callable[[str], None]

TELEGRAM_HOSTS = {'t.me', 'telegram.me', 'telegram.dog', 'www.t.me', 'www.telegram.me'}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WHITESPACE_RE = re.compile(r'\s+')
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
MEDIA_URL_RE = re.compile(r"""(?P<url>(?:https?:)?//[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
RELATIVE_MEDIA_RE = re.compile(r"""(?P<url>/[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
SESSION_FILE_NAME = 'telegram.session'
DEFAULT_FILENAME_TEMPLATE = '%(title)s [%(id)s].%(ext)s'
_stem_lock = Lock()


@dataclass(frozen=True)
class TelegramConfig:
    api_id: str
    api_hash: str
    phone: str
    session_file: str | Path


@dataclass(frozen=True)
class DownloadTask:
    source_url: str
    source_kind: SourceKind
    target_title: str = ''
    output_subdir: str = ''


@dataclass(frozen=True)
class DownloadOptions:
    web_use_browser_cookies: bool = False
    overwrite: bool = False
    filename_template: str = DEFAULT_FILENAME_TEMPLATE
    web_candidate_indices: list[int] | None = None
    web_download_all_candidates: bool = False
    max_concurrent_downloads: int = 1
    telegram_recent_limit: int | None = 500
    telegram_download_all_messages: bool = False
    telegram_date_from: date | None = None
    telegram_date_to: date | None = None
    telegram_include_videos: bool = True
    telegram_include_photos: bool = False


@dataclass(frozen=True)
class TelegramUrlParts:
    entity_ref: str | int
    message_id: int | None
    invite_hash: str = ''


class DownloadError(RuntimeError):
    pass


class CancelledError(RuntimeError):
    pass


class Token:
    __slots__ = ('cancel', 'pause')

    def __init__(self) -> None:
        self.cancel = Event()
        self.pause = Event()


def _check_cancel(token: Token) -> None:
    if token.cancel.is_set():
        raise CancelledError('下载已取消')


_state = _threading.local()


def _current_token() -> Token | None:
    return getattr(_state, 'token', None)


def _set_current_token(token: Token | None) -> None:
    _state.token = token


def _require_token() -> Token:
    token = _current_token()
    if token is None:
        return Token()
    return token


def parse_task_lines(text: str) -> list[str]:
    unique: dict[str, None] = {}
    for raw in (text or '').splitlines():
        normalized = _normalize_url_text(raw)
        if normalized:
            unique.setdefault(normalized, None)
    return list(unique.keys())


def classify_source(url: str) -> SourceKind:
    normalized = _normalize_url_text(url)
    if not normalized:
        raise ValueError('链接不能为空')
    parsed = urlparse(normalized)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError(f'无效链接: {url}')
    host = parsed.netloc.lower()
    if host not in TELEGRAM_HOSTS:
        return 'web'
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return 'telegram_chat'
    if parts[0] == 'joinchat' or parts[0].startswith('+'):
        return 'telegram_chat'
    if parts[0] == 'c':
        if len(parts) >= 3 and parts[2].isdigit():
            return 'telegram_message'
        return 'telegram_chat'
    if len(parts) >= 2 and parts[1].isdigit():
        return 'telegram_message'
    return 'telegram_chat'


def build_download_tasks(urls: Iterable[str]) -> list[DownloadTask]:
    tasks: list[DownloadTask] = []
    for raw in urls:
        normalized = _normalize_url_text(raw)
        if not normalized:
            continue
        tasks.append(
            DownloadTask(
                source_url=normalized,
                source_kind=classify_source(normalized),
                target_title=guess_task_title(normalized),
            )
        )
    return tasks


def guess_task_title(url: str) -> str:
    parsed = urlparse(_normalize_url_text(url))
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return sanitize_filename_component(parsed.netloc or 'video')
    return sanitize_filename_component(parts[-1] or parts[0] or parsed.netloc or 'video')


def probe_download_backends() -> dict[str, dict[str, object]]:
    ffmpeg = shutil.which('ffmpeg')
    return {
        'telethon': _build_backend_status('telethon', 'Telegram 登录/下载'),
        'yt_dlp': _build_backend_status('yt_dlp', '网页视频解析'),
        'ffmpeg': {
            'available': bool(ffmpeg),
            'label': '媒体合并/转封装',
            'message': '已检测到 ffmpeg' if ffmpeg else '未检测到 ffmpeg，部分站点可能无法合并音视频',
            'path': ffmpeg or '',
        },
    }


def validate_download_request(
    task_lines: Iterable[str] | Iterable[DownloadTask] | str,
    output_dir: str,
    telegram_config: TelegramConfig | None = None,
    recent_limit: str | int | None = None,
    telegram_download_all_messages: bool = False,
    date_from: str | date | None = None,
    date_to: str | date | None = None,
    telegram_include_videos: bool = True,
    telegram_include_photos: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        tasks = _coerce_tasks(task_lines)
    except ValueError as exc:
        return [str(exc)]
    if not tasks:
        errors.append('请先输入下载链接')
    cleaned_output = (output_dir or '').strip()
    if not cleaned_output:
        errors.append('请选择输出目录')
    else:
        output_path = Path(cleaned_output)
        if output_path.exists() and not output_path.is_dir():
            errors.append('输出路径不是文件夹')
    try:
        normalize_recent_limit(recent_limit, default=500)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        normalize_date_range(date_from, date_to)
    except ValueError as exc:
        errors.append(str(exc))
    needs_telegram = any(task.source_kind.startswith('telegram') for task in tasks)
    if needs_telegram:
        if not telegram_include_videos and not telegram_include_photos:
            errors.append('Telegram 任务至少要勾选一种下载类型')
        if telegram_config is None:
            errors.append('Telegram 任务需要填写 API ID、API Hash 和手机号')
        else:
            if not str(telegram_config.api_id).strip():
                errors.append('请输入 Telegram API ID')
            if not str(telegram_config.api_hash).strip():
                errors.append('请输入 Telegram API Hash')
            if not str(telegram_config.phone).strip():
                errors.append('请输入 Telegram 手机号')
            if not str(telegram_config.session_file).strip():
                errors.append('Telegram 会话文件路径不能为空')
        if not telegram_download_all_messages:
            try:
                limit = normalize_recent_limit(recent_limit, default=500)
            except ValueError:
                limit = None
            if limit == 0:
                errors.append('未勾选“全部消息”时，最近消息条数不能为 0')
    return errors


def normalize_recent_limit(value: str | int | None, default: int | None = 500) -> int | None:
    if value is None:
        return default
    if isinstance(value, int):
        if value < 0:
            raise ValueError('最近消息条数不能小于 0')
        return value
    cleaned = str(value).strip()
    if not cleaned:
        return default
    try:
        limit = int(cleaned)
    except ValueError as exc:
        raise ValueError('最近消息条数必须是整数') from exc
    if limit < 0:
        raise ValueError('最近消息条数不能小于 0')
    return limit


def normalize_positive_indices(value: str | int | None, field_label: str) -> list[int] | None:
    """Parse '3' or '3,4,6' into a list of positive integers. Returns None for empty input."""
    if value is None:
        return None
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f'{field_label}必须大于 0')
        return [value]
    cleaned = str(value).strip()
    if not cleaned:
        return None
    parts = [p.strip() for p in cleaned.split(',') if p.strip()]
    if not parts:
        return None
    indices: list[int] = []
    for part in parts:
        try:
            parsed = int(part)
        except ValueError as exc:
            raise ValueError(f'{field_label} "{part}" 不是有效的正整数') from exc
        if parsed <= 0:
            raise ValueError(f'{field_label} {parsed} 必须大于 0')
        if parsed in indices:
            raise ValueError(f'{field_label} {parsed} 重复')
        indices.append(parsed)
    indices.sort()
    return indices


def parse_iso_date(value: str | date | None, field_label: str) -> date | None:
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    cleaned = str(value).strip()
    if not cleaned:
        return None
    try:
        return datetime.strptime(cleaned, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError(f'{field_label}必须是 YYYY-MM-DD 格式') from exc


def normalize_date_range(date_from: str | date | None, date_to: str | date | None) -> tuple[date | None, date | None]:
    parsed_from = parse_iso_date(date_from, '开始日期')
    parsed_to = parse_iso_date(date_to, '结束日期')
    if parsed_from and parsed_to and parsed_from > parsed_to:
        raise ValueError('开始日期不能晚于结束日期')
    return parsed_from, parsed_to


def sanitize_filename_component(text: str, fallback: str = 'video') -> str:
    cleaned = INVALID_FILENAME_CHARS.sub('_', str(text or '').strip())
    cleaned = WHITESPACE_RE.sub(' ', cleaned).strip(' .')
    return cleaned or fallback


def ensure_unique_path(path: str | Path) -> Path:
    candidate = Path(path)
    parent = candidate.parent
    stem = candidate.stem
    suffix = ''.join(candidate.suffixes)
    index = 1
    while candidate.exists():
        candidate = parent / f'{stem} ({index}){suffix}'
        index += 1
    return candidate


def ensure_unique_stem(directory: str | Path, stem: str) -> str:
    folder = Path(directory)
    safe_stem = sanitize_filename_component(stem)
    with _stem_lock:
        candidate = safe_stem
        index = 1
        while any(folder.glob(f'{candidate}.*')):
            candidate = f'{safe_stem} ({index})'
            index += 1
        return candidate


def _run_web_task(task, output_root, options, progress_cb, token):
    _set_current_token(token)
    return _download_web_task(task, output_root, options, progress_cb)


def _download_web_entries(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
) -> dict[int, dict[str, object]]:
    """Download web entries. Uses sequential loop for concurrency=1, thread pool otherwise."""
    if not web_entries:
        return {}
    max_workers = max(1, min(options.max_concurrent_downloads, len(web_entries)))
    if max_workers <= 1:
        return _download_web_sequential(web_entries, output_root, options, progress_cb, total_tasks, completed_count)
    return _download_web_concurrent(web_entries, output_root, options, progress_cb, total_tasks, completed_count, max_workers)


def _download_web_sequential(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    for index, task in web_entries:
        _check_cancel(_require_token())
        token = _current_token()
        if token and token.pause.is_set():
            _emit(progress_cb, '下载已暂停')
            token.pause.wait()
            _emit(progress_cb, '下载已恢复')
        _emit_task_start(progress_cb, index, total_tasks, task)
        _set_current_token(_require_token())
        try:
            results[index] = _download_web_task(task, output_root, options, progress_cb)
        except CancelledError:
            results[index] = _make_result(task, False, [], '下载已取消')
            completed_count += 1
            _emit_task_done(progress_cb, completed_count, total_tasks)
            raise
        except Exception as exc:
            results[index] = _make_result(task, False, [], str(exc))
        completed_count += 1
        _emit_task_done(progress_cb, completed_count, total_tasks)
    return results


def _download_web_concurrent(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    completed_count: int,
    max_workers: int,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    task_by_index = {index: task for index, task in web_entries}
    for index, task in web_entries:
        _emit_task_start(progress_cb, index, total_tasks, task)
    token = _current_token()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_run_web_task, task, output_root, options, progress_cb, token): index
            for index, task in web_entries
        }
        for future in as_completed(future_map):
            index = future_map[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = _make_result(task_by_index[index], False, [], str(exc))
            completed_count += 1
            _emit_task_done(progress_cb, completed_count, total_tasks)
    return results


def _download_web_auto(
    web_entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
    initial_completed: int,
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
        _emit_task_start(progress_cb, index, total_tasks, task)
        _set_current_token(_require_token())
        try:
            results[index] = _download_web_task(task, output_root, options, tracker.emit)
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
        remaining, output_root, concurrent_opts, progress_cb, total_tasks, completed,
    ))
    return results


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


def _speed_to_concurrency(bytes_per_sec: float) -> int:
    """Map download speed to recommended concurrency (1-5)."""
    if bytes_per_sec <= 0:
        return 2
    mbps = bytes_per_sec / (1024 * 1024)
    if mbps >= 5:
        return 5
    if mbps >= 2:
        return 3
    if mbps >= 0.5:
        return 2
    return 1


def download_batch(
    tasks: Iterable[str] | Iterable[DownloadTask],
    output_dir: str | Path,
    telegram_config: TelegramConfig | None,
    options: DownloadOptions | None = None,
    progress_cb: ProgressCallback | None = None,
    *,
    token: Token | None = None,
) -> list[dict[str, object]]:
    task_list = _coerce_tasks(tasks)
    config = telegram_config
    download_options = options or DownloadOptions()
    if token is not None:
        _set_current_token(token)
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
            telegram_results = asyncio.run(
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
            results.update(_download_web_auto(web_entries, output_root, download_options, progress_cb, total_tasks, len(results)))
        else:
            results.update(_download_web_entries(web_entries, output_root, download_options, progress_cb, total_tasks, len(results)))
    except CancelledError:
        for index in range(len(task_list)):
            if index not in results:
                results[index] = _make_result(task_list[index], False, [], '下载已取消')
    return [results[index] for index in range(len(task_list))]


def check_telegram_authorization(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_check_telegram_authorization_async(config))


def begin_telegram_login(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_begin_telegram_login_async(config))


def complete_telegram_login(config: TelegramConfig, code: str, phone_code_hash: str) -> dict[str, object]:
    return asyncio.run(_complete_telegram_login_async(config, code, phone_code_hash))


def _normalize_url_text(text: str) -> str:
    cleaned = str(text or '').strip()
    if not cleaned:
        return ''
    cleaned = cleaned.lstrip('-*').strip()
    if '://' in cleaned:
        return cleaned
    if cleaned.startswith('www.'):
        return f'https://{cleaned}'
    if cleaned.startswith(('t.me/', 'telegram.me/', 'telegram.dog/')):
        return f'https://{cleaned}'
    if '.' in cleaned.split('/')[0]:
        return f'https://{cleaned}'
    return cleaned


def _coerce_tasks(task_lines: Iterable[str] | Iterable[DownloadTask] | str) -> list[DownloadTask]:
    if isinstance(task_lines, str):
        return build_download_tasks(parse_task_lines(task_lines))
    items = list(task_lines)
    if not items:
        return []
    if all(isinstance(item, DownloadTask) for item in items):
        return [item for item in items if isinstance(item, DownloadTask)]
    return build_download_tasks(str(item) for item in items)


def _build_backend_status(module_name: str, label: str) -> dict[str, object]:
    available = importlib.util.find_spec(module_name) is not None
    return {
        'available': available,
        'label': label,
        'message': f'已检测到 {module_name}' if available else f'未安装 {module_name}',
        'path': module_name,
    }


async def _check_telegram_authorization_async(config: TelegramConfig) -> dict[str, object]:
    _require_telegram_backend()
    client = await _create_telegram_client(config)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        return {
            'authorized': authorized,
            'message': 'Telegram 会话已登录' if authorized else 'Telegram 尚未登录，请先发送验证码并完成登录',
        }
    finally:
        await client.disconnect()


async def _begin_telegram_login_async(config: TelegramConfig) -> dict[str, object]:
    _require_telegram_backend()
    client = await _create_telegram_client(config)
    try:
        await client.connect()
        if await client.is_user_authorized():
            return {
                'authorized': True,
                'sent': False,
                'phone_code_hash': '',
                'message': 'Telegram 会话已登录',
            }
        result = await client.send_code_request(config.phone)
        return {
            'authorized': False,
            'sent': True,
            'phone_code_hash': getattr(result, 'phone_code_hash', ''),
            'message': '验证码已发送，请输入验证码后点击登录',
        }
    finally:
        await client.disconnect()


async def _complete_telegram_login_async(config: TelegramConfig, code: str, phone_code_hash: str) -> dict[str, object]:
    _require_telegram_backend()
    cleaned_code = str(code or '').strip()
    cleaned_hash = str(phone_code_hash or '').strip()
    if not cleaned_code:
        raise ValueError('请输入 Telegram 验证码')
    if not cleaned_hash:
        raise ValueError('请先发送验证码')
    from telethon.errors import SessionPasswordNeededError

    client = await _create_telegram_client(config)
    try:
        await client.connect()
        if await client.is_user_authorized():
            return {'authorized': True, 'message': 'Telegram 会话已登录'}
        try:
            await client.sign_in(phone=config.phone, code=cleaned_code, phone_code_hash=cleaned_hash)
        except SessionPasswordNeededError as exc:
            raise DownloadError('当前账号开启了两步验证，v1 暂不支持密码验证') from exc
        return {'authorized': True, 'message': 'Telegram 登录成功'}
    finally:
        await client.disconnect()


async def _create_telegram_client(config: TelegramConfig):
    from telethon import TelegramClient

    api_id = str(config.api_id).strip()
    try:
        api_id_int = int(api_id)
    except ValueError as exc:
        raise ValueError('Telegram API ID 必须是整数') from exc
    session_path = Path(config.session_file).expanduser()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(str(session_path), api_id_int, str(config.api_hash).strip())


def _require_telegram_backend() -> None:
    if importlib.util.find_spec('telethon') is None:
        raise DownloadError('未安装 Telethon，无法使用 Telegram 下载')


def _require_web_backend() -> None:
    if importlib.util.find_spec('yt_dlp') is None:
        raise DownloadError('未安装 yt-dlp，无法解析网页视频')


async def _download_telegram_entries(
    entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    config: TelegramConfig | None,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    if config is None:
        for index, task in entries:
            _emit_task_start(progress_cb, index, total_tasks, task)
            results[index] = _make_result(task, False, [], 'Telegram 配置缺失')
            _emit_task_done(progress_cb, len(results), total_tasks)
        return results
    try:
        client = await _create_telegram_client(config)
        await client.connect()
        if not await client.is_user_authorized():
            message = 'Telegram 尚未登录，请先在页面完成验证码登录'
            for index, task in entries:
                _emit_task_start(progress_cb, index, total_tasks, task)
                results[index] = _make_result(task, False, [], message)
                _emit_task_done(progress_cb, len(results), total_tasks)
            return results
        for index, task in entries:
            _emit_task_start(progress_cb, index, total_tasks, task)
            try:
                results[index] = await _download_single_telegram_task(client, task, output_root, options, progress_cb)
            except Exception as exc:
                results[index] = _make_result(task, False, [], str(exc))
            _emit_task_done(progress_cb, len(results), total_tasks)
        return results
    finally:
        if 'client' in locals():
            await client.disconnect()


async def _download_single_telegram_task(client, task: DownloadTask, output_root: Path, options: DownloadOptions, progress_cb: ProgressCallback | None) -> dict[str, object]:
    parts = _parse_telegram_url(task.source_url)
    entity = await _resolve_telegram_entity(client, parts)
    if task.source_kind == 'telegram_message':
        if parts.message_id is None:
            raise DownloadError('Telegram 消息链接缺少消息 ID')
        message = await client.get_messages(entity, ids=parts.message_id)
        if not message or not _message_matches_media_selection(message, options):
            raise DownloadError('该 Telegram 消息中没有符合筛选条件的媒体')
        output_folder = _resolve_task_output_dir(output_root, task)
        output_folder.mkdir(parents=True, exist_ok=True)
        file_path = await _download_telegram_message_media(
            client,
            message,
            output_folder,
            fallback_prefix=task.target_title or 'telegram_video',
            options=options,
            progress_cb=progress_cb,
        )
        _emit(progress_cb, f'Telegram OK -> {file_path.name}')
        return _make_result(task, True, [file_path], '')

    recent_limit = None if options.telegram_download_all_messages else options.telegram_recent_limit
    date_from = options.telegram_date_from
    date_to = options.telegram_date_to
    after_utc = _date_start_utc(date_from)
    before_utc = _date_end_utc(date_to)
    output_folder = _resolve_task_output_dir(output_root, task, default_name=_get_entity_title(entity))
    output_folder.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    scanned_count = 0
    matched_count = 0
    async for message in client.iter_messages(entity, limit=recent_limit or None):
        scanned_count += 1
        message_date = _normalize_message_datetime(getattr(message, 'date', None))
        if before_utc is not None and message_date is not None and message_date > before_utc:
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        if after_utc is not None and message_date is not None and message_date < after_utc:
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        if not _message_matches_media_selection(message, options):
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        matched_count += 1
        _emit_scan_progress(progress_cb, scanned_count, matched_count)
        file_path = await _download_telegram_message_media(
            client,
            message,
            output_folder,
            fallback_prefix=f'{task.target_title or "telegram_video"}_{message.id}',
            options=options,
            progress_cb=progress_cb,
        )
        files.append(file_path)
        _emit(progress_cb, f'Telegram OK -> {file_path.name}')
    if not files:
        raise DownloadError('该聊天范围内未找到符合筛选条件的媒体')
    return _make_result(task, True, files, '')


async def _resolve_telegram_entity(client, parts: TelegramUrlParts):
    from telethon import functions, utils
    from telethon.errors import UserAlreadyParticipantError

    if parts.invite_hash:
        try:
            updates = await client(functions.messages.ImportChatInviteRequest(parts.invite_hash))
        except UserAlreadyParticipantError:
            try:
                return await client.get_entity(f'https://t.me/+{parts.invite_hash}')
            except Exception:
                pass
            async for dialog in client.iter_dialogs():
                if _dialog_matches_invite(dialog, parts.invite_hash):
                    return dialog.entity
            raise DownloadError('无法根据邀请链接解析聊天，请确认账号已加入该会话')
        except Exception as exc:
            raise DownloadError(f'无法访问 Telegram 邀请链接: {exc}') from exc
        if updates is not None:
            chats = getattr(updates, 'chats', None) or []
            if chats:
                return chats[0]
        raise DownloadError('邀请链接解析失败，未返回聊天信息')
    if isinstance(parts.entity_ref, int):
        expected_peer_id = int(f'-100{parts.entity_ref}')
        async for dialog in client.iter_dialogs():
            if utils.get_peer_id(dialog.entity) == expected_peer_id:
                return dialog.entity
        raise DownloadError('当前账号没有找到该私有聊天，请确认已加入并且聊天可见')
    try:
        return await client.get_entity(parts.entity_ref)
    except Exception as exc:
        raise DownloadError(f'无法解析 Telegram 聊天: {exc}') from exc


async def _download_telegram_message_media(
    client,
    message,
    output_dir: Path,
    fallback_prefix: str,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None = None,
) -> Path:
    file_info = getattr(message, 'file', None)
    original_name = ''
    suffix = ''
    if file_info is not None:
        original_name = getattr(file_info, 'name', '') or ''
        suffix = getattr(file_info, 'ext', '') or ''
    if _is_photo_message(message) and options.telegram_include_photos:
        suffix = Path(original_name).suffix or suffix or '.jpg'
        target_name = sanitize_filename_component(Path(original_name).stem or fallback_prefix) + suffix
    elif original_name:
        target_name = sanitize_filename_component(Path(original_name).stem) + (Path(original_name).suffix or suffix or '.mp4')
    else:
        target_name = sanitize_filename_component(fallback_prefix) + (suffix or '.mp4')
    target_path = ensure_unique_path(output_dir / target_name)
    downloaded = await client.download_media(
        message,
        file=str(target_path),
        progress_callback=_make_telegram_progress_callback(progress_cb, target_path.name),
    )
    if not downloaded:
        raise DownloadError('Telegram 视频下载失败')
    return Path(downloaded)


def _parse_telegram_url(url: str) -> TelegramUrlParts:
    parsed = urlparse(_normalize_url_text(url))
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        raise ValueError('无效 Telegram 链接')
    if parts[0] == 'joinchat':
        if len(parts) < 2:
            raise ValueError('无效 Telegram 邀请链接')
        return TelegramUrlParts(entity_ref='', message_id=None, invite_hash=parts[1])
    if parts[0].startswith('+'):
        return TelegramUrlParts(entity_ref='', message_id=None, invite_hash=parts[0][1:])
    if parts[0] == 'c':
        if len(parts) < 2 or not parts[1].isdigit():
            raise ValueError('无效 Telegram 私有聊天链接')
        message_id = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
        return TelegramUrlParts(entity_ref=int(parts[1]), message_id=message_id)
    message_id = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
    return TelegramUrlParts(entity_ref=parts[0], message_id=message_id)


def _is_video_message(message) -> bool:
    if message is None:
        return False
    if getattr(message, 'video', None) is not None:
        return True
    file_info = getattr(message, 'file', None)
    mime_type = getattr(file_info, 'mime_type', '') or ''
    if mime_type.startswith('video/'):
        return True
    document = getattr(message, 'document', None)
    doc_mime = getattr(document, 'mime_type', '') or ''
    return doc_mime.startswith('video/')


def _is_photo_message(message) -> bool:
    if message is None:
        return False
    if getattr(message, 'photo', None) is not None:
        return True
    file_info = getattr(message, 'file', None)
    mime_type = getattr(file_info, 'mime_type', '') or ''
    if mime_type.startswith('image/'):
        return True
    document = getattr(message, 'document', None)
    doc_mime = getattr(document, 'mime_type', '') or ''
    return doc_mime.startswith('image/')


def _message_matches_media_selection(message, options: DownloadOptions) -> bool:
    if options.telegram_include_videos and _is_video_message(message):
        return True
    if options.telegram_include_photos and _is_photo_message(message):
        return True
    return False


def _get_entity_title(entity) -> str:
    return getattr(entity, 'title', '') or getattr(entity, 'username', '') or getattr(entity, 'first_name', '') or 'telegram_chat'


def _dialog_matches_invite(dialog, invite_hash: str) -> bool:
    """Best-effort match of a dialog to an invite hash via username. Last-resort fallback."""
    invite_lower = str(invite_hash or '').lower()
    if not invite_lower:
        return False
    username = str(getattr(dialog.entity, 'username', '') or '').lower()
    return bool(username and invite_lower in username)


def _resolve_task_output_dir(output_root: Path, task: DownloadTask, default_name: str = '') -> Path:
    subdir = sanitize_filename_component(task.output_subdir or default_name, fallback='').strip()
    if not subdir:
        return output_root
    return output_root / subdir


def _normalize_message_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _date_start_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _date_end_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


def _is_m3u8_url(url: str) -> bool:
    return str(url or '').lower().split('?', 1)[0].endswith('.m3u8')


def _download_web_candidate(
    candidate_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
) -> dict[str, object]:
    if _is_m3u8_url(candidate_url) and ffmpeg_path:
        return _download_m3u8_with_ffmpeg(
            candidate_url,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
        )
    return _download_url_with_ytdlp(
        candidate_url,
        output_root,
        options,
        progress_cb,
        title_hint=task.target_title,
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
) -> tuple[list[Path], Exception | None]:
    downloaded_files: list[Path] = []
    last_error: Exception | None = None
    total_candidates = len(candidates)
    for candidate_index, candidate in enumerate(candidates, start=1):
        try:
            _emit_file_select(progress_cb, candidate, candidate_index, total_candidates)
            downloaded = _download_web_candidate(
                candidate,
                task,
                output_root,
                options,
                progress_cb,
                ffmpeg_path=ffmpeg_path,
            )
            files = [Path(item) for item in downloaded['files']]
            if not options.web_download_all_candidates and not download_all:
                return files, None
            downloaded_files.extend(files)
        except Exception as exc:
            last_error = exc
    return downloaded_files, last_error


def inspect_web_media_batch(urls: Iterable[str] | str, progress_cb: ProgressCallback | None = None) -> list[dict[str, object]]:
    items = parse_task_lines(urls) if isinstance(urls, str) else [_normalize_url_text(item) for item in urls]
    web_urls = [url for url in items if url and classify_source(url) == 'web']
    results: list[dict[str, object]] = []
    total = len(web_urls)
    for index, url in enumerate(web_urls, start=1):
        _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_start|index={index}|total={total}|url={url}')
        try:
            result = inspect_web_media_candidates(url)
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


def inspect_web_media_candidates(source_url: str) -> dict[str, object]:
    candidates, source = _collect_web_media_candidates(source_url)
    return {
        'source_url': source_url,
        'success': True,
        'candidate_count': len(candidates),
        'candidates': candidates,
        'source': source,
        'error': '',
    }


def _download_web_task(task: DownloadTask, output_root: Path, options: DownloadOptions, progress_cb: ProgressCallback | None) -> dict[str, object]:
    first_error = None
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(task.source_url)
    except Exception:
        ytdlp_candidates = []
    if len(ytdlp_candidates) > 1:
            try:
                ffmpeg_path = shutil.which('ffmpeg') or ''
                if options.web_download_all_candidates:
                    downloaded_files, last_error = _download_web_candidates(
                        ytdlp_candidates,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
                elif options.web_candidate_indices is not None:
                    selected = _pick_candidates(ytdlp_candidates, options.web_candidate_indices)
                    downloaded_files, last_error = _download_web_candidates(
                        selected,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                        download_all=True,
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
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
            except Exception as exc:
                first_error = exc
    try:
        downloaded = _download_url_with_ytdlp(task.source_url, output_root, options, progress_cb, title_hint=task.target_title)
        return _make_result(task, True, downloaded['files'], '')
    except Exception as exc:
        first_error = exc
    try:
        candidates = _extract_media_candidates(_fetch_webpage_html(task.source_url), task.source_url)
    except Exception as exc:
        raise DownloadError(f'{first_error}; 网页兜底解析失败: {exc}') from exc
    if not candidates:
        raise DownloadError(f'{first_error}; 网页中未找到可下载媒体地址')
    ffmpeg_path = shutil.which('ffmpeg') or ''
    if options.web_download_all_candidates:
        downloaded_files, last_error = _download_web_candidates(
            candidates,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
        )
        if downloaded_files:
            return _make_result(task, True, downloaded_files, '')
        raise DownloadError(f'{first_error}; 全部候选下载失败: {last_error}')
    if options.web_candidate_indices is not None:
        selected = _pick_candidates(candidates, options.web_candidate_indices)
        downloaded_files, last_error = _download_web_candidates(
            selected,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
            download_all=True,
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


def _collect_web_media_candidates(source_url: str) -> tuple[list[str], str]:
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(source_url)
    except Exception:
        ytdlp_candidates = []
    if ytdlp_candidates:
        return ytdlp_candidates, 'yt-dlp'
    try:
        html_candidates = _extract_media_candidates(_fetch_webpage_html(source_url), source_url)
    except Exception:
        html_candidates = []
    if html_candidates:
        return html_candidates, 'html'
    if _supports_ytdlp_direct_media(source_url):
        return [source_url], 'page'
    return [], ''


def _download_url_with_ytdlp(
    source_url: str,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    title_hint: str = '',
) -> dict[str, object]:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    info = YoutubeDL({'quiet': True, 'skip_download': True, 'noplaylist': True, 'nocheckcertificate': True}).extract_info(source_url, download=False)
    title = sanitize_filename_component(str(info.get('title') or title_hint or 'video'))
    media_id = sanitize_filename_component(str(info.get('id') or 'video'))
    base_stem = options.filename_template.replace('%(title)s', title).replace('%(id)s', media_id).replace('.%(ext)s', '')
    unique_stem = ensure_unique_stem(output_root, base_stem)
    ydl_opts = {
        'format': 'bv*+ba/b',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'windowsfilenames': True,
        'overwrites': bool(options.overwrite),
        'outtmpl': str(output_root / f'{unique_stem}.%(ext)s'),
        'progress_hooks': [_make_web_progress_hook(progress_cb, _current_token())],
        'concurrent_fragment_downloads': 16,
        'file_access_retries': 3,
        'fragment_retries': 5,
        'retries': 5,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'http_chunk_size': 10 * 1024 * 1024,
    }
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg
    if options.web_use_browser_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(source_url, download=True)
    created = sorted(output_root.glob(f'{unique_stem}.*'))
    created = [path.resolve() for path in created if path.is_file()]
    if not created:
        raise DownloadError('网页视频下载完成，但未找到输出文件')
    _emit(progress_cb, f'网页 OK -> {created[0].name}')
    return {
        'success': True,
        'files': created,
    }


def _fetch_webpage_html(url: str) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    request = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': url,
        },
    )
    with urlopen(request, timeout=20, context=ctx) as response:
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


def _extract_ytdlp_entry_candidates(page_url: str) -> list[str]:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    info = YoutubeDL({'quiet': True, 'skip_download': True, 'nocheckcertificate': True}).extract_info(page_url, download=False)
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


def _supports_ytdlp_direct_media(source_url: str) -> bool:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    info = YoutubeDL({'quiet': True, 'skip_download': True, 'noplaylist': True, 'nocheckcertificate': True}).extract_info(source_url, download=False)
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


def _download_m3u8_with_ffmpeg(
    media_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
) -> dict[str, object]:
    ffmpeg = ffmpeg_path or shutil.which('ffmpeg')
    if not ffmpeg:
        raise DownloadError('未检测到 ffmpeg，无法直接下载 m3u8')
    base_stem = ensure_unique_stem(output_root, sanitize_filename_component(task.target_title or 'video'))
    output_path = ensure_unique_path(output_root / f'{base_stem}.mp4')
    total_duration = _probe_stream_duration(media_url, ffmpeg)
    command = [
        ffmpeg,
        '-y' if options.overwrite else '-n',
        '-i', media_url,
        '-c', 'copy',
        '-progress', 'pipe:1',
        '-nostats',
        '-loglevel', 'error',
        str(output_path),
    ]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    started = monotonic()
    last_emit = 0.0
    for line in proc.stdout:
        token = _current_token()
        if token and token.cancel.is_set():
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            raise CancelledError('ffmpeg 下载已取消')
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
    proc.wait()
    if proc.returncode != 0:
        stderr = (proc.stderr.read() if proc.stderr else '').strip()
        raise DownloadError(stderr or 'ffmpeg 下载失败')
    _emit(progress_cb, f'网页 OK -> {output_path.name}')
    return {
        'success': True,
        'files': [output_path],
    }


def _probe_stream_duration(url: str, ffmpeg_path: str = '') -> float | None:
    """Get stream duration via ffprobe. Returns seconds or None."""
    ffprobe = Path(ffmpeg_path).with_name('ffprobe') if ffmpeg_path else 'ffprobe'
    if ffmpeg_path:
        ffprobe = str(ffprobe)
    try:
        result = subprocess.run(
            [ffprobe, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', url],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    return None


def _make_web_progress_hook(progress_cb: ProgressCallback | None, token: Token | None = None):
    def hook(status: dict[str, object]) -> None:
        if token and token.cancel.is_set():
            raise CancelledError('yt-dlp 下载已取消')
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


def _make_telegram_progress_callback(progress_cb: ProgressCallback | None, file_name: str):
    clean_name = sanitize_filename_component(Path(str(file_name or 'telegram_media')).name, fallback='telegram_media')
    started_at = monotonic()
    last_emitted_at = started_at
    last_percent = -1.0

    def callback(received: int, total: int) -> None:
        nonlocal last_emitted_at, last_percent
        current = max(0, int(received or 0))
        total_bytes = max(0, int(total or 0))
        percent = (current * 100.0 / total_bytes) if total_bytes else 0.0
        now = monotonic()
        if current < total_bytes and now - last_emitted_at < 0.35 and percent - last_percent < 1.0:
            return
        elapsed = max(now - started_at, 1e-6)
        speed_value = current / elapsed if current > 0 else 0.0
        speed_text = _format_byte_rate(speed_value)
        eta_text = ''
        if speed_value > 0 and total_bytes > current:
            eta_text = _format_eta_seconds(int((total_bytes - current) / speed_value))
        parts = [f'name={clean_name}', f'percent={percent:.2f}']
        if speed_text:
            parts.append(f'speed={speed_text}')
        if eta_text:
            parts.append(f'eta={eta_text}')
        _emit(progress_cb, '__HYL_PROGRESS__|tg_media|' + '|'.join(parts))
        _emit(progress_cb, _build_download_log_message(clean_name, speed_text, _format_progress_percent(percent), eta_text))
        last_emitted_at = now
        last_percent = percent

    return callback


def _emit_web_transfer_progress(
    progress_cb: ProgressCallback | None,
    file_name: str,
    percent_text: str,
    speed_text: str,
    eta_text: str,
) -> None:
    parts = [f'name={sanitize_filename_component(Path(str(file_name or "video")).name, fallback="video")}']
    try:
        parts.append(f'percent={float(percent_text)}')
    except ValueError:
        pass
    if speed_text:
        parts.append(f'speed={speed_text}')
    if eta_text:
        parts.append(f'eta={eta_text}')
    _emit(progress_cb, '__HYL_PROGRESS__|web_status|' + '|'.join(parts))


def _normalize_progress_text(value: object) -> str:
    text = ANSI_ESCAPE_RE.sub('', str(value or ''))
    return WHITESPACE_RE.sub(' ', text).strip()


def _resolve_web_percent_text(status: dict[str, object]) -> str:
    percent = _normalize_progress_text(status.get('_percent_str', ''))
    if percent:
        return percent
    numeric_percent = _coerce_float(status.get('_percent'))
    if numeric_percent is not None:
        return _format_progress_percent(numeric_percent)
    downloaded = _coerce_float(status.get('downloaded_bytes'))
    total = _coerce_float(status.get('total_bytes'))
    estimate = _coerce_float(status.get('total_bytes_estimate'))
    denominator = total or estimate or 0.0
    if downloaded is not None and denominator > 0:
        return _format_progress_percent(downloaded * 100.0 / denominator)
    return ''


def _resolve_web_speed_text(status: dict[str, object]) -> str:
    speed = _normalize_progress_text(status.get('_speed_str', ''))
    if speed:
        return speed
    speed_value = _coerce_float(status.get('speed'))
    if speed_value is not None:
        return _format_byte_rate(speed_value)
    return ''


def _coerce_float(value: object) -> float | None:
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_download_log_message(file_name: str, speed_text: str, percent_text: str, eta_text: str = '') -> str:
    clean_name = str(file_name or 'video').strip() or 'video'
    clean_speed = _normalize_progress_text(speed_text) or '--'
    clean_percent = _normalize_progress_text(percent_text) or '--'
    parts = [f'正在下载 "{clean_name}" "{clean_speed}" "{clean_percent}"']
    if eta_text and eta_text.strip():
        clean_eta = _normalize_progress_text(eta_text)
        if clean_eta:
            parts.append(f'"{clean_eta}"')
    return ' '.join(parts)


def _format_progress_percent(percent: float) -> str:
    value = max(0.0, min(100.0, float(percent or 0.0)))
    text = f'{value:.1f}'.rstrip('0').rstrip('.')
    return f'{text}%'


def _format_byte_rate(bytes_per_second: float) -> str:
    rate = max(0.0, float(bytes_per_second or 0.0))
    if rate <= 0:
        return ''
    units = ['B/s', 'KiB/s', 'MiB/s', 'GiB/s']
    unit_index = 0
    while rate >= 1024.0 and unit_index < len(units) - 1:
        rate /= 1024.0
        unit_index += 1
    precision = 0 if unit_index == 0 else 1
    return f'{rate:.{precision}f} {units[unit_index]}'


def _format_eta_seconds(seconds: int) -> str:
    remaining = max(0, int(seconds or 0))
    hours, remainder = divmod(remaining, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f'{hours:d}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def _parse_ffmpeg_time(time_str: str) -> float:
    """Parse ffmpeg time string 'HH:MM:SS.xxxxxx' to seconds."""
    parts = time_str.strip().split(':')
    if len(parts) != 3:
        return 0.0
    try:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError:
        return 0.0


def _format_duration(seconds: float) -> str:
    s = max(0.0, seconds)
    h, r = divmod(int(s), 3600)
    m, sec = divmod(r, 60)
    if h:
        return f'{h}:{m:02d}:{sec:02d}'
    return f'{m:02d}:{sec:02d}'


def _estimate_download_rate(elapsed: float, media_seconds: float) -> float:
    """Estimate effective byte rate based on typical m3u8 bitrate (~2 Mbps)."""
    if elapsed <= 0 or media_seconds <= 0:
        return 0.0
    estimated_bytes = media_seconds * 250_000
    return estimated_bytes / elapsed


def _make_result(task: DownloadTask, success: bool, files: Iterable[Path], error: str) -> dict[str, object]:
    file_list = [str(Path(path)) for path in files]
    return {
        'source_url': task.source_url,
        'source_kind': task.source_kind,
        'title': task.target_title,
        'success': success,
        'error': error,
        'downloaded_count': len(file_list),
        'files': file_list,
    }


def _emit(progress_cb: ProgressCallback | None, message: str) -> None:
    if progress_cb is not None and message:
        progress_cb(message)


def _emit_task_start(progress_cb: ProgressCallback | None, index: int, total: int, task: DownloadTask) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|task_start|index={index}|total={total}|url={task.source_url}')


def _emit_task_done(progress_cb: ProgressCallback | None, completed: int, total: int) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|task_done|completed={completed}|total={total}')


def _emit_scan_progress(progress_cb: ProgressCallback | None, scanned: int, matched: int) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|tg_scan|matched={matched}|scanned={scanned}')


def _emit_file_select(progress_cb: ProgressCallback | None, file_label: str, index: int = 0, total: int = 0) -> None:
    parsed = urlparse(str(file_label or ''))
    label = Path(parsed.path).name if parsed.path else str(file_label or '')
    clean_label = sanitize_filename_component(label, fallback='media')
    _emit(progress_cb, f'__HYL_PROGRESS__|file|index={index}|name={clean_label}|total={total}')
