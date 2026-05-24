from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


DEFAULT_TARGET_DIR_NAME = '重复文件'
HASH_CHUNK_SIZE = 1024 * 1024


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


def _iter_recursive_files(root: Path, target_dir_name: str) -> list[Path]:
    files: list[Path] = []
    target_name = target_dir_name.casefold()
    for current in sorted(root.rglob('*')):
        if not current.is_file():
            continue
        relative_parts = [part.casefold() for part in current.relative_to(root).parts[:-1]]
        if target_name in relative_parts:
            continue
        files.append(current.resolve())
    return files


def scan_files(root: str | Path, recursive: bool, target_dir_name: str = DEFAULT_TARGET_DIR_NAME) -> list[Path]:
    folder = _ensure_root(root)
    target_dir_name = _normalize_target_dir_name(target_dir_name)
    if recursive:
        files = _iter_recursive_files(folder, target_dir_name)
    else:
        files = [item.resolve() for item in sorted(folder.iterdir(), key=lambda item: item.name.lower()) if item.is_file()]
    return files


def hash_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while True:
            chunk = handle.read(HASH_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _group_candidates(files: list[Path]) -> dict[tuple[str, int], list[Path]]:
    buckets: dict[tuple[str, int], list[Path]] = {}
    for file in files:
        stat = file.stat()
        key = (file.suffix.lower(), stat.st_size)
        buckets.setdefault(key, []).append(file)
    return buckets


def find_duplicate_groups(root: str | Path, recursive: bool, target_dir_name: str = DEFAULT_TARGET_DIR_NAME) -> dict[str, object]:
    folder = _ensure_root(root)
    target_dir_name = _normalize_target_dir_name(target_dir_name)
    files = scan_files(folder, recursive, target_dir_name)
    duplicate_groups: list[dict[str, object]] = []
    for (suffix, size), candidates in _group_candidates(files).items():
        if len(candidates) < 2:
            continue
        hashed: dict[str, list[Path]] = {}
        for file in candidates:
            hashed.setdefault(hash_file(file), []).append(file)
        for digest, grouped_files in hashed.items():
            if len(grouped_files) < 2:
                continue
            keeper = grouped_files[0]
            duplicates = grouped_files[1:]
            duplicate_groups.append(
                {
                    'suffix': suffix,
                    'size': size,
                    'hash': digest,
                    'keeper': keeper,
                    'duplicates': duplicates,
                    'files': grouped_files,
                }
            )
    duplicate_groups.sort(
        key=lambda item: str(Path(item['keeper']).relative_to(folder)).lower()
    )
    return {
        'root': folder,
        'recursive': bool(recursive),
        'target_dir_name': target_dir_name,
        'target_dir': folder / target_dir_name,
        'scanned_files': len(files),
        'duplicate_group_count': len(duplicate_groups),
        'duplicate_file_count': sum(len(group['duplicates']) for group in duplicate_groups),
        'groups': duplicate_groups,
    }


def resolve_name_conflict(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        renamed = candidate.with_name(f'{candidate.stem}({index}){candidate.suffix}')
        if not renamed.exists():
            return renamed
        index += 1


def _build_target_path(root: Path, source_path: Path, target_dir_name: str) -> Path:
    relative = source_path.relative_to(root)
    target_path = root / target_dir_name / relative
    if target_path.exists() and target_path.is_dir():
        target_path = target_path.with_name(f'{target_path.stem}({1}){target_path.suffix}')
    return resolve_name_conflict(target_path)


def _resolve_move_inputs(
    groups_or_result: list[dict[str, object]] | dict[str, object],
    target_dir_name: str | Path | None,
) -> tuple[list[dict[str, object]], str]:
    if isinstance(groups_or_result, dict):
        groups = groups_or_result.get('groups', [])
        if not isinstance(groups, list):
            raise TypeError('扫描结果中的 groups 格式不正确')
        result_target_dir_name = _normalize_target_dir_name(groups_or_result.get('target_dir_name', DEFAULT_TARGET_DIR_NAME))
        if target_dir_name is not None:
            normalized_target_dir_name = _normalize_target_dir_name(target_dir_name)
            if normalized_target_dir_name != result_target_dir_name:
                raise ValueError('move_duplicates 的 target_dir_name 与扫描结果不一致')
        return groups, result_target_dir_name
    if isinstance(groups_or_result, list):
        groups = groups_or_result
        normalized_target_dir_name = _normalize_target_dir_name(
            DEFAULT_TARGET_DIR_NAME if target_dir_name is None else target_dir_name
        )
        return groups, normalized_target_dir_name
    raise TypeError('groups_or_result 必须是扫描结果字典或重复组列表')


def move_duplicates(
    root: str | Path,
    groups_or_result: list[dict[str, object]] | dict[str, object],
    target_dir_name: str | Path | None = None,
) -> list[dict[str, object]]:
    folder = _ensure_root(root)
    groups, target_dir_name = _resolve_move_inputs(groups_or_result, target_dir_name)
    results: list[dict[str, object]] = []
    for group in groups:
        duplicates = group.get('duplicates', [])
        if not isinstance(duplicates, list):
            continue
        for source in duplicates:
            source_path = Path(source).resolve()
            target_path = _build_target_path(folder, source_path, target_dir_name)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            renamed = target_path.name != source_path.name
            try:
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
                        'target_path': target_path,
                        'renamed': renamed,
                        'error': str(exc),
                    }
                )
    return results
