"""Base64 编解码服务 — 包装 base64/converter.py"""
from __future__ import annotations

from pathlib import Path
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)

SUPPORTED_IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}


class Base64Service:
    """Base64 编解码服务"""

    def __init__(self):
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from ..loaders import load_module_once
            converter_path = Path(__file__).resolve().parent.parent.parent / 'base64' / 'converter.py'
            self._converter = load_module_once('base64_converter_module', converter_path)
        return self._converter

    def encode(self, image_path: str | Path, data_url: bool = False) -> str:
        """图片转 Base64"""
        try:
            conv = self._get_converter()
            encoded = conv.encode_image_to_base64(image_path)
            if data_url:
                encoded = conv.build_data_url(encoded, Path(image_path).suffix)
            return encoded
        except Exception as e:
            raise ServiceError(f'Base64 编码失败: {e}', 'Base64Service')

    def decode(self, text: str, output_dir: str | Path, output_name: str) -> Path:
        """Base64 还原为图片"""
        try:
            conv = self._get_converter()
            return conv.decode_base64_to_file(text, output_dir, output_name)
        except Exception as e:
            raise ServiceError(f'Base64 解码失败: {e}', 'Base64Service')

    def save_text(self, text: str, output_dir: str | Path, filename: str) -> Path:
        """保存 Base64 文本到文件"""
        try:
            conv = self._get_converter()
            return conv.save_base64_text(text, output_dir, filename)
        except Exception as e:
            raise ServiceError(f'保存失败: {e}', 'Base64Service')
