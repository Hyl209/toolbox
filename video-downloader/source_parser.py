"""URL classification, task line parsing, and validation helpers."""
from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from .models import (
    CancelledError, DownloadError, DownloadOptions, DownloadTask,
    ProgressCallback, TelegramConfig, Token,
)
from . import _shared as _s

# Re-export commonly used _shared functions for sibling modules
classify_source = _s.classify_source
guess_task_title = _s.guess_task_title

ARIA2_PROGRESS_RE = re.compile(
    r'\((?P<percent>\d+(?:\.\d+)?)%\).*?\bDL:(?P<speed>[^\s\]]+)(?:.*?\bETA:(?P<eta>[^\s\]]+))?',
    re.IGNORECASE,
)

# Thread-local token state
import threading as _threading
_state = _threading.local()


def _check_cancel(token: Token) -> None:
    if token.cancel.is_set():
        raise CancelledError('下载已取消')


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
        normalized = _s._normalize_url_text(raw)
        if normalized:
            unique.setdefault(normalized, None)
    return list(unique.keys())


def build_download_tasks(urls: Iterable[str]) -> list[DownloadTask]:
    from .models import DownloadTask as DT
    tasks: list[DT] = []
    for raw in urls:
        normalized = _s._normalize_url_text(raw)
        if not normalized:
            continue
        tasks.append(DT(
            source_url=normalized,
            source_kind=_s.classify_source(normalized),
            target_title=_s.guess_task_title(normalized),
        ))
    return tasks


def _coerce_tasks(task_lines: Iterable[str] | Iterable[DownloadTask] | str) -> list[DownloadTask]:
    if isinstance(task_lines, str):
        return build_download_tasks(parse_task_lines(task_lines))
    items = list(task_lines)
    if not items:
        return []
    if all(isinstance(item, DownloadTask) for item in items):
        return [item for item in items if isinstance(item, DownloadTask)]
    return build_download_tasks(str(item) for item in items)


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


def _parse_candidate_mode(value: str) -> tuple[str, str]:
    cleaned = str(value or '').strip()
    lower = cleaned.lower()
    for prefix, mode in [('before', 'before'), ('after', 'after'), ('not', 'exclude'), ('no', 'exclude')]:
        if lower.startswith(prefix) and len(cleaned) > len(prefix):
            after = cleaned[len(prefix):]
            if after[0].isdigit():
                return mode, after
    return 'pick', cleaned


def _resolve_candidate_indices(mode: str, indices: list[int] | None, total: int) -> list[int] | None:
    if mode == 'before' and indices and len(indices) == 1:
        n = indices[0]
        return list(range(1, min(n, total) + 1))
    if mode == 'after' and indices and len(indices) == 1:
        n = indices[0]
        return list(range(max(1, n), total + 1))
    return indices


def normalize_positive_indices(value: str | int | None, field_label: str) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f'{field_label}必须大于 0')
        return [value]
    cleaned = _parse_candidate_mode(str(value).strip())[1]
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
                errors.append('未勾选"全部消息"时，最近消息条数不能为 0')
    return errors


def probe_download_backends() -> dict[str, dict[str, object]]:
    import shutil as _shutil
    ffmpeg = _shutil.which('ffmpeg')
    aria2c = _s._resolve_aria2c_path()
    return {
        'telethon': _s._build_backend_status('telethon', 'Telegram 登录/下载'),
        'yt_dlp': _s._build_backend_status('yt_dlp', '网页视频解析'),
        'aria2c': {
            'available': bool(aria2c),
            'label': '网页多连接加速',
            'message': f'已检测到 aria2c' if aria2c else '未检测到 aria2c，网页视频将使用 yt-dlp 内置下载',
            'path': aria2c,
        },
        'ffmpeg': {
            'available': bool(ffmpeg),
            'label': '媒体合并/转封装',
            'message': '已检测到 ffmpeg' if ffmpeg else '未检测到 ffmpeg，部分站点可能无法合并音视频',
            'path': ffmpeg or '',
        },
    }
