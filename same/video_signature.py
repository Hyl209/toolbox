"""Video similarity detection via frame comparison."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from same._common import (
    FFPROBE_PATH,
    FFMPEG_PATH,
    VIDEO_ASPECT_RATIO_TOLERANCE,
    VIDEO_DURATION_TOLERANCE_SECONDS,
    VIDEO_FRAME_HEIGHT,
    VIDEO_FRAME_WIDTH,
    VIDEO_MIN_FRAME_COUNT,
    VIDEO_SAMPLE_COUNT,
    VIDEO_SIMILARITY_THRESHOLD,
    MEDIA_COMMAND_TIMEOUT_SECONDS,
    _BoundedCache,
    _build_cache_key,
    _build_group,
    _map_parallel,
    _safe_float,
    probe_video_ref,
    build_video_signature_ref,
)


_VIDEO_METADATA_CACHE = _BoundedCache()
_VIDEO_SIGNATURE_CACHE = _BoundedCache()


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
    metadata = probe_video_ref(path)
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


def _build_video_similarity_groups(files: list[Path]) -> tuple[list[dict[str, object]], list[Path]]:
    fallback_files: list[Path] = []
    metadata_entries: list[dict[str, object]] = []
    metadata_results = _map_parallel(probe_video_ref, files)
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
    signature_results = _map_parallel(build_video_signature_ref, candidate_paths)
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


# Register function references for monkey-patching support
probe_video_ref.fn = _probe_video
build_video_signature_ref.fn = _build_video_signature
