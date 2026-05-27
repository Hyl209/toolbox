"""Common utilities for tool tabs — eliminates repeated patterns across all tab files."""
from __future__ import annotations

from pathlib import Path
from typing import Callable


def collect_inputs_by_suffix(paths: list[str], suffixes: set[str],
                             recursive: bool = True) -> list[Path]:
    """Collect files from paths, deduplicating by resolved path.

    Args:
        paths: List of file/directory paths (as strings).
        suffixes: Accepted file extensions (lowercase, with dot), e.g. {'.mp4', '.avi'}.
        recursive: Whether to recurse into directories.
    """
    unique: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file() and path.suffix.lower() in suffixes:
            unique[path] = None
        elif path.is_dir():
            items = path.rglob('*') if recursive else path.iterdir()
            for item in sorted(items):
                if item.is_file() and item.suffix.lower() in suffixes:
                    unique[item.resolve()] = None
    return sorted(unique.keys())


def format_drop_summary(files: list[Path], label: str = '文件',
                        max_preview: int = 6) -> str:
    """Format a drop-zone summary string.

    Args:
        files: List of collected file paths.
        label: Noun for the file type (e.g. '视频', '图片', '文件').
        max_preview: Max number of filenames to show.
    """
    if not files:
        return f'拖入 {label}'
    names = [p.stem for p in files[:max_preview]]
    summary = '\n'.join(names)
    if len(files) > max_preview:
        summary += f'\n... 另有 {len(files) - max_preview} 个{label}'
    return f'已添加 {len(files)} 个{label}\n\n{summary}'


def merge_new_files(existing: list[Path], new_files: list[Path]) -> list[Path]:
    """Merge new files into existing list, skipping duplicates. Returns newly added files."""
    existing_set = {p.resolve() for p in existing}
    added: list[Path] = []
    for f in new_files:
        resolved = f.resolve()
        if resolved not in existing_set:
            existing.append(resolved)
            existing_set.add(resolved)
            added.append(resolved)
    return added
