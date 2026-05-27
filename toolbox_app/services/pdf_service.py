from __future__ import annotations

from pathlib import Path
from typing import Optional
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils

logger = get_logger(__name__)


class PDFService:
    """PDF 服务"""

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        try:
            import PyPDF2
            self._initialized = True
            logger.info("PDF 服务初始化成功")
        except ImportError:
            raise ServiceError("PyPDF2 未安装", "PDFService")

    def merge_pdfs(self, input_paths: list[str | Path], output_path: str | Path) -> bool:
        """合并 PDF 文件"""
        self.initialize()

        try:
            from PyPDF2 import PdfMerger
            merger = PdfMerger()

            for path in input_paths:
                if not Path(path).exists():
                    raise ServiceError(f"文件不存在: {path}", "PDFService")
                merger.append(str(path))

            output_path = Path(output_path)
            file_utils.ensure_dir(output_path.parent)
            merger.write(str(output_path))
            merger.close()

            logger.info(f"PDF 合并完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF 合并失败: {e}")
            raise ServiceError(f"PDF 合并失败: {e}", "PDFService")

    def split_pdf(self, input_path: str | Path, output_dir: str | Path,
                  pages: list[int] = None) -> list[Path]:
        """拆分 PDF 文件"""
        self.initialize()

        try:
            from PyPDF2 import PdfReader, PdfWriter
            input_path = Path(input_path)
            output_dir = Path(output_dir)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "PDFService")

            file_utils.ensure_dir(output_dir)
            reader = PdfReader(str(input_path))
            output_files = []

            if pages is None:
                pages = list(range(len(reader.pages)))

            for page_num in pages:
                if page_num < 0 or page_num >= len(reader.pages):
                    continue

                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])

                output_file = output_dir / f"{input_path.stem}_page{page_num + 1}.pdf"
                with open(output_file, 'wb') as f:
                    writer.write(f)

                output_files.append(output_file)

            logger.info(f"PDF 拆分完成: {len(output_files)} 页")
            return output_files

        except Exception as e:
            logger.error(f"PDF 拆分失败: {e}")
            raise ServiceError(f"PDF 拆分失败: {e}", "PDFService")

    def extract_text(self, input_path: str | Path, pages: list[int] = None) -> str:
        """提取 PDF 文本"""
        self.initialize()

        try:
            from PyPDF2 import PdfReader
            input_path = Path(input_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "PDFService")

            reader = PdfReader(str(input_path))
            text_parts = []

            if pages is None:
                pages = list(range(len(reader.pages)))

            for page_num in pages:
                if page_num < 0 or page_num >= len(reader.pages):
                    continue
                text_parts.append(reader.pages[page_num].extract_text())

            return '\n'.join(text_parts)

        except Exception as e:
            logger.error(f"PDF 文本提取失败: {e}")
            raise ServiceError(f"PDF 文本提取失败: {e}", "PDFService")

    def add_password(self, input_path: str | Path, output_path: str | Path,
                     password: str) -> bool:
        """添加密码保护"""
        self.initialize()

        try:
            from PyPDF2 import PdfReader, PdfWriter
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "PDFService")

            reader = PdfReader(str(input_path))
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.encrypt(password)

            file_utils.ensure_dir(output_path.parent)
            with open(output_path, 'wb') as f:
                writer.write(f)

            logger.info(f"PDF 密码添加完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF 密码添加失败: {e}")
            raise ServiceError(f"PDF 密码添加失败: {e}", "PDFService")

    def get_page_count(self, input_path: str | Path) -> int:
        """获取 PDF 页数"""
        self.initialize()

        try:
            from PyPDF2 import PdfReader
            input_path = Path(input_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "PDFService")

            reader = PdfReader(str(input_path))
            return len(reader.pages)

        except Exception as e:
            logger.error(f"获取 PDF 页数失败: {e}")
            raise ServiceError(f"获取 PDF 页数失败: {e}", "PDFService")
