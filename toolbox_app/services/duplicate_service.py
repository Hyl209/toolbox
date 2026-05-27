"""重复文件检测服务 — 包装 same/converter.py"""
from __future__ import annotations

from pathlib import Path
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)


class DuplicateService:
    """重复文件检测服务"""

    def __init__(self):
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from ..loaders import load_module_once
            converter_path = Path(__file__).resolve().parent.parent.parent / 'same' / 'converter.py'
            self._converter = load_module_once('same_converter_module', converter_path)
        return self._converter

    def detect(self, folder_path: str | Path, recursive: bool = True) -> list[list[Path]]:
        """检测重复文件，返回重复文件组列表"""
        try:
            conv = self._get_converter()
            return conv.find_duplicate_groups(str(folder_path), recursive)
        except Exception as e:
            raise ServiceError(f'重复检测失败: {e}', 'DuplicateService')

    def compute_hash(self, file_path: str | Path) -> str:
        """计算文件哈希值"""
        try:
            conv = self._get_converter()
            return conv.compute_file_hash(str(file_path))
        except Exception as e:
            raise ServiceError(f'哈希计算失败: {e}', 'DuplicateService')

    def move_duplicates(self, groups: list[list[Path]], target_dir: str | Path,
                        keep_oldest: bool = True) -> list[tuple[Path, list[Path]]]:
        """移动重复文件到目标目录，返回 (保留文件, 移动文件列表)"""
        try:
            conv = self._get_converter()
            results = []
            for group in groups:
                if len(group) < 2:
                    continue
                sorted_group = sorted(group, key=lambda p: p.stat().st_mtime)
                keeper = sorted_group[0] if keep_oldest else sorted_group[-1]
                to_move = [f for f in group if f != keeper]
                moved = []
                for f in to_move:
                    dest = Path(target_dir) / f.name
                    if dest.exists():
                        from ..core.file_utils import file_utils
                        dest = file_utils.get_unique_filename(dest)
                    f.rename(dest)
                    moved.append(dest)
                results.append((keeper, moved))
            return results
        except Exception as e:
            raise ServiceError(f'移动重复文件失败: {e}', 'DuplicateService')
