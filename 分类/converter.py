from __future__ import annotations

import shutil
from pathlib import Path


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
WINDOWS_HIDDEN_ATTRIBUTE = 0x2
WINDOWS_SYSTEM_ATTRIBUTE = 0x4
MAX_RENAME_ATTEMPTS = 1000
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
    folder = Path(path).resolve()
    if not folder.exists():
        raise FileNotFoundError(f'文件夹不存在: {folder}')
    if not folder.is_dir():
        raise NotADirectoryError(f'不是文件夹: {folder}')
    files = [item.resolve() for item in folder.iterdir() if is_sortable_file(item)]
    return sorted(files, key=lambda item: item.name.lower())


def get_category_for_file(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    for category in CATEGORY_ORDER:
        if suffix in CATEGORY_EXTENSIONS.get(category, set()):
            return category
    return '其他'


def normalize_selected_categories(selected_categories: list[str] | tuple[str, ...] | set[str] | None) -> tuple[str, ...]:
    if selected_categories is None:
        return CATEGORY_ORDER
    picked = [category for category in CATEGORY_ORDER if category in set(selected_categories)]
    return tuple(picked)


def summarize_folder(path: str | Path, selected_categories: list[str] | tuple[str, ...] | set[str] | None = None) -> dict[str, object]:
    folder = Path(path).resolve()
    files = scan_folder(folder)
    active_categories = normalize_selected_categories(selected_categories)
    counts = {category: 0 for category in CATEGORY_ORDER}
    selected_total = 0
    for file in files:
        category = get_category_for_file(file)
        counts[category] += 1
        if category in active_categories:
            selected_total += 1
    return {
        'folder': folder,
        'total_files': len(files),
        'category_counts': counts,
        'selected_categories': active_categories,
        'selected_total_files': selected_total,
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


def classify_files(path: str | Path, selected_categories: list[str] | tuple[str, ...] | set[str] | None = None) -> list[dict[str, object]]:
    folder = Path(path).resolve()
    files = scan_folder(folder)
    active_categories = set(normalize_selected_categories(selected_categories))
    results: list[dict[str, object]] = []
    for source in files:
        category = get_category_for_file(source)
        if category not in active_categories:
            continue
        target_dir = folder / category
        target_path = target_dir / source.name
        renamed = False
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = resolve_name_conflict(target_path)
            renamed = target_path.name != source.name
            shutil.move(str(source), str(target_path))
            results.append(
                {
                    'success': True,
                    'source': source,
                    'source_name': source.name,
                    'category': category,
                    'target_dir': target_dir,
                    'target_path': target_path,
                    'target_name': target_path.name,
                    'renamed': renamed,
                    'error': '',
                }
            )
        except Exception as exc:
            results.append(
                {
                    'success': False,
                    'source': source,
                    'source_name': source.name,
                    'category': category,
                    'target_dir': target_dir,
                    'target_path': target_path,
                    'target_name': target_path.name,
                    'renamed': renamed,
                    'error': str(exc),
                }
            )
    return results
