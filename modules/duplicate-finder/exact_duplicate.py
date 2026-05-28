"""Exact hash-based duplicate detection."""
from __future__ import annotations

import hashlib
from pathlib import Path

from ._common import (
    HASH_CHUNK_SIZE,
    _BoundedCache,
    _build_cache_key,
    _build_group,
    _group_by_size,
)


_FILE_HASH_CACHE = _BoundedCache()


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


def find_duplicate_groups(root: str | Path, recursive: bool, target_dir_name: str = '重复文件') -> dict[str, object]:
    from ._common import (
        DEFAULT_TARGET_DIR_NAME,
        _ensure_root,
        _normalize_target_dir_name,
        _scan_files_from_root,
        _split_video_and_other_files,
    )
    from .video_signature import _build_video_similarity_groups

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
