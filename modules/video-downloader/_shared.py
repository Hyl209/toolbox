"""Shared utility functions used across multiple sub-modules."""
from __future__ import annotations

import importlib.util
import re
import shutil
import threading
from pathlib import Path
from urllib.parse import urlparse

TELEGRAM_HOSTS = {'t.me', 'telegram.me', 'telegram.dog', 'www.t.me', 'www.telegram.me'}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WHITESPACE_RE = re.compile(r'\s+')
EMBEDDED_URL_RE = re.compile(r'https?://[^\s<>"\'`]+', re.IGNORECASE)
WEB_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
SESSION_FILE_NAME = 'telegram.session'
_stem_lock = threading.Lock()


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
        while any(_find_files_by_stem(folder, candidate)):
            candidate = f'{safe_stem} ({index})'
            index += 1
        return candidate


def _find_files_by_stem(directory: str | Path, stem: str) -> list[Path]:
    folder = Path(directory)
    if not folder.exists():
        return []
    return [path for path in folder.iterdir() if path.is_file() and path.stem == stem]


def _find_completed_downloads(directory: str | Path, stem: str) -> list[Path]:
    unfinished_suffixes = {'.part', '.ytdl', '.tmp', '.aria2'}
    return [
        path.resolve()
        for path in _find_files_by_stem(directory, stem)
        if path.suffix.lower() not in unfinished_suffixes and path.stat().st_size > 0
    ]


def _trim_url_suffix(text: str) -> str:
    return str(text or '').rstrip(' \t\r\n,.;:!?"\')}]\u3001\u3002\uff01\uff1f\uff1b\uff1a\u300b\u300d\u300f\u3011\uff09')


def _normalize_url_text(text: str) -> str:
    cleaned = str(text or '').strip()
    if not cleaned:
        return ''
    cleaned = cleaned.lstrip('-*').strip()
    if cleaned.startswith(('http://', 'https://')):
        return _trim_url_suffix(cleaned)
    match = EMBEDDED_URL_RE.search(cleaned)
    if match:
        return _trim_url_suffix(match.group(0))
    if '://' in cleaned:
        return cleaned
    if cleaned.startswith('www.'):
        return f'https://{cleaned}'
    if cleaned.startswith(('t.me/', 'telegram.me/', 'telegram.dog/')):
        return f'https://{cleaned}'
    if '.' in cleaned.split('/')[0]:
        return f'https://{cleaned}'
    return cleaned


def classify_source(url: str) -> str:
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


def guess_task_title(url: str) -> str:
    parsed = urlparse(_normalize_url_text(url))
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return sanitize_filename_component(parsed.netloc or 'video')
    return sanitize_filename_component(parts[-1] or parts[0] or parsed.netloc or 'video')


def _resolve_bundled_tool(name: str) -> str:
    suffix = '.exe' if not name.lower().endswith('.exe') else ''
    candidate = Path(__file__).resolve().parent / 'bin' / f'{name}{suffix}'
    return str(candidate) if candidate.is_file() else ''


def _resolve_aria2c_path() -> str:
    bundled = _resolve_bundled_tool('aria2c')
    if bundled:
        return bundled
    return shutil.which('aria2c') or ''


def _build_backend_status(module_name: str, label: str) -> dict[str, object]:
    available = importlib.util.find_spec(module_name) is not None
    return {
        'available': available,
        'label': label,
        'message': f'已检测到 {module_name}' if available else f'未安装 {module_name}',
        'path': module_name,
    }


def _build_web_headers(referer_url: str = '') -> dict[str, str]:
    headers = {
        'User-Agent': WEB_USER_AGENT,
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    if referer_url:
        headers['Referer'] = referer_url
    return headers


def _build_ffmpeg_header_text(referer_url: str = '') -> str:
    return ''.join(f'{key}: {value}\r\n' for key, value in _build_web_headers(referer_url).items())
