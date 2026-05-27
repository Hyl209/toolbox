from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional
from ..toolbox_app.core.logger import get_logger

logger = get_logger(__name__)


class TempManager:
    """临时文件管理器"""

    def __init__(self, temp_dir: str | Path = None):
        if temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "HylToolbox"
        else:
            self.temp_dir = Path(temp_dir)

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._temp_files: dict[str, Path] = {}
        self._temp_dirs: dict[str, Path] = {}

    def create_temp_file(self, suffix: str = "", prefix: str = "tmp_",
                         content: bytes = None) -> Path:
        """创建临时文件"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=self.temp_dir,
            delete=False
        )

        if content:
            temp_file.write(content)
            temp_file.flush()

        temp_file.close()
        temp_path = Path(temp_file.name)

        self._temp_files[str(temp_path)] = temp_path
        logger.debug(f"创建临时文件: {temp_path}")

        return temp_path

    def create_temp_dir(self, suffix: str = "", prefix: str = "tmp_") -> Path:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp(
            suffix=suffix,
            prefix=prefix,
            dir=self.temp_dir
        )

        temp_path = Path(temp_dir)
        self._temp_dirs[str(temp_path)] = temp_path
        logger.debug(f"创建临时目录: {temp_path}")

        return temp_path

    def get_temp_path(self, name: str) -> Path:
        """获取临时文件路径"""
        return self.temp_dir / name

    def exists(self, name: str) -> bool:
        """检查临时文件是否存在"""
        return (self.temp_dir / name).exists()

    def delete_temp_file(self, path: str | Path) -> bool:
        """删除临时文件"""
        path = Path(path)
        try:
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)

                self._temp_files.pop(str(path), None)
                self._temp_dirs.pop(str(path), None)
                logger.debug(f"删除临时文件: {path}")
                return True
        except Exception as e:
            logger.error(f"删除临时文件失败 {path}: {e}")
        return False

    def cleanup_all(self):
        """清理所有临时文件"""
        # 清理跟踪的文件
        for path in list(self._temp_files.values()):
            self.delete_temp_file(path)

        for path in list(self._temp_dirs.values()):
            self.delete_temp_file(path)

        self._temp_files.clear()
        self._temp_dirs.clear()

        logger.info("清理所有临时文件完成")

    def cleanup_old(self, max_age_hours: int = 24):
        """清理过期的临时文件"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        try:
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        logger.debug(f"清理过期临时文件: {item}")

            # 清理空目录
            for item in self.temp_dir.rglob("*"):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
                    logger.debug(f"清理空临时目录: {item}")

        except Exception as e:
            logger.error(f"清理过期临时文件失败: {e}")

    def get_temp_size(self) -> int:
        """获取临时文件总大小"""
        total_size = 0
        try:
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"计算临时文件大小失败: {e}")
        return total_size

    def get_temp_count(self) -> int:
        """获取临时文件数量"""
        count = 0
        try:
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    count += 1
        except Exception as e:
            logger.error(f"计算临时文件数量失败: {e}")
        return count

    def list_temp_files(self) -> list[Path]:
        """列出所有临时文件"""
        files = []
        try:
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    files.append(item)
        except Exception as e:
            logger.error(f"列出临时文件失败: {e}")
        return files

    def create_temp_copy(self, source: str | Path, name: str = None) -> Path:
        """创建临时副本"""
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source}")

        if name is None:
            name = source.name

        temp_path = self.get_temp_path(name)
        shutil.copy2(source, temp_path)

        self._temp_files[str(temp_path)] = temp_path
        logger.debug(f"创建临时副本: {source} -> {temp_path}")

        return temp_path

    def get_or_create_temp(self, name: str, creator: callable = None) -> Path:
        """获取或创建临时文件"""
        temp_path = self.get_temp_path(name)

        if temp_path.exists():
            return temp_path

        if creator:
            return creator(temp_path)

        return self.create_temp_file(suffix=f"_{name}")

    def __del__(self):
        """析构时清理"""
        # 注意：不自动清理，由用户显式调用
        pass


# 全局临时文件管理器实例
_temp_manager: Optional[TempManager] = None


def get_temp_manager(temp_dir: str | Path = None) -> TempManager:
    """获取全局临时文件管理器实例"""
    global _temp_manager
    if _temp_manager is None:
        _temp_manager = TempManager(temp_dir)
    return _temp_manager
