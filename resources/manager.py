from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
from toolbox_app.core.logger import get_logger
from toolbox_app.core.exceptions import ResourceError

logger = get_logger(__name__)


class ResourceManager:
    """资源管理器"""

    def __init__(self, base_dir: str | Path = None):
        if base_dir is None:
            if getattr(sys, 'frozen', False):
                # PyInstaller 打包环境
                self.base_dir = Path(sys.executable).parent
            else:
                # 开发环境
                self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)

        self._resources_dir = self.base_dir / "resources"
        self._temp_dir = self.base_dir / "temp"
        self._cache_dir = self.base_dir / "cache"

        # 确保目录存在
        self._resources_dir.mkdir(parents=True, exist_ok=True)
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._resource_cache: dict[str, Path] = {}

    @property
    def resources_dir(self) -> Path:
        """获取资源目录"""
        return self._resources_dir

    @property
    def temp_dir(self) -> Path:
        """获取临时目录"""
        return self._temp_dir

    @property
    def cache_dir(self) -> Path:
        """获取缓存目录"""
        return self._cache_dir

    def get_resource(self, *path_parts: str) -> Path:
        """获取资源文件路径"""
        resource_path = self._resources_dir.joinpath(*path_parts)
        if not resource_path.exists():
            raise ResourceError(f"资源不存在: {resource_path}", "resource")
        return resource_path

    def get_resource_or_default(self, *path_parts: str, default: Path = None) -> Optional[Path]:
        """获取资源文件路径，不存在则返回默认值"""
        resource_path = self._resources_dir.joinpath(*path_parts)
        if resource_path.exists():
            return resource_path
        return default

    def get_temp_path(self, *path_parts: str) -> Path:
        """获取临时文件路径"""
        return self._temp_dir.joinpath(*path_parts)

    def get_cache_path(self, *path_parts: str) -> Path:
        """获取缓存文件路径"""
        return self._cache_dir.joinpath(*path_parts)

    def list_resources(self, pattern: str = "*") -> list[Path]:
        """列出资源文件"""
        return list(self._resources_dir.rglob(pattern))

    def resource_exists(self, *path_parts: str) -> bool:
        """检查资源是否存在"""
        return self._resources_dir.joinpath(*path_parts).exists()

    def copy_to_temp(self, source: str | Path, name: str = None) -> Path:
        """复制资源到临时目录"""
        source = Path(source)
        if not source.exists():
            raise ResourceError(f"源文件不存在: {source}", "resource")

        if name is None:
            name = source.name

        temp_path = self._temp_dir / name
        import shutil
        shutil.copy2(source, temp_path)
        return temp_path

    def cleanup_temp(self, max_age_hours: int = 24):
        """清理临时文件"""
        import time

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        try:
            for item in self._temp_dir.rglob("*"):
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        logger.debug(f"清理临时文件: {item}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    def cleanup_cache(self, max_age_days: int = 7):
        """清理缓存"""
        import time

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        try:
            for item in self._cache_dir.rglob("*"):
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        logger.debug(f"清理缓存: {item}")
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")

    def get_resource_size(self, *path_parts: str) -> int:
        """获取资源大小"""
        resource_path = self._resources_dir.joinpath(*path_parts)
        if not resource_path.exists():
            return 0

        if resource_path.is_file():
            return resource_path.stat().st_size
        elif resource_path.is_dir():
            total_size = 0
            for item in resource_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size

        return 0

    def get_total_size(self) -> dict[str, int]:
        """获取所有目录大小"""
        return {
            'resources': self._get_dir_size(self._resources_dir),
            'temp': self._get_dir_size(self._temp_dir),
            'cache': self._get_dir_size(self._cache_dir)
        }

    def _get_dir_size(self, directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"计算目录大小失败 {directory}: {e}")
        return total_size

    def validate_resources(self) -> dict[str, bool]:
        """验证资源"""
        results = {}

        # 检查必需资源
        required_resources = [
            'logo.png',
            'logo.ico'
        ]

        for resource in required_resources:
            results[resource] = self.resource_exists(resource)

        return results

    def get_ffmpeg_path(self) -> Optional[Path]:
        """获取 ffmpeg 路径"""
        # 检查资源目录
        ffmpeg_path = self._resources_dir / "ffmpeg.exe"
        if ffmpeg_path.exists():
            return ffmpeg_path

        # 检查系统 PATH
        import shutil
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return Path(system_ffmpeg)

        return None

    def get_tesseract_path(self) -> Optional[Path]:
        """获取 tesseract 路径"""
        # 检查资源目录
        tesseract_path = self._resources_dir / "tesseract.exe"
        if tesseract_path.exists():
            return tesseract_path

        # 检查系统 PATH
        import shutil
        system_tesseract = shutil.which("tesseract")
        if system_tesseract:
            return Path(system_tesseract)

        return None

    # ------------------------------------------------------------------
    # OCR 模型管理
    # ------------------------------------------------------------------

    def get_ocr_model_path(self, model_name: str) -> Path:
        """获取 OCR 模型文件路径

        Args:
            model_name: 模型名称（如 ``tesseract``、``easyocr``）

        Returns:
            模型文件所在的目录路径

        Raises:
            ResourceError: 模型不存在时抛出
        """
        model_path = self._resources_dir / "ocr_models" / model_name
        if not model_path.exists():
            raise ResourceError(f"OCR 模型不存在: {model_name}", "ocr_model")
        return model_path

    def list_ocr_models(self) -> list[str]:
        """列出可用的 OCR 模型

        Returns:
            模型名称列表，若无模型则返回空列表
        """
        ocr_dir = self._resources_dir / "ocr_models"
        if not ocr_dir.exists():
            return []
        return sorted(
            entry.name for entry in ocr_dir.iterdir() if entry.is_dir()
        )

    def validate_ocr_model(self, model_name: str) -> bool:
        """验证 OCR 模型是否存在且可用

        Args:
            model_name: 模型名称

        Returns:
            True 表示模型有效
        """
        try:
            model_path = self.get_ocr_model_path(model_name)
            # 模型目录中至少包含一个文件才算有效
            return any(model_path.iterdir())
        except ResourceError:
            return False


# 全局资源管理器实例
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager(base_dir: str | Path = None) -> ResourceManager:
    """获取全局资源管理器实例"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager(base_dir)
    return _resource_manager
