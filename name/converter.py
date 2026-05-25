from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import uuid


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
GROUP_MODE_SUFFIX = 'suffix'
GROUP_MODE_TYPE = 'type'
GROUP_MODE_ALL = 'all'
SORT_MODE_NAME = 'name'
SORT_MODE_MTIME = 'mtime'
SORT_MODE_SIZE = 'size'
ORDER_ASC = 'asc'
ORDER_DESC = 'desc'
WINDOWS_HIDDEN_ATTRIBUTE = 0x2
WINDOWS_SYSTEM_ATTRIBUTE = 0x4
DEFAULT_SKIPPED_NAMES = {'desktop.ini', 'thumbs.db'}


@dataclass(frozen=True)
class RenamePlanItem:
    source: Path
    group_key: str
    order_value: object
    target_name: str


def is_hidden_or_system_file(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.name.startswith('.') or candidate.name.lower() in DEFAULT_SKIPPED_NAMES:
        return True
    try:
        attributes = candidate.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & (WINDOWS_HIDDEN_ATTRIBUTE | WINDOWS_SYSTEM_ATTRIBUTE))


def is_renameable_file(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.is_symlink():
        return False
    if not candidate.is_file():
        return False
    if is_hidden_or_system_file(candidate):
        return False
    return True


def scan_folder(path: str | Path) -> list[Path]:
    folder = Path(path).resolve()
    if not folder.exists():
        raise FileNotFoundError(f'文件夹不存在: {folder}')
    if not folder.is_dir():
        raise NotADirectoryError(f'不是文件夹: {folder}')
    files = [item.resolve() for item in folder.iterdir() if is_renameable_file(item)]
    return sorted(files, key=lambda item: item.name.casefold())


def normalize_prefix(prefix: str) -> str:
    cleaned = prefix.strip()
    if not cleaned:
        raise ValueError('请输入命名前缀')
    invalid_chars = '<>:"/\\|?*'
    if any(char in invalid_chars for char in cleaned):
        raise ValueError('命名前缀不能包含 \\ / : * ? " < > |')
    normalized = cleaned.rstrip(' .')
    if not normalized:
        raise ValueError('请输入有效的命名前缀')
    return normalized


def normalize_group_mode(group_mode: str) -> str:
    cleaned = (group_mode or '').strip().lower()
    if cleaned in {GROUP_MODE_SUFFIX, GROUP_MODE_TYPE, GROUP_MODE_ALL}:
        return cleaned
    raise ValueError(f'不支持的分组方式: {group_mode}')


def normalize_sort_mode(sort_mode: str) -> str:
    cleaned = (sort_mode or '').strip().lower()
    if cleaned in {SORT_MODE_NAME, SORT_MODE_MTIME, SORT_MODE_SIZE}:
        return cleaned
    raise ValueError(f'不支持的排序方式: {sort_mode}')


def normalize_sort_order(sort_order: str) -> str:
    cleaned = (sort_order or '').strip().lower()
    if cleaned in {ORDER_ASC, ORDER_DESC}:
        return cleaned
    raise ValueError(f'不支持的排序方向: {sort_order}')


def get_file_category(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    for category in CATEGORY_ORDER:
        if suffix in CATEGORY_EXTENSIONS.get(category, set()):
            return category
    return '其他'


def get_group_key(path: str | Path, group_mode: str) -> str:
    normalized_mode = normalize_group_mode(group_mode)
    file_path = Path(path)
    if normalized_mode == GROUP_MODE_SUFFIX:
        return file_path.suffix.lower() or '[无后缀]'
    if normalized_mode == GROUP_MODE_TYPE:
        return get_file_category(file_path)
    return '全部文件'


def _group_sort_key(group_key: str, group_mode: str) -> tuple[int, str]:
    if group_mode == GROUP_MODE_TYPE:
        try:
            return (CATEGORY_ORDER.index(group_key), group_key)
        except ValueError:
            return (len(CATEGORY_ORDER), group_key)
    return (0, group_key)


def _get_sort_value(path: Path, sort_mode: str) -> object:
    if sort_mode == SORT_MODE_MTIME:
        return path.stat().st_mtime
    if sort_mode == SORT_MODE_SIZE:
        return path.stat().st_size
    return path.name.casefold()


def _build_sort_key(path: Path, sort_mode: str) -> tuple[object, str]:
    return (_get_sort_value(path, sort_mode), path.name.casefold())


def _group_files(files: list[Path], group_mode: str, sort_mode: str, sort_order: str) -> list[tuple[str, list[Path]]]:
    grouped: dict[str, list[Path]] = {}
    for file in files:
        grouped.setdefault(get_group_key(file, group_mode), []).append(file)
    reverse = normalize_sort_order(sort_order) == ORDER_DESC
    grouped_items: list[tuple[str, list[Path]]] = []
    for group_key, group_files in grouped.items():
        ordered_files = sorted(group_files, key=lambda item: _build_sort_key(item, sort_mode), reverse=reverse)
        grouped_items.append((group_key, ordered_files))
    grouped_items.sort(key=lambda item: _group_sort_key(item[0], group_mode))
    return grouped_items


def build_rename_plan(
    path: str | Path,
    prefix: str,
    group_mode: str,
    sort_mode: str,
    sort_order: str,
) -> list[dict[str, object]]:
    folder = Path(path).resolve()
    files = scan_folder(folder)
    normalized_prefix = normalize_prefix(prefix)
    normalized_group_mode = normalize_group_mode(group_mode)
    normalized_sort_mode = normalize_sort_mode(sort_mode)
    normalized_sort_order = normalize_sort_order(sort_order)
    grouped_files = _group_files(files, normalized_group_mode, normalized_sort_mode, normalized_sort_order)
    plan: list[dict[str, object]] = []
    for group_key, ordered_files in grouped_files:
        width = max(3, len(str(len(ordered_files))))
        for index, source in enumerate(ordered_files, start=1):
            number = f'{index:0{width}d}'
            target_name = f'{normalized_prefix}_{number}{source.suffix.lower()}'
            plan.append(
                {
                    'source': source,
                    'source_name': source.name,
                    'group_key': group_key,
                    'sort_value': _get_sort_value(source, normalized_sort_mode),
                    'target_name': target_name,
                }
            )
    return plan


def summarize_folder(
    path: str | Path,
    prefix: str,
    group_mode: str,
    sort_mode: str,
    sort_order: str,
) -> dict[str, object]:
    folder = Path(path).resolve()
    files = scan_folder(folder)
    plan = build_rename_plan(folder, prefix, group_mode, sort_mode, sort_order)
    group_counts: dict[str, int] = {}
    for item in plan:
        group_key = str(item['group_key'])
        group_counts[group_key] = group_counts.get(group_key, 0) + 1
    return {
        'folder': folder,
        'files': files,
        'total_files': len(files),
        'group_mode': normalize_group_mode(group_mode),
        'sort_mode': normalize_sort_mode(sort_mode),
        'sort_order': normalize_sort_order(sort_order),
        'prefix': normalize_prefix(prefix),
        'group_counts': group_counts,
        'plan': plan,
    }


def _make_temp_path(source: Path) -> Path:
    while True:
        candidate = source.with_name(f'.hyl_rename_tmp_{uuid.uuid4().hex}{source.suffix}')
        if not candidate.exists():
            return candidate


def _ensure_no_external_conflicts(folder: Path, plan: list[dict[str, object]]) -> None:
    sources = {Path(item['source']).resolve() for item in plan}
    for item in plan:
        target_path = folder / str(item['target_name'])
        if target_path.exists() and target_path.resolve() not in sources:
            raise FileExistsError(f'目标文件已存在: {target_path.name}')


def rename_files(
    path: str | Path,
    prefix: str,
    group_mode: str,
    sort_mode: str,
    sort_order: str,
) -> list[dict[str, object]]:
    folder = Path(path).resolve()
    plan = build_rename_plan(folder, prefix, group_mode, sort_mode, sort_order)
    _ensure_no_external_conflicts(folder, plan)

    staged: list[tuple[Path, Path, Path]] = []
    results: list[dict[str, object]] = []
    try:
        for item in plan:
            source = Path(item['source']).resolve()
            target_path = folder / str(item['target_name'])
            temp_path = _make_temp_path(source)
            source.rename(temp_path)
            staged.append((source, temp_path, target_path))
        for source, temp_path, target_path in staged:
            temp_path.rename(target_path)
            results.append(
                {
                    'success': True,
                    'source': source,
                    'source_name': source.name,
                    'target_path': target_path,
                    'target_name': target_path.name,
                    'group_key': get_group_key(source, group_mode),
                    'renamed': source.name != target_path.name,
                    'error': '',
                }
            )
    except Exception as exc:
        for source, temp_path, target_path in reversed(staged):
            if temp_path.exists():
                try:
                    temp_path.rename(source)
                except OSError:
                    pass
            elif target_path.exists() and not source.exists():
                try:
                    target_path.rename(source)
                except OSError:
                    pass
        raise RuntimeError(str(exc)) from exc
    return results
