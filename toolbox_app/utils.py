from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# QSettings helpers
# ---------------------------------------------------------------------------

def save_setting(settings, key: str, value: str) -> None:
    settings.setValue(key, value)
    settings.sync()


def load_setting(settings, key: str, default: str = '') -> str:
    value = settings.value(key, default)
    return '' if value is None else str(value)


# ---------------------------------------------------------------------------
# Fallback signal (when PySide6 is unavailable)
# ---------------------------------------------------------------------------

class _FallbackSignal:
    def __init__(self):
        self._callbacks: list[object] = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self._callbacks):
            callback(*args)


# ---------------------------------------------------------------------------
# Windows hidden/system file detection
# ---------------------------------------------------------------------------

WINDOWS_HIDDEN_ATTRIBUTE = 0x2
WINDOWS_SYSTEM_ATTRIBUTE = 0x4
DEFAULT_SKIPPED_NAMES = {'desktop.ini', 'thumbs.db'}


def is_hidden_or_system_file(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.name.startswith('.') or candidate.name.lower() in DEFAULT_SKIPPED_NAMES:
        return True
    try:
        attributes = candidate.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & (WINDOWS_HIDDEN_ATTRIBUTE | WINDOWS_SYSTEM_ATTRIBUTE))


# ---------------------------------------------------------------------------
# Category extensions & order
# ---------------------------------------------------------------------------

CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    '图片': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.tif', '.tiff', '.svg', '.ico'},
    '视频': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
    '音频': {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma', '.ncm'},
    '文档': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv'},
    '压缩包': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
    '程序': {'.exe', '.msi', '.bat', '.cmd', '.ps1', '.py'},
    '其他': set(),
}

CATEGORY_ORDER = ('图片', '视频', '音频', '文档', '压缩包', '程序', '其他')


# ---------------------------------------------------------------------------
# Cache key & name conflict resolution
# ---------------------------------------------------------------------------

def _build_cache_key(path: str | Path) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return str(resolved).lower(), stat.st_size, stat.st_mtime_ns


def resolve_name_conflict(path: str | Path, max_attempts: int = 1000) -> Path:
    candidate = Path(path)
    if not candidate.exists():
        return candidate
    for index in range(1, max_attempts + 1):
        renamed = candidate.with_name(f'{candidate.stem}({index}){candidate.suffix}')
        if not renamed.exists():
            return renamed
    raise RuntimeError(f'重名文件过多，超过最大尝试次数: {max_attempts}')
