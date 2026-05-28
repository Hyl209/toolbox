"""图片格式转换服务 — 包装 image-convert/converter.py"""
from __future__ import annotations

from pathlib import Path
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)


class ImageService:
    """图片格式转换服务（基于 ImageMagick）"""

    def __init__(self):
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from ..loaders import load_module_once
            converter_path = Path(__file__).resolve().parent.parent.parent / 'modules' / 'image-converter' / 'converter.py'
            self._converter = load_module_once('image_convert_module', converter_path)
        return self._converter

    def check_imagemagick(self) -> tuple[bool, str]:
        """检查 ImageMagick 是否可用"""
        conv = self._get_converter()
        return conv.probe_imagemagick()

    def convert(self, input_path: Path, output_dir: Path, target_format: str,
                quality: int = 85, preserve_alpha: bool = True,
                jpg_background: str = 'white',
                target_size_kb: float | None = None) -> Path:
        """转换单张图片格式"""
        try:
            conv = self._get_converter()
            return conv.convert_image(
                input_path=input_path,
                output_dir=output_dir,
                target_format=target_format,
                quality=quality,
                preserve_alpha=preserve_alpha,
                jpg_background=jpg_background,
                target_size_kb=target_size_kb,
            )
        except Exception as e:
            raise ServiceError(f'图片转换失败: {e}', 'ImageService')

    def batch_convert(self, files: list[Path], output_dir: Path, **kwargs) -> list[Path]:
        """批量转换图片"""
        results = []
        for src in files:
            out = self.convert(src, output_dir, **kwargs)
            results.append(out)
        return results

    def validate_target_size(self, raw: str):
        """验证目标大小参数"""
        conv = self._get_converter()
        return conv.validate_target_size_kb(raw)
