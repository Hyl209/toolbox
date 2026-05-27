"""PDF 工具服务 — 包装 pdf-tools/converter.py"""
from __future__ import annotations

from pathlib import Path
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)


class PDFService:
    """PDF 处理服务"""

    def __init__(self):
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from ..loaders import load_module_once
            converter_path = Path(__file__).resolve().parent.parent.parent / 'pdf-tools' / 'converter.py'
            self._converter = load_module_once('pdf_tools_converter_module', converter_path)
        return self._converter

    def validate_action(self, action: str, files: list[Path], page_ranges: str) -> list[str]:
        """验证 PDF 操作参数"""
        conv = self._get_converter()
        return conv.validate_pdf_action(action, files, page_ranges)

    def merge(self, inputs: list[Path], output_path: Path) -> Path:
        """合并多个 PDF"""
        try:
            conv = self._get_converter()
            return conv.merge_pdfs(inputs, output_path)
        except Exception as e:
            raise ServiceError(f'PDF 合并失败: {e}', 'PDFService')

    def split(self, input_path: Path, output_dir: Path, page_indexes: list[int]) -> list[Path]:
        """拆分 PDF"""
        try:
            conv = self._get_converter()
            return conv.split_pdf(input_path, output_dir, page_indexes)
        except Exception as e:
            raise ServiceError(f'PDF 拆分失败: {e}', 'PDFService')

    def to_images(self, input_path: Path, output_dir: Path,
                  image_format: str = 'png', dpi: int = 150) -> list[Path]:
        """PDF 转图片"""
        try:
            conv = self._get_converter()
            return conv.pdf_to_images(input_path, output_dir, image_format, dpi)
        except Exception as e:
            raise ServiceError(f'PDF 转图片失败: {e}', 'PDFService')

    def extract_text(self, input_path: Path, ocr_fallback: bool = False,
                     dpi: int = 150) -> str:
        """提取 PDF 文本"""
        try:
            conv = self._get_converter()
            return conv.extract_text_from_pdf(input_path, ocr_fallback, dpi)
        except Exception as e:
            raise ServiceError(f'文本提取失败: {e}', 'PDFService')

    def export_text(self, input_path: Path, output_dir: Path,
                    export_format: str = 'txt', ocr_fallback: bool = False,
                    dpi: int = 150) -> Path:
        """导出 PDF 文本到文件"""
        try:
            conv = self._get_converter()
            return conv.export_pdf_text(input_path, output_dir, export_format, ocr_fallback, dpi)
        except Exception as e:
            raise ServiceError(f'文本导出失败: {e}', 'PDFService')

    def parse_page_ranges(self, raw: str, total_pages: int) -> list[int]:
        """解析页码范围"""
        conv = self._get_converter()
        return conv.parse_page_ranges(raw, total_pages)
