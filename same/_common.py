"""Shared constants, cache classes, and utility functions used across sub-modules."""
from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import threading
from pathlib import Path

from toolbox_app.utils import _build_cache_key, resolve_name_conflict


DEFAULT_TARGET_DIR_NAME = '重复文件'
HASH_CHUNK_SIZE = 1024 * 1024
FFPROBE_PATH = shutil.which('ffprobe')
FFMPEG_PATH = shutil.which('ffmpeg')
VIDEO_SUFFIXES = {
    '.3gp',
    '.avi',
    '.flv',
    '.m2ts',
    '.m4v',
    '.mkv',
    '.mov',
    '.mp4',
    '.mpeg',
    '.mpg',
    '.mts',
    '.ts',
    '.webm',
    '.wmv',
}
VIDEO_SAMPLE_COUNT = 6
VIDEO_FRAME_WIDTH = 24
VIDEO_FRAME_HEIGHT = 24
VIDEO_MIN_FRAME_COUNT = 3
VIDEO_DURATION_TOLERANCE_SECONDS = 1.0
VIDEO_ASPECT_RATIO_TOLERANCE = 0.12
VIDEO_SIMILARITY_THRESHOLD = 0.95
MEDIA_COMMAND_TIMEOUT_SECONDS = 20
VIDEO_PARALLEL_WORKERS = max(2, min(6, os.cpu_count() or 4))
_CACHE_MAX_SIZE = 2048


class _BoundedCache:
    """Thread-safe bounded dict with LRU-like eviction.

    Evicts the oldest half of entries when the cache exceeds *max_size*.
    """

    def __init__(self, max_size: int = _CACHE_MAX_SIZE) -> None:
        self._max_size = max_size
        self._data: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            return self._data.get(key, default)

    def __contains__(self, key):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            return key in self._data

    def __getitem__(self, key):
        with self._lock:
            value = self._data[key]
            self._data.move_to_end(key)
            return value

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            if len(self._data) > self._max_size:
                keep = self._max_size // 2
                while len(self._data) > keep:
                    self._data.popitem(last=False)


_FILE_HASH_CACHE = _BoundedCache()
_VIDEO_METADATA_CACHE = _BoundedCache()
_VIDEO_SIGNATURE_CACHE = _BoundedCache()


def _ensure_root(root: str | Path) -> Path:
    path = Path(root).resolve()
    if not path.exists():
        raise FileNotFoundError(f'文件夹不存在: {path}')
    if not path.is_dir():
        raise NotADirectoryError(f'不是文件夹: {path}')
    return path


def _normalize_target_dir_name(target_dir_name: str | Path) -> str:
    cleaned = str(target_dir_name).strip()
    if not cleaned:
        return DEFAULT_TARGET_DIR_NAME
    leaf = Path(cleaned).name
    if leaf in {'', '.', '..'}:
        return DEFAULT_TARGET_DIR_NAME
    return leaf


def _iter_top_level_files(root: Path) -> list[Path]:
    return [
        item.resolve()
        for item in sorted(root.iterdir(), key=lambda item: item.name.lower())
        if item.is_file()
    ]


def _iter_recursive_files(root: Path, target_dir_name: str) -> list[Path]:
    files: list[Path] = []
    skipped_name = target_dir_name.casefold()
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(
            [name for name in dir_names if name.casefold() != skipped_name],
            key=str.lower,
        )
        for file_name in sorted(file_names, key=str.lower):
            files.append(Path(current_root, file_name).resolve())
    return files


def _scan_files_from_root(root: Path, recursive: bool, target_dir_name: str) -> list[Path]:
    if recursive:
        return _iter_recursive_files(root, target_dir_name)
    return _iter_top_level_files(root)


def scan_files(root: str | Path, recursive: bool, target_dir_name: str = DEFAULT_TARGET_DIR_NAME) -> list[Path]:
    folder = _ensure_root(root)
    normalized_target_dir_name = _normalize_target_dir_name(target_dir_name)
    return _scan_files_from_root(folder, recursive, normalized_target_dir_name)


def _group_by_size(files: list[Path]) -> dict[int, list[Path]]:
    buckets: dict[int, list[Path]] = {}
    for file in files:
        buckets.setdefault(file.stat().st_size, []).append(file)
    return buckets


def _is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_SUFFIXES


def _map_parallel(func, items: list[Path]) -> list[object]:
    if len(items) <= 1:
        return [func(item) for item in items]
    worker_count = min(VIDEO_PARALLEL_WORKERS, len(items))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(func, items))


def _safe_float(value: object) -> float | None:
    if value in {None, '', 'N/A'}:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _build_group(
    keeper: Path,
    grouped_files: list[Path],
    match_mode: str,
    digest: str = '',
    similarity: float = 0.0,
) -> dict[str, object]:
    group: dict[str, object] = {
        'suffix': keeper.suffix.lower(),
        'size': keeper.stat().st_size,
        'hash': digest,
        'keeper': keeper,
        'duplicates': grouped_files[1:],
        'files': grouped_files,
        'match_mode': match_mode,
    }
    if match_mode == 'video_similarity':
        group['similarity'] = similarity
        group['similarity_threshold'] = VIDEO_SIMILARITY_THRESHOLD
    return group


def _split_video_and_other_files(files: list[Path]) -> tuple[list[Path], list[Path]]:
    video_files: list[Path] = []
    other_files: list[Path] = []
    for file in files:
        if _is_video_file(file):
            video_files.append(file)
        else:
            other_files.append(file)
    return video_files, other_files


class _FnRef:
    """Mutable function reference holder.

    Allows monkey-patching from the re-export layer (converter.py) to propagate
    into sub-modules at call time without circular imports.
    """
    __slots__ = ('fn',)

    def __init__(self, fn=None):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


probe_video_ref = _FnRef()
build_video_signature_ref = _FnRef()
