from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import subprocess
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


def hash_file(path: str | Path) -> str:
    cache_key = _build_cache_key(path)
    cached = _FILE_HASH_CACHE.get(cache_key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b''):
            digest.update(chunk)
    hashed = digest.hexdigest()
    _FILE_HASH_CACHE[cache_key] = hashed
    return hashed


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


def _probe_video(path: Path) -> dict[str, object] | None:
    cache_key = _build_cache_key(path)
    if cache_key in _VIDEO_METADATA_CACHE:
        return _VIDEO_METADATA_CACHE[cache_key]
    if not FFPROBE_PATH:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    command = [
        FFPROBE_PATH,
        '-v',
        'error',
        '-select_streams',
        'v:0',
        '-show_entries',
        'stream=width,height,duration:format=duration',
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
    except OSError:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    except subprocess.TimeoutExpired:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    if completed.returncode != 0:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    try:
        payload = json.loads(completed.stdout or '{}')
    except json.JSONDecodeError:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    streams = payload.get('streams', [])
    stream = streams[0] if isinstance(streams, list) and streams else {}
    format_info = payload.get('format', {})
    duration = _safe_float(stream.get('duration')) or _safe_float(format_info.get('duration'))
    if duration is None:
        _VIDEO_METADATA_CACHE[cache_key] = None
        return None
    width = int(stream.get('width') or 0)
    height = int(stream.get('height') or 0)
    metadata = {
        'duration': duration,
        'width': width,
        'height': height,
        'aspect_ratio': (width / height) if width > 0 and height > 0 else 0.0,
    }
    _VIDEO_METADATA_CACHE[cache_key] = metadata
    return metadata


def _extract_video_frames(path: Path, duration: float) -> tuple[bytes, ...]:
    if not FFMPEG_PATH:
        return ()
    edge_margin = min(0.5, duration / 10)
    start = edge_margin
    end = max(duration - edge_margin, start + 0.1)
    span = max(end - start, 0.1)
    fps_value = VIDEO_SAMPLE_COUNT / span
    filter_text = (
        f'trim=start={start:.3f}:end={end:.3f},fps={fps_value:.6f},'
        f'scale={VIDEO_FRAME_WIDTH}:{VIDEO_FRAME_HEIGHT}:force_original_aspect_ratio=decrease,'
        f'pad={VIDEO_FRAME_WIDTH}:{VIDEO_FRAME_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,format=rgb24'
    )
    command = [
        FFMPEG_PATH,
        '-hide_banner',
        '-loglevel',
        'error',
        '-i',
        str(path),
        '-vf',
        filter_text,
        '-frames:v',
        str(VIDEO_SAMPLE_COUNT),
        '-f',
        'rawvideo',
        'pipe:1',
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=MEDIA_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except OSError:
        return ()
    except subprocess.TimeoutExpired:
        return ()
    if completed.returncode != 0:
        return ()
    frame_size = VIDEO_FRAME_WIDTH * VIDEO_FRAME_HEIGHT * 3
    if len(completed.stdout) < frame_size:
        return ()
    frame_count = len(completed.stdout) // frame_size
    frames: list[bytes] = []
    for index in range(frame_count):
        offset = index * frame_size
        frames.append(completed.stdout[offset:offset + frame_size])
    return tuple(frames)


def _build_video_signature(path: Path) -> dict[str, object] | None:
    cache_key = _build_cache_key(path)
    if cache_key in _VIDEO_SIGNATURE_CACHE:
        return _VIDEO_SIGNATURE_CACHE[cache_key]
    metadata = _probe_video(path)
    if metadata is None:
        _VIDEO_SIGNATURE_CACHE[cache_key] = None
        return None
    frames = _extract_video_frames(path, float(metadata['duration']))
    if len(frames) < VIDEO_MIN_FRAME_COUNT:
        _VIDEO_SIGNATURE_CACHE[cache_key] = None
        return None
    signature = {
        'path': path,
        'duration': float(metadata['duration']),
        'width': int(metadata.get('width', 0) or 0),
        'height': int(metadata.get('height', 0) or 0),
        'aspect_ratio': float(metadata.get('aspect_ratio', 0.0) or 0.0),
        'frames': frames,
    }
    _VIDEO_SIGNATURE_CACHE[cache_key] = signature
    return signature


def _frame_similarity(left: bytes, right: bytes) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    total = sum(abs(a - b) for a, b in zip(left, right))
    return 1.0 - total / (len(left) * 255)


def _video_similarity_score(left: dict[str, object], right: dict[str, object]) -> float:
    if abs(float(left['duration']) - float(right['duration'])) > VIDEO_DURATION_TOLERANCE_SECONDS:
        return 0.0
    left_ratio = float(left.get('aspect_ratio', 0.0) or 0.0)
    right_ratio = float(right.get('aspect_ratio', 0.0) or 0.0)
    if left_ratio > 0 and right_ratio > 0 and abs(left_ratio - right_ratio) > VIDEO_ASPECT_RATIO_TOLERANCE:
        return 0.0
    left_frames = left.get('frames', ())
    right_frames = right.get('frames', ())
    if not isinstance(left_frames, tuple) or not isinstance(right_frames, tuple):
        return 0.0
    shared_frame_count = min(len(left_frames), len(right_frames))
    if shared_frame_count < VIDEO_MIN_FRAME_COUNT:
        return 0.0
    scores = [
        _frame_similarity(left_frames[index], right_frames[index])
        for index in range(shared_frame_count)
    ]
    return sum(scores) / shared_frame_count


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


def _build_exact_duplicate_groups(files: list[Path]) -> list[dict[str, object]]:
    duplicate_groups: list[dict[str, object]] = []
    for candidates in _group_by_size(files).values():
        if len(candidates) < 2:
            continue
        hashed: dict[str, list[Path]] = {}
        for file in candidates:
            hashed.setdefault(hash_file(file), []).append(file)
        for digest, grouped_files in hashed.items():
            if len(grouped_files) < 2:
                continue
            duplicate_groups.append(_build_group(grouped_files[0], grouped_files, 'exact', digest=digest))
    return duplicate_groups


def _build_video_similarity_groups(files: list[Path]) -> tuple[list[dict[str, object]], list[Path]]:
    fallback_files: list[Path] = []
    metadata_entries: list[dict[str, object]] = []
    metadata_results = _map_parallel(_probe_video, files)
    for file, metadata in zip(files, metadata_results):
        if metadata is None:
            fallback_files.append(file)
            continue
        metadata_entries.append(
            {
                'path': file,
                'duration': float(metadata['duration']),
                'aspect_ratio': float(metadata.get('aspect_ratio', 0.0) or 0.0),
            }
        )
    if len(metadata_entries) < 2:
        return [], fallback_files

    metadata_entries.sort(key=lambda item: (float(item['duration']), str(item['path']).lower()))
    candidate_indexes: set[int] = set()
    for index, base in enumerate(metadata_entries):
        for candidate_index in range(index + 1, len(metadata_entries)):
            candidate = metadata_entries[candidate_index]
            if float(candidate['duration']) - float(base['duration']) > VIDEO_DURATION_TOLERANCE_SECONDS:
                break
            if abs(float(candidate['aspect_ratio']) - float(base['aspect_ratio'])) <= VIDEO_ASPECT_RATIO_TOLERANCE:
                candidate_indexes.add(index)
                candidate_indexes.add(candidate_index)

    if not candidate_indexes:
        return [], fallback_files

    candidate_paths = [metadata_entries[index]['path'] for index in sorted(candidate_indexes)]
    signature_results = _map_parallel(_build_video_signature, candidate_paths)
    signature_by_path = {
        path: signature
        for path, signature in zip(candidate_paths, signature_results)
        if signature is not None
    }

    signatures: list[dict[str, object]] = []
    for index, entry in enumerate(metadata_entries):
        if index not in candidate_indexes:
            continue
        signature = signature_by_path.get(entry['path'])
        if signature is None:
            fallback_files.append(entry['path'])
            continue
        signatures.append(signature)

    if len(signatures) < 2:
        return [], fallback_files

    used_indexes: set[int] = set()
    duplicate_groups: list[dict[str, object]] = []

    for index, base in enumerate(signatures):
        if index in used_indexes:
            continue
        matched_indexes: list[int] = []
        for candidate_index in range(index + 1, len(signatures)):
            if candidate_index in used_indexes:
                continue
            candidate = signatures[candidate_index]
            if float(candidate['duration']) - float(base['duration']) > VIDEO_DURATION_TOLERANCE_SECONDS:
                break
            similarity = _video_similarity_score(base, candidate)
            if similarity >= VIDEO_SIMILARITY_THRESHOLD:
                matched_indexes.append(candidate_index)
        if not matched_indexes:
            continue

        component_indexes = [index, *matched_indexes]
        grouped_files = [signatures[item]['path'] for item in component_indexes]
        grouped_files.sort(key=lambda item: str(item).lower())
        keeper = grouped_files[0]
        keeper_signature = next(item for item in signatures if item['path'] == keeper)
        similarities = [
            _video_similarity_score(keeper_signature, item)
            for item in signatures
            if item['path'] in grouped_files and item['path'] != keeper
        ]
        duplicate_groups.append(
            _build_group(
                keeper,
                grouped_files,
                'video_similarity',
                similarity=min(similarities) if similarities else 1.0,
            )
        )
        used_indexes.update(component_indexes)

    grouped_video_files = {
        file
        for group in duplicate_groups
        for file in group['files']
        if isinstance(group.get('files'), list)
    }
    for signature in signatures:
        path = signature['path']
        if path not in grouped_video_files:
            fallback_files.append(path)
    return duplicate_groups, fallback_files


def _split_video_and_other_files(files: list[Path]) -> tuple[list[Path], list[Path]]:
    video_files: list[Path] = []
    other_files: list[Path] = []
    for file in files:
        if _is_video_file(file):
            video_files.append(file)
        else:
            other_files.append(file)
    return video_files, other_files


def find_duplicate_groups(root: str | Path, recursive: bool, target_dir_name: str = DEFAULT_TARGET_DIR_NAME) -> dict[str, object]:
    folder = _ensure_root(root)
    normalized_target_dir_name = _normalize_target_dir_name(target_dir_name)
    files = _scan_files_from_root(folder, recursive, normalized_target_dir_name)
    video_files, other_files = _split_video_and_other_files(files)
    video_groups, fallback_video_files = _build_video_similarity_groups(video_files)
    duplicate_groups = _build_exact_duplicate_groups(other_files + fallback_video_files) + video_groups
    duplicate_groups.sort(key=lambda item: str(Path(item['keeper']).relative_to(folder)).lower())
    duplicate_file_count = sum(len(group['duplicates']) for group in duplicate_groups)
    return {
        'root': folder,
        'recursive': bool(recursive),
        'target_dir_name': normalized_target_dir_name,
        'target_dir': folder / normalized_target_dir_name,
        'scanned_files': len(files),
        'duplicate_group_count': len(duplicate_groups),
        'duplicate_file_count': duplicate_file_count,
        'groups': duplicate_groups,
    }



def _build_target_path(root: Path, source_path: Path, target_dir_name: str) -> Path:
    relative = source_path.relative_to(root)
    target_path = root / target_dir_name / relative
    if target_path.exists() and target_path.is_dir():
        target_path = target_path.with_name(f'{target_path.stem}(1){target_path.suffix}')
    return resolve_name_conflict(target_path)


def _resolve_move_inputs(
    groups_or_result: list[dict[str, object]] | dict[str, object],
    target_dir_name: str | Path | None,
) -> tuple[list[dict[str, object]], str]:
    if isinstance(groups_or_result, dict):
        groups = groups_or_result.get('groups', [])
        if not isinstance(groups, list):
            raise TypeError("scan result 'groups' must be a list")
        result_target_dir_name = _normalize_target_dir_name(
            groups_or_result.get('target_dir_name', DEFAULT_TARGET_DIR_NAME)
        )
        if target_dir_name is not None:
            normalized_target_dir_name = _normalize_target_dir_name(target_dir_name)
            if normalized_target_dir_name != result_target_dir_name:
                raise ValueError('move_duplicates target_dir_name does not match scan result')
        return groups, result_target_dir_name

    if isinstance(groups_or_result, list):
        normalized_target_dir_name = _normalize_target_dir_name(
            DEFAULT_TARGET_DIR_NAME if target_dir_name is None else target_dir_name
        )
        return groups_or_result, normalized_target_dir_name

    raise TypeError('groups_or_result must be a scan result dict or duplicate group list')


def move_duplicates(
    root: str | Path,
    groups_or_result: list[dict[str, object]] | dict[str, object],
    target_dir_name: str | Path | None = None,
) -> list[dict[str, object]]:
    folder = _ensure_root(root)
    groups, normalized_target_dir_name = _resolve_move_inputs(groups_or_result, target_dir_name)
    results: list[dict[str, object]] = []

    for group in groups:
        duplicates = group.get('duplicates', [])
        if not isinstance(duplicates, list):
            continue

        for source in duplicates:
            source_path = Path(source).resolve()
            try:
                target_path = _build_target_path(folder, source_path, normalized_target_dir_name)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                renamed = target_path.name != source_path.name
                shutil.move(str(source_path), str(target_path))
                results.append(
                    {
                        'success': True,
                        'source': source_path,
                        'target_path': target_path,
                        'renamed': renamed,
                        'error': '',
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        'success': False,
                        'source': source_path,
                        'target_path': None,
                        'renamed': False,
                        'error': str(exc),
                    }
                )

    return results
