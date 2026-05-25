from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image


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
RESOLUTION_CATEGORY_ORDER = ('图片', '视频')
OTHER_CATEGORY = CATEGORY_ORDER[-1]
IMAGE_CATEGORY = CATEGORY_ORDER[0]
VIDEO_CATEGORY = CATEGORY_ORDER[1]
MODE_CATEGORY = 'category'
MODE_RESOLUTION = 'resolution'
MODE_ORDER = (MODE_CATEGORY, MODE_RESOLUTION)
FFPROBE_PATH = shutil.which('ffprobe')
MEDIA_COMMAND_TIMEOUT_SECONDS = 20
WINDOWS_HIDDEN_ATTRIBUTE = 0x2
WINDOWS_SYSTEM_ATTRIBUTE = 0x4
MAX_RENAME_ATTEMPTS = 1000
DEFAULT_SKIPPED_NAMES = {'desktop.ini', 'thumbs.db'}
RESOLUTION_BUCKET_RULES: tuple[tuple[int, str], ...] = (
    (854, '480p及以下'),
    (1280, '720p'),
    (1920, '1080p'),
    (2560, '2K'),
    (3840, '4K'),
)
RESOLUTION_BUCKET_ORDER = tuple(label for _, label in RESOLUTION_BUCKET_RULES) + ('8K及以上',)
EXTENSION_TO_CATEGORY = {
    extension: category
    for category, extensions in CATEGORY_EXTENSIONS.items()
    for extension in extensions
}
_VIDEO_RESOLUTION_CACHE: dict[tuple[str, int, int], tuple[int, int] | None] = {}
_IMAGE_RESOLUTION_CACHE: dict[tuple[str, int, int], tuple[int, int] | None] = {}


def _resolve_folder(path: str | Path) -> Path:
    folder = Path(path).resolve()
    if not folder.exists():
        raise FileNotFoundError(f'文件夹不存在: {folder}')
    if not folder.is_dir():
        raise NotADirectoryError(f'不是文件夹: {folder}')
    return folder


def _scan_folder(folder: Path) -> list[Path]:
    return sorted((item.resolve() for item in folder.iterdir() if is_sortable_file(item)), key=lambda item: item.name.lower())


def _normalize_files(files: Iterable[str | Path]) -> list[Path]:
    return [Path(file).resolve() for file in files]


def _build_cache_key(path: str | Path) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return str(resolved).lower(), stat.st_size, stat.st_mtime_ns


def normalize_mode(mode: str | None) -> str:
    return MODE_RESOLUTION if mode == MODE_RESOLUTION else MODE_CATEGORY


def is_hidden_or_system_file(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.name.startswith('.') or candidate.name.lower() in DEFAULT_SKIPPED_NAMES:
        return True
    try:
        attributes = candidate.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & (WINDOWS_HIDDEN_ATTRIBUTE | WINDOWS_SYSTEM_ATTRIBUTE))


def is_sortable_file(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.is_symlink():
        return False
    if not candidate.is_file():
        return False
    if is_hidden_or_system_file(candidate):
        return False
    return True


def scan_folder(path: str | Path) -> list[Path]:
    return _scan_folder(_resolve_folder(path))


def get_category_for_file(path: str | Path) -> str:
    return EXTENSION_TO_CATEGORY.get(Path(path).suffix.lower(), OTHER_CATEGORY)


def normalize_selected_categories(
    selected_categories: list[str] | tuple[str, ...] | set[str] | None,
    mode: str = MODE_CATEGORY,
) -> tuple[str, ...]:
    normalized_mode = normalize_mode(mode)
    category_order = CATEGORY_ORDER if normalized_mode == MODE_CATEGORY else RESOLUTION_CATEGORY_ORDER
    if selected_categories is None:
        return category_order
    selected_set = set(selected_categories)
    return tuple(category for category in category_order if category in selected_set)


def get_resolution_bucket(width: int, height: int) -> str:
    longer_edge = max(width, height)
    for max_edge, label in RESOLUTION_BUCKET_RULES:
        if longer_edge <= max_edge:
            return label
    return RESOLUTION_BUCKET_ORDER[-1]


def _safe_positive_int(value: object) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def _read_image_resolution(path: Path) -> tuple[int, int] | None:
    cache_key = _build_cache_key(path)
    if cache_key in _IMAGE_RESOLUTION_CACHE:
        return _IMAGE_RESOLUTION_CACHE[cache_key]
    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception:
        _IMAGE_RESOLUTION_CACHE[cache_key] = None
        return None
    if width <= 0 or height <= 0:
        _IMAGE_RESOLUTION_CACHE[cache_key] = None
        return None
    resolution = int(width), int(height)
    _IMAGE_RESOLUTION_CACHE[cache_key] = resolution
    return resolution


def _read_video_resolution(path: Path) -> tuple[int, int] | None:
    cache_key = _build_cache_key(path)
    if cache_key in _VIDEO_RESOLUTION_CACHE:
        return _VIDEO_RESOLUTION_CACHE[cache_key]
    if not FFPROBE_PATH:
        _VIDEO_RESOLUTION_CACHE[cache_key] = None
        return None
    command = [
        FFPROBE_PATH,
        '-v',
        'error',
        '-select_streams',
        'v:0',
        '-show_entries',
        'stream=width,height',
        '-of',
        'json',
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=MEDIA_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        _VIDEO_RESOLUTION_CACHE[cache_key] = None
        return None
    if completed.returncode != 0:
        _VIDEO_RESOLUTION_CACHE[cache_key] = None
        return None
    try:
        payload = json.loads(completed.stdout or '{}')
    except json.JSONDecodeError:
        _VIDEO_RESOLUTION_CACHE[cache_key] = None
        return None
    streams = payload.get('streams', [])
    stream = streams[0] if isinstance(streams, list) and streams else {}
    width = _safe_positive_int(stream.get('width'))
    height = _safe_positive_int(stream.get('height'))
    if width <= 0 or height <= 0:
        _VIDEO_RESOLUTION_CACHE[cache_key] = None
        return None
    resolution = width, height
    _VIDEO_RESOLUTION_CACHE[cache_key] = resolution
    return resolution


def get_media_resolution(path: str | Path, category: str | None = None) -> tuple[int, int] | None:
    resolved = Path(path).resolve()
    resolved_category = category or get_category_for_file(resolved)
    if resolved_category == IMAGE_CATEGORY:
        return _read_image_resolution(resolved)
    if resolved_category == VIDEO_CATEGORY:
        return _read_video_resolution(resolved)
    return None


def summarize_folder(
    path: str | Path,
    selected_categories: list[str] | tuple[str, ...] | set[str] | None = None,
    mode: str = MODE_CATEGORY,
) -> dict[str, object]:
    folder = _resolve_folder(path)
    files = _scan_folder(folder)
    normalized_mode = normalize_mode(mode)
    active_categories = normalize_selected_categories(selected_categories, normalized_mode)
    counts = {category: 0 for category in CATEGORY_ORDER}
    active_category_set = set(active_categories)
    selected_total = 0
    media_total = 0
    detected_media_total = 0
    unresolved_total = 0
    resolution_bucket_counts = {bucket: 0 for bucket in RESOLUTION_BUCKET_ORDER}

    for file in files:
        category = get_category_for_file(file)
        counts[category] += 1
        if normalized_mode == MODE_CATEGORY:
            if category in active_category_set:
                selected_total += 1
            continue
        if category not in RESOLUTION_CATEGORY_ORDER:
            continue
        media_total += 1
        resolution = get_media_resolution(file, category)
        if resolution is None:
            if category in active_category_set:
                unresolved_total += 1
            continue
        detected_media_total += 1
        if category not in active_category_set:
            continue
        resolution_bucket_counts[get_resolution_bucket(*resolution)] += 1
        selected_total += 1

    return {
        'mode': normalized_mode,
        'folder': folder,
        'total_files': len(files),
        'category_counts': counts,
        'selected_categories': active_categories,
        'selected_total_files': selected_total,
        'media_total_files': media_total,
        'detected_media_files': detected_media_total,
        'unresolved_media_files': unresolved_total,
        'resolution_bucket_counts': resolution_bucket_counts,
        'files': files,
    }


def resolve_name_conflict(path: str | Path, max_attempts: int = MAX_RENAME_ATTEMPTS) -> Path:
    candidate = Path(path)
    if not candidate.exists():
        return candidate
    for index in range(1, max_attempts + 1):
        renamed = candidate.with_name(f'{candidate.stem}({index}){candidate.suffix}')
        if not renamed.exists():
            return renamed
    raise RuntimeError(f'重名文件过多，超过最大尝试次数: {max_attempts}')


def _build_result(
    source: Path,
    category: str,
    target_dir: Path | None,
    target_path: Path | None,
    group_label: str,
    success: bool,
    renamed: bool,
    error: str = '',
    skip_reason: str = '',
    resolution: tuple[int, int] | None = None,
) -> dict[str, object]:
    return {
        'success': success,
        'source': source,
        'source_name': source.name,
        'category': category,
        'target_dir': target_dir,
        'target_path': target_path,
        'target_name': target_path.name if target_path is not None else '',
        'group_label': group_label,
        'renamed': renamed,
        'error': error,
        'skip_reason': skip_reason,
        'resolution': resolution,
    }


def classify_files(
    path: str | Path,
    selected_categories: list[str] | tuple[str, ...] | set[str] | None = None,
    files: Iterable[str | Path] | None = None,
    mode: str = MODE_CATEGORY,
) -> list[dict[str, object]]:
    folder = _resolve_folder(path)
    source_files = _scan_folder(folder) if files is None else _normalize_files(files)
    normalized_mode = normalize_mode(mode)
    active_categories = set(normalize_selected_categories(selected_categories, normalized_mode))
    results: list[dict[str, object]] = []

    for source in source_files:
        category = get_category_for_file(source)
        if category not in active_categories:
            continue

        resolution: tuple[int, int] | None = None
        group_label = category
        if normalized_mode == MODE_RESOLUTION:
            if category not in RESOLUTION_CATEGORY_ORDER:
                continue
            resolution = get_media_resolution(source, category)
            if resolution is None:
                results.append(
                    _build_result(
                        source,
                        category,
                        None,
                        None,
                        '',
                        False,
                        False,
                        error='无法读取分辨率',
                        skip_reason='无法读取分辨率',
                    )
                )
                continue
            group_label = get_resolution_bucket(*resolution)

        target_dir = folder / group_label
        target_path = target_dir / source.name
        renamed = False
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = resolve_name_conflict(target_path)
            renamed = target_path.name != source.name
            shutil.move(str(source), str(target_path))
            results.append(
                _build_result(
                    source,
                    category,
                    target_dir,
                    target_path,
                    group_label,
                    True,
                    renamed,
                    resolution=resolution,
                )
            )
        except Exception as exc:
            results.append(
                _build_result(
                    source,
                    category,
                    target_dir,
                    target_path,
                    group_label,
                    False,
                    renamed,
                    error=str(exc),
                    resolution=resolution,
                )
            )
    return results
