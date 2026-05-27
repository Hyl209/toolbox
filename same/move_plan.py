"""Duplicate file moving logic."""
from __future__ import annotations

import shutil
from pathlib import Path

from toolbox_app.utils import resolve_name_conflict

from same._common import (
    DEFAULT_TARGET_DIR_NAME,
    _ensure_root,
    _normalize_target_dir_name,
)


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
