from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional, Callable
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils

logger = get_logger(__name__)


class FileService:
    """文件服务"""

    def __init__(self):
        pass

    def organize_files(self, source_dir: str | Path, target_dir: str | Path,
                       organize_by: str = "extension") -> dict[str, list[Path]]:
        """整理文件"""
        try:
            source_dir = Path(source_dir)
            target_dir = Path(target_dir)

            if not source_dir.exists():
                raise ServiceError(f"源目录不存在: {source_dir}", "FileService")

            file_utils.ensure_dir(target_dir)
            organized_files: dict[str, list[Path]] = {}

            for file_path in source_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # 根据整理方式确定目标目录
                if organize_by == "extension":
                    category = self._get_extension_category(file_path.suffix)
                elif organize_by == "date":
                    category = self._get_date_category(file_path)
                elif organize_by == "size":
                    category = self._get_size_category(file_path)
                else:
                    category = "其他"

                # 创建分类目录
                category_dir = target_dir / category
                file_utils.ensure_dir(category_dir)

                # 移动文件
                target_file = category_dir / file_path.name
                target_file = file_utils.get_unique_filename(target_file)

                shutil.move(str(file_path), str(target_file))

                if category not in organized_files:
                    organized_files[category] = []
                organized_files[category].append(target_file)

                logger.debug(f"文件整理: {file_path} -> {target_file}")

            logger.info(f"文件整理完成: {len(organized_files)} 个分类")
            return organized_files

        except Exception as e:
            logger.error(f"文件整理失败: {e}")
            raise ServiceError(f"文件整理失败: {e}", "FileService")

    def _get_extension_category(self, extension: str) -> str:
        """根据扩展名获取分类"""
        extension = extension.lower()
        categories = {
            '图片': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.tif', '.tiff', '.svg', '.ico'},
            '视频': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
            '音频': {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma', '.ncm'},
            '文档': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv'},
            '压缩包': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
            '程序': {'.exe', '.msi', '.bat', '.cmd', '.ps1', '.py'}
        }

        for category, extensions in categories.items():
            if extension in extensions:
                return category
        return "其他"

    def _get_date_category(self, file_path: Path) -> str:
        """根据日期获取分类"""
        import time
        mtime = file_path.stat().st_mtime
        date = time.localtime(mtime)
        return f"{date.tm_year}-{date.tm_mon:02d}"

    def _get_size_category(self, file_path: Path) -> str:
        """根据大小获取分类"""
        size = file_path.stat().st_size
        if size < 1024 * 1024:  # < 1MB
            return "小文件"
        elif size < 100 * 1024 * 1024:  # < 100MB
            return "中等文件"
        else:
            return "大文件"

    def find_duplicates(self, directory: str | Path) -> dict[str, list[Path]]:
        """查找重复文件"""
        try:
            directory = Path(directory)
            if not directory.exists():
                raise ServiceError(f"目录不存在: {directory}", "FileService")

            # 使用文件大小和哈希值查找重复
            size_map: dict[int, list[Path]] = {}
            duplicates: dict[str, list[Path]] = {}

            # 第一步：按大小分组
            for file_path in directory.rglob("*"):
                if not file_path.is_file():
                    continue
                size = file_path.stat().st_size
                if size not in size_map:
                    size_map[size] = []
                size_map[size].append(file_path)

            # 第二步：对相同大小的文件计算哈希值
            for size, files in size_map.items():
                if len(files) < 2:
                    continue

                hash_map: dict[str, list[Path]] = {}
                for file_path in files:
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash not in hash_map:
                        hash_map[file_hash] = []
                    hash_map[file_hash].append(file_path)

                # 找出重复文件
                for file_hash, duplicate_files in hash_map.items():
                    if len(duplicate_files) > 1:
                        duplicates[file_hash] = duplicate_files

            logger.info(f"查找重复文件完成: {len(duplicates)} 组")
            return duplicates

        except Exception as e:
            logger.error(f"查找重复文件失败: {e}")
            raise ServiceError(f"查找重复文件失败: {e}", "FileService")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def rename_batch(self, directory: str | Path, pattern: str,
                     replacement: str = "", callback: Callable[[Path, Path], None] = None) -> list[Path]:
        """批量重命名"""
        try:
            directory = Path(directory)
            if not directory.exists():
                raise ServiceError(f"目录不存在: {directory}", "FileService")

            renamed_files = []
            for file_path in directory.iterdir():
                if not file_path.is_file():
                    continue

                new_name = file_path.name
                if pattern in new_name:
                    new_name = new_name.replace(pattern, replacement)
                    new_path = file_path.parent / new_name

                    if new_path.exists():
                        new_path = file_utils.get_unique_filename(new_path)

                    file_path.rename(new_path)
                    renamed_files.append(new_path)

                    if callback:
                        callback(file_path, new_path)

                    logger.debug(f"重命名: {file_path} -> {new_path}")

            logger.info(f"批量重命名完成: {len(renamed_files)} 个文件")
            return renamed_files

        except Exception as e:
            logger.error(f"批量重命名失败: {e}")
            raise ServiceError(f"批量重命名失败: {e}", "FileService")

    def get_directory_stats(self, directory: str | Path) -> dict:
        """获取目录统计信息"""
        try:
            directory = Path(directory)
            if not directory.exists():
                raise ServiceError(f"目录不存在: {directory}", "FileService")

            stats = {
                'total_files': 0,
                'total_dirs': 0,
                'total_size': 0,
                'by_extension': {},
                'by_category': {}
            }

            for item in directory.rglob("*"):
                if item.is_file():
                    stats['total_files'] += 1
                    size = item.stat().st_size
                    stats['total_size'] += size

                    # 按扩展名统计
                    ext = item.suffix.lower()
                    if ext not in stats['by_extension']:
                        stats['by_extension'][ext] = {'count': 0, 'size': 0}
                    stats['by_extension'][ext]['count'] += 1
                    stats['by_extension'][ext]['size'] += size

                    # 按分类统计
                    category = self._get_extension_category(ext)
                    if category not in stats['by_category']:
                        stats['by_category'][category] = {'count': 0, 'size': 0}
                    stats['by_category'][category]['count'] += 1
                    stats['by_category'][category]['size'] += size

                elif item.is_dir():
                    stats['total_dirs'] += 1

            return stats

        except Exception as e:
            logger.error(f"获取目录统计失败: {e}")
            raise ServiceError(f"获取目录统计失败: {e}", "FileService")


# 全局文件服务实例
_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    """获取全局文件服务实例"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
