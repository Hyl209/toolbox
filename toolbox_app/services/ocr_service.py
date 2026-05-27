from __future__ import annotations

from pathlib import Path
from typing import Optional
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils

logger = get_logger(__name__)


class OCRService:
    """OCR 服务"""

    def __init__(self):
        self._initialized = False
        self._engine = None

    def initialize(self, engine: str = "tesseract"):
        """初始化服务"""
        if self._initialized:
            return

        try:
            if engine == "tesseract":
                self._init_tesseract()
            elif engine == "easyocr":
                self._init_easyocr()
            else:
                raise ServiceError(f"不支持的 OCR 引擎: {engine}", "OCRService")

            self._initialized = True
            logger.info(f"OCR 服务初始化成功 (引擎: {engine})")

        except Exception as e:
            logger.error(f"OCR 服务初始化失败: {e}")
            raise ServiceError(f"OCR 服务初始化失败: {e}", "OCRService")

    def _init_tesseract(self):
        """初始化 Tesseract"""
        try:
            import pytesseract
            from PIL import Image
            self._engine = "tesseract"
            # 测试是否可用
            pytesseract.get_tesseract_version()
        except ImportError:
            raise ServiceError("pytesseract 或 Pillow 未安装", "OCRService")
        except Exception as e:
            raise ServiceError(f"Tesseract 初始化失败: {e}", "OCRService")

    def _init_easyocr(self):
        """初始化 EasyOCR"""
        try:
            import easyocr
            self._engine = "easyocr"
            self._reader = easyocr.Reader(['ch_sim', 'en'])
        except ImportError:
            raise ServiceError("easyocr 未安装", "OCRService")

    def recognize_text(self, image_path: str | Path, language: str = "chi_sim+eng") -> str:
        """识别图片文本"""
        self.initialize()

        try:
            image_path = Path(image_path)

            if not image_path.exists():
                raise ServiceError(f"文件不存在: {image_path}", "OCRService")

            if self._engine == "tesseract":
                return self._recognize_tesseract(image_path, language)
            elif self._engine == "easyocr":
                return self._recognize_easyocr(image_path)
            else:
                raise ServiceError("OCR 引擎未初始化", "OCRService")

        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            raise ServiceError(f"OCR 识别失败: {e}", "OCRService")

    def _recognize_tesseract(self, image_path: Path, language: str) -> str:
        """使用 Tesseract 识别"""
        import pytesseract
        from PIL import Image

        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)
        return text.strip()

    def _recognize_easyocr(self, image_path: Path) -> str:
        """使用 EasyOCR 识别"""
        results = self._reader.readtext(str(image_path))
        text_parts = [result[1] for result in results]
        return '\n'.join(text_parts)

    def recognize_text_from_pdf(self, pdf_path: str | Path, pages: list[int] = None) -> str:
        """从 PDF 识别文本"""
        self.initialize()

        try:
            pdf_path = Path(pdf_path)

            if not pdf_path.exists():
                raise ServiceError(f"文件不存在: {pdf_path}", "OCRService")

            # 将 PDF 页面转换为图片
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path))

            if pages:
                images = [images[i] for i in pages if i < len(images)]

            text_parts = []
            for i, image in enumerate(images):
                # 保存临时图片
                temp_image = pdf_path.parent / f"temp_page_{i}.png"
                image.save(str(temp_image))

                try:
                    text = self.recognize_text(temp_image)
                    text_parts.append(text)
                finally:
                    # 清理临时文件
                    file_utils.safe_delete(temp_image)

            return '\n\n'.join(text_parts)

        except Exception as e:
            logger.error(f"PDF OCR 识别失败: {e}")
            raise ServiceError(f"PDF OCR 识别失败: {e}", "OCRService")

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言"""
        if self._engine == "tesseract":
            import pytesseract
            return pytesseract.get_languages()
        elif self._engine == "easyocr":
            return ['ch_sim', 'en', 'ja', 'ko']
        return []
