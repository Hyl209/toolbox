"""Progress formatting, markers, and helper emitters."""
from __future__ import annotations

import re
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

from .models import DownloadTask, ProgressCallback
from . import _shared as _s

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
WHITESPACE_RE = re.compile(r'\s+')


def _normalize_progress_text(value: object) -> str:
    text = ANSI_ESCAPE_RE.sub('', str(value or ''))
    return WHITESPACE_RE.sub(' ', text).strip()


def _coerce_float(value: object) -> float | None:
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


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
    if elapsed <= 0 or media_seconds <= 0:
        return 0.0
    estimated_bytes = media_seconds * 250_000
    return estimated_bytes / elapsed


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


def _emit_web_transfer_progress(
    progress_cb: ProgressCallback | None,
    file_name: str,
    percent_text: str,
    speed_text: str,
    eta_text: str,
) -> None:
    parts = [f'name={_s.sanitize_filename_component(Path(str(file_name or "video")).name, fallback="video")}']
    try:
        parts.append(f'percent={float(percent_text)}')
    except ValueError:
        pass
    if speed_text:
        parts.append(f'speed={speed_text}')
    if eta_text:
        parts.append(f'eta={eta_text}')
    _emit(progress_cb, '__HYL_PROGRESS__|web_status|' + '|'.join(parts))


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
    clean_label = _s.sanitize_filename_component(label, fallback='media')
    _emit(progress_cb, f'__HYL_PROGRESS__|file|index={index}|name={clean_label}|total={total}')


def _make_result(task: DownloadTask, success: bool, files, error: str) -> dict[str, object]:
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


def _make_telegram_progress_callback(progress_cb: ProgressCallback | None, file_name: str):
    clean_name = _s.sanitize_filename_component(Path(str(file_name or 'telegram_media')).name, fallback='telegram_media')
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
