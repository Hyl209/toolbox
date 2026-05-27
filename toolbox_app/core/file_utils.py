from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional
from .logger import get_logger
from .exceptions import ResourceError

logger = get_logger(__name__)


class FileUtils:
    """文件工具类"""

    @staticmethod
    def ensure_dir(path: str | Path) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def safe_delete(path: str | Path) -> bool:
        """安全删除文件或目录"""
        try:
            path = Path(path)
            if path.is_file():
                path.unlink()
                logger.debug(f"删除文件: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.debug(f"删除目录: {path}")
            return True
        except Exception as e:
            logger.error(f"删除失败 {path}: {e}")
            return False

    @staticmethod
    def safe_copy(src: str | Path, dst: str | Path, overwrite: bool = False) -> bool:
        """安全复制文件"""
        try:
            src, dst = Path(src), Path(dst)
            if not src.exists():
                raise ResourceError(f"源文件不存在: {src}", "file")

            if dst.exists() and not overwrite:
                raise ResourceError(f"目标文件已存在: {dst}", "file")

            FileUtils.ensure_dir(dst.parent)
            shutil.copy2(src, dst)
            logger.debug(f"复制文件: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"复制失败 {src} -> {dst}: {e}")
            return False

    @staticmethod
    def safe_move(src: str | Path, dst: str | Path, overwrite: bool = False) -> bool:
        """安全移动文件"""
        try:
            src, dst = Path(src), Path(dst)
            if not src.exists():
                raise ResourceError(f"源文件不存在: {src}", "file")

            if dst.exists() and not overwrite:
                raise ResourceError(f"目标文件已存在: {dst}", "file")

            FileUtils.ensure_dir(dst.parent)
            shutil.move(str(src), str(dst))
            logger.debug(f"移动文件: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"移动失败 {src} -> {dst}: {e}")
            return False

    @staticmethod
    def get_file_size(path: str | Path) -> Optional[int]:
        """获取文件大小（字节）"""
        try:
            return Path(path).stat().st_size
        except Exception:
            return None

    @staticmethod
    def get_file_extension(path: str | Path) -> str:
        """获取文件扩展名（小写）"""
        return Path(path).suffix.lower()

    @staticmethod
    def is_hidden_file(path: str | Path) -> bool:
        """检查是否为隐藏文件"""
        try:
            attrs = Path(path).stat().st_file_attributes
            return bool(attrs & 0x2)  # FILE_ATTRIBUTE_HIDDEN
        except (AttributeError, OSError):
            return Path(path).name.startswith('.')

    @staticmethod
    def is_system_file(path: str | Path) -> bool:
        """检查是否为系统文件"""
        try:
            attrs = Path(path).stat().st_file_attributes
            return bool(attrs & 0x4)  # FILE_ATTRIBUTE_SYSTEM
        except (AttributeError, OSError):
            return False

    @staticmethod
    def resolve_name_conflict(path: str | Path, max_attempts: int = 1000) -> Path:
        """解决文件名冲突"""
        candidate = Path(path)
        if not candidate.exists():
            return candidate

        for index in range(1, max_attempts + 1):
            renamed = candidate.with_name(f'{candidate.stem}({index}){candidate.suffix}')
            if not renamed.exists():
                return renamed

        raise RuntimeError(f'重名文件过多，超过最大尝试次数: {max_attempts}')

    @staticmethod
    def get_unique_filename(path: str | Path) -> Path:
        """获取唯一文件名"""
        return FileUtils.resolve_name_conflict(path)

    @staticmethod
    def read_text(path: str | Path, encoding: str = 'utf-8') -> Optional[str]:
        """读取文本文件"""
        try:
            return Path(path).read_text(encoding=encoding)
        except Exception as e:
            logger.error(f"读取文件失败 {path}: {e}")
            return None

    @staticmethod
    def write_text(path: str | Path, content: str, encoding: str = 'utf-8') -> bool:
        """写入文本文件"""
        try:
            FileUtils.ensure_dir(Path(path).parent)
            Path(path).write_text(content, encoding=encoding)
            return True
        except Exception as e:
            logger.error(f"写入文件失败 {path}: {e}")
            return False

    @staticmethod
    def list_files(directory: str | Path, pattern: str = "*") -> list[Path]:
        """列出目录下的文件"""
        try:
            return list(Path(directory).glob(pattern))
        except Exception as e:
            logger.error(f"列出文件失败 {directory}: {e}")
            return []

    @staticmethod
    def get_directory_size(path: str | Path) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for item in Path(path).rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"计算目录大小失败 {path}: {e}")
        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# 全局文件工具实例
file_utils = FileUtils()
