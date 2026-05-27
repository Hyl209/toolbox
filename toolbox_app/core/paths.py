from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Optional
from .logger import get_logger

logger = get_logger(__name__)


class PathManager:
    """路径管理器"""

    def __init__(self, app_name: str = "HylToolbox"):
        self.app_name = app_name
        self._base_dir: Optional[Path] = None
        self._resource_dir: Optional[Path] = None
        self._temp_dir: Optional[Path] = None
        self._log_dir: Optional[Path] = None
        self._config_dir: Optional[Path] = None
        self._setup_paths()

    def _setup_paths(self):
        """初始化路径"""
        # 基础目录
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包环境
            self._base_dir = Path(sys.executable).parent
        else:
            # 开发环境
            self._base_dir = Path(__file__).parent.parent.parent

        # 资源目录
        self._resource_dir = self._base_dir / "resources"
        self._resource_dir.mkdir(parents=True, exist_ok=True)

        # 临时目录
        self._temp_dir = Path(tempfile.gettempdir()) / self.app_name
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        # 日志目录
        self._log_dir = self._base_dir / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 配置目录
        self._config_dir = self._base_dir / "config"
        self._config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        """获取应用基础目录"""
        return self._base_dir

    @property
    def resource_dir(self) -> Path:
        """获取资源目录"""
        return self._resource_dir

    @property
    def temp_dir(self) -> Path:
        """获取临时目录"""
        return self._temp_dir

    @property
    def log_dir(self) -> Path:
        """获取日志目录"""
        return self._log_dir

    @property
    def config_dir(self) -> Path:
        """获取配置目录"""
        return self._config_dir

    def get_resource(self, *path_parts: str) -> Path:
        """获取资源文件路径"""
        return self.resource_dir.joinpath(*path_parts)

    def get_temp(self, *path_parts: str) -> Path:
        """获取临时文件路径"""
        return self.temp_dir.joinpath(*path_parts)

    def get_log(self, *path_parts: str) -> Path:
        """获取日志文件路径"""
        return self.log_dir.joinpath(*path_parts)

    def get_config(self, *path_parts: str) -> Path:
        """获取配置文件路径"""
        return self.config_dir.joinpath(*path_parts)

    def cleanup_temp(self, max_age_hours: int = 24):
        """清理过期的临时文件"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        try:
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        logger.debug(f"清理临时文件: {item}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    def ensure_dir(self, path: Path) -> Path:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        return path


# 全局路径管理器实例
_path_manager: Optional[PathManager] = None


def get_path_manager(app_name: str = "HylToolbox") -> PathManager:
    """获取全局路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager(app_name)
    return _path_manager
