from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

try:
    import fitz
except ModuleNotFoundError:
    fitz = None

try:
    from pypdf import PdfReader, PdfWriter
except ModuleNotFoundError:
    PdfReader = None
    PdfWriter = None

try:
    from docx import Document
except ModuleNotFoundError:
    Document = None

SUPPORTED_INPUT_EXTENSIONS = {'.pdf'}
SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp'}
SUPPORTED_TEXT_EXPORT_FORMATS = {'txt', 'docx'}


class PdfToolsError(Exception):
    pass


def collect_pdf_inputs(paths: list[str]) -> list[Path]:
    unique: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
            unique[path] = None
        elif path.is_dir():
            for item in sorted(path.rglob('*')):
                if item.is_file() and item.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
                    unique[item.resolve()] = None
    return sorted(unique.keys())


def probe_tesseract() -> tuple[bool, str]:
    command = shutil.which('tesseract')
    if not command:
        return False, '未检测到 Tesseract，请先安装后再使用 OCR 功能'
    return True, ''


def run_ocr_on_image(image_path: Path) -> str:
    raise PdfToolsError('OCR 实现待接入')


def parse_page_ranges(raw: str, total_pages: int) -> list[int]:
    text = raw.strip()
    if not text:
        raise ValueError('页码范围不能为空')
    pages: set[int] = set()
    for part in text.split(','):
        chunk = part.strip()
        if not chunk:
            raise ValueError('页码范围格式不正确')
        if '-' in chunk:
            start_text, end_text = chunk.split('-', 1)
            if not start_text.isdigit() or not end_text.isdigit():
                raise ValueError('页码范围格式不正确')
            start = int(start_text)
            end = int(end_text)
            if start < 1 or end < 1 or end < start:
                raise ValueError('页码范围不合法')
            if end > total_pages:
                raise ValueError('页码超出 PDF 总页数')
            for page in range(start, end + 1):
                pages.add(page - 1)
        else:
            if not chunk.isdigit():
                raise ValueError('页码范围格式不正确')
            page = int(chunk)
            if page < 1 or page > total_pages:
                raise ValueError('页码超出 PDF 总页数')
            pages.add(page - 1)
    return sorted(pages)


def build_pdf_output_path(input_path: Path, output_dir: Path, suffix: str) -> Path:
    return output_dir / f'{input_path.stem}{suffix}'


def build_split_output_paths(input_path: Path, output_dir: Path, page_indexes: list[int]) -> list[Path]:
    return [output_dir / f'{input_path.stem}_page_{page + 1:03d}.pdf' for page in page_indexes]


def build_image_output_paths(input_path: Path, output_dir: Path, total_pages: int, image_format: str) -> list[Path]:
    suffix = image_format.strip().lower()
    return [output_dir / f'{input_path.stem}_page_{page:03d}.{suffix}' for page in range(1, total_pages + 1)]


def validate_pdf_action(action: str, files: list[Path], page_ranges_text: str) -> list[str]:
    errors: list[str] = []
    normalized = action.strip().lower()
    if normalized == 'merge' and len(files) < 2:
        errors.append('请选择至少两个 PDF 文件')
    if normalized == 'split':
        if len(files) != 1:
            errors.append('拆分功能只支持单个 PDF')
        if not page_ranges_text.strip():
            errors.append('请输入拆分页码范围')
    if normalized in {'images', 'word', 'text'} and len(files) != 1:
        errors.append('该功能只支持单个 PDF')
    return errors


def merge_pdfs(inputs: list[Path], output_path: Path) -> Path:
    if len(inputs) < 2:
        raise PdfToolsError('至少需要两个 PDF 文件才能合并')
    if PdfReader is None or PdfWriter is None:
        raise PdfToolsError('未安装 pypdf，无法执行 PDF 合并')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    for path in inputs:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
    with output_path.open('wb') as stream:
        writer.write(stream)
    return output_path


def split_pdf(input_path: Path, output_dir: Path, page_indexes: list[int]) -> list[Path]:
    if PdfReader is None or PdfWriter is None:
        raise PdfToolsError('未安装 pypdf，无法执行 PDF 拆分')
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(input_path))
    outputs = build_split_output_paths(input_path, output_dir, page_indexes)
    for page_index, output_path in zip(page_indexes, outputs):
        writer = PdfWriter()
        writer.add_page(reader.pages[page_index])
        with output_path.open('wb') as stream:
            writer.write(stream)
    return outputs


def pdf_to_images(input_path: Path, output_dir: Path, image_format: str, dpi: int) -> list[Path]:
    if fitz is None:
        raise PdfToolsError('未安装 PyMuPDF，无法执行 PDF 转图片')
    normalized_format = image_format.strip().lower()
    if normalized_format not in SUPPORTED_IMAGE_FORMATS:
        raise PdfToolsError(f'暂不支持输出为 {image_format}')
    if dpi <= 0:
        raise PdfToolsError('DPI 必须大于 0')
    output_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(str(input_path))
    try:
        pages = list(document)
        outputs = build_image_output_paths(input_path, output_dir, len(pages), normalized_format)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        for page, output_path in zip(pages, outputs):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pixmap.save(str(output_path))
        return outputs
    finally:
        close = getattr(document, 'close', None)
        if callable(close):
            close()


def choose_text_extraction_mode(text: str, ocr_fallback: bool) -> str:
    if text and text.strip():
        return 'text'
    if ocr_fallback:
        return 'ocr'
    return 'empty'


def extract_text_from_pdf(input_path: Path, ocr_fallback: bool = False, dpi: int = 150) -> str:
    if fitz is None:
        raise PdfToolsError('未安装 PyMuPDF，无法提取 PDF 文字')
    document = fitz.open(str(input_path))
    chunks: list[str] = []
    try:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text('text')
            mode = choose_text_extraction_mode(text, ocr_fallback)
            if mode == 'text':
                chunks.append(text.strip())
                continue
            if mode == 'ocr':
                available, message = probe_tesseract()
                if not available:
                    raise PdfToolsError(message)
                scale = dpi / 72.0
                matrix = fitz.Matrix(scale, scale)
                with tempfile.TemporaryDirectory() as tmp:
                    image_path = Path(tmp) / f'page_{page_index:03d}.png'
                    page.get_pixmap(matrix=matrix, alpha=False).save(str(image_path))
                    ocr_text = run_ocr_on_image(image_path)
                if ocr_text.strip():
                    chunks.append(ocr_text.strip())
        return '\n\n'.join(chunk for chunk in chunks if chunk)
    finally:
        close = getattr(document, 'close', None)
        if callable(close):
            close()


def export_pdf_text(input_path: Path, output_dir: Path, export_format: str, ocr_fallback: bool = False, dpi: int = 150) -> Path:
    normalized = export_format.strip().lower()
    if normalized not in SUPPORTED_TEXT_EXPORT_FORMATS:
        raise PdfToolsError(f'暂不支持导出为 {export_format}')
    output_dir.mkdir(parents=True, exist_ok=True)
    text = extract_text_from_pdf(input_path, ocr_fallback=ocr_fallback, dpi=dpi)
    if normalized == 'txt':
        output_path = build_pdf_output_path(input_path, output_dir, '.txt')
        output_path.write_text(text, encoding='utf-8')
        return output_path
    if Document is None:
        raise PdfToolsError('未安装 python-docx，无法导出 DOCX')
    output_path = build_pdf_output_path(input_path, output_dir, '.docx')
    document = Document()
    for paragraph in text.split('\n\n'):
        document.add_paragraph(paragraph)
    document.save(str(output_path))
    return output_path
