from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

MIME_TO_SUFFIX = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/webp': '.webp',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'text/plain': '.txt',
    'application/json': '.json',
    'application/pdf': '.pdf',
    'application/zip': '.zip',
}
SUFFIX_TO_MIME = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
}
SUPPORTED_IMAGE_SUFFIXES = set(SUFFIX_TO_MIME)


def encode_file_to_base64(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise ValueError('文件不存在')
    return base64.b64encode(path.read_bytes()).decode('ascii')


def encode_image_to_base64(image_path: str | Path) -> str:
    return encode_file_to_base64(image_path)


def build_data_url(base64_text: str, image_suffix: str) -> str:
    mime = SUFFIX_TO_MIME.get(image_suffix.lower()) or mimetypes.types_map.get(image_suffix.lower()) or 'application/octet-stream'
    return f'data:{mime};base64,{base64_text}'


def normalize_base64_text(text: str) -> str:
    raw = (text or '').strip()
    if not raw:
        raise ValueError('请输入 Base64 内容')
    if raw.startswith('data:'):
        marker = ';base64,'
        if marker not in raw:
            raise ValueError('Data URL 格式不正确')
        raw = raw.split(marker, 1)[1].strip()
    compact = ''.join(raw.split())
    try:
        base64.b64decode(compact, validate=True)
    except Exception as exc:
        raise ValueError('Base64 内容无效') from exc
    return compact


def infer_extension_from_base64(text: str) -> str:
    raw = (text or '').strip()
    if raw.startswith('data:'):
        mime = raw.split(';', 1)[0][5:].strip().lower()
        if mime in MIME_TO_SUFFIX:
            return MIME_TO_SUFFIX[mime]
        suffix = mimetypes.guess_extension(mime)
        if suffix:
            return suffix
    return ''


def decode_base64_to_file(
    text: str,
    output_dir: str | Path,
    output_name: str,
    default_extension: str = '.bin',
) -> Path:
    normalized = normalize_base64_text(text)
    ext = infer_extension_from_base64(text) or default_extension
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    safe_name = (output_name or 'output').strip()
    if not Path(safe_name).suffix:
        safe_name = f'{safe_name}{ext or default_extension}'
    output_path = output_root / safe_name
    output_path.write_bytes(base64.b64decode(normalized))
    return output_path


def save_base64_text(text: str, output_dir: str | Path, filename: str) -> Path:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    name = filename.strip() or 'output.txt'
    if not name.lower().endswith('.txt'):
        name = f'{name}.txt'
    output_path = output_root / name
    output_path.write_text(text, encoding='utf-8')
    return output_path


def guess_mime_from_path(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    return SUFFIX_TO_MIME.get(suffix) or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
