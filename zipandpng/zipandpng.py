#!/usr/bin/env python3
import argparse
import struct
import sys
from pathlib import Path

MAGIC = b'ZPNGPKG1'
NAME_LEN_STRUCT = struct.Struct('>H')
DATA_LEN_STRUCT = struct.Struct('>Q')
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
JPEG_SIGNATURE = b'\xff\xd8\xff'
GIF87A_SIGNATURE = b'GIF87a'
GIF89A_SIGNATURE = b'GIF89a'
WEBP_RIFF_SIGNATURE = b'RIFF'
WEBP_FORMAT_SIGNATURE = b'WEBP'


class ZipAndPngError(Exception):
    pass


def read_bytes(path: Path, label: str = '输入文件') -> bytes:
    if not path.exists():
        raise ZipAndPngError(f'{label}不存在: {path}')
    return path.read_bytes()


def detect_cover_image_format(data: bytes) -> str:
    if data.startswith(PNG_SIGNATURE):
        return 'png'
    if data.startswith(JPEG_SIGNATURE):
        return 'jpeg'
    if data.startswith(GIF87A_SIGNATURE) or data.startswith(GIF89A_SIGNATURE):
        return 'gif'
    if len(data) >= 12 and data.startswith(WEBP_RIFF_SIGNATURE) and data[8:12] == WEBP_FORMAT_SIGNATURE:
        return 'webp'
    raise ZipAndPngError('不支持的封面图片格式')


def ensure_supported_cover_image(path: Path, data: bytes) -> str:
    try:
        return detect_cover_image_format(data)
    except ZipAndPngError as exc:
        raise ZipAndPngError(f'{exc}: {path}') from exc


def build_default_disguised_output_path(image_path: Path) -> Path:
    return image_path.with_name(f'{image_path.stem}_disguised{image_path.suffix}')


def build_payload(file_path: Path, file_bytes: bytes) -> bytes:
    name_bytes = file_path.name.encode('utf-8')
    if len(name_bytes) > 65535:
        raise ZipAndPngError('文件名过长')
    return b''.join([
        MAGIC,
        NAME_LEN_STRUCT.pack(len(name_bytes)),
        name_bytes,
        DATA_LEN_STRUCT.pack(len(file_bytes)),
        file_bytes,
    ])


def parse_appended_payload(data: bytes):
    marker = data.rfind(MAGIC)
    if marker == -1:
        return None

    offset = marker + len(MAGIC)
    if len(data) < offset + NAME_LEN_STRUCT.size:
        raise ZipAndPngError('附加数据损坏：缺少文件名长度')

    (name_len,) = NAME_LEN_STRUCT.unpack(data[offset:offset + NAME_LEN_STRUCT.size])
    offset += NAME_LEN_STRUCT.size

    if len(data) < offset + name_len + DATA_LEN_STRUCT.size:
        raise ZipAndPngError('附加数据损坏：元数据不完整')

    name_bytes = data[offset:offset + name_len]
    offset += name_len
    (file_len,) = DATA_LEN_STRUCT.unpack(data[offset:offset + DATA_LEN_STRUCT.size])
    offset += DATA_LEN_STRUCT.size

    file_data = data[offset:]
    if len(file_data) != file_len:
        raise ZipAndPngError('附加数据损坏：文件长度不匹配')

    return {
        'filename': name_bytes.decode('utf-8'),
        'file_size': file_len,
        'file_data': file_data,
        'marker_offset': marker,
    }


def get_embedded_file_info(image_path: Path) -> dict:
    image_bytes = read_bytes(image_path, '输入图片')
    image_format = ensure_supported_cover_image(image_path, image_bytes)
    payload = parse_appended_payload(image_bytes)
    if payload is None:
        return {'found': False, 'filename': None, 'file_size': 0, 'image_format': image_format}
    return {
        'found': True,
        'filename': payload['filename'],
        'file_size': payload['file_size'],
        'image_format': image_format,
    }


def disguise_file(image_path: Path, payload_path: Path, output_path: Path | None = None) -> int:
    image_bytes = read_bytes(image_path, '输入图片')
    payload_bytes = read_bytes(payload_path, '输入文件')
    ensure_supported_cover_image(image_path, image_bytes)

    if output_path is None:
        output_path = build_default_disguised_output_path(image_path)

    payload = build_payload(payload_path, payload_bytes)
    output_path.write_bytes(image_bytes + payload)
    print(f'伪装完成: {output_path}')
    return 0


def recover_file(image_path: Path, output_path: Path | None) -> int:
    image_bytes = read_bytes(image_path, '输入图片')
    ensure_supported_cover_image(image_path, image_bytes)
    payload = parse_appended_payload(image_bytes)
    if payload is None:
        raise ZipAndPngError('未发现附加文件')

    if output_path is None:
        output_path = image_path.with_name(payload['filename'])

    output_path.write_bytes(payload['file_data'])
    print(f'恢复完成: {output_path}')
    return 0


def show_info(image_path: Path) -> int:
    info = get_embedded_file_info(image_path)
    if not info['found']:
        print('未发现附加文件')
        return 0

    print('发现附加文件')
    print(f"封面格式: {info['image_format']}")
    print(f"文件名: {info['filename']}")
    print(f"大小: {info['file_size']} bytes")
    return 0


def cmd_disguise(args) -> int:
    output = Path(args.output) if args.output else None
    return disguise_file(Path(args.image), Path(args.file), output)


def cmd_recover(args) -> int:
    output = Path(args.output) if args.output else None
    return recover_file(Path(args.image), output)


def cmd_info(args) -> int:
    return show_info(Path(args.image))


def cmd_merge(args) -> int:
    return disguise_file(Path(args.image), Path(args.file), Path(args.output))


def cmd_extract(args) -> int:
    output = Path(args.output) if args.output else None
    return recover_file(Path(args.image), output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='把任意单文件伪装到 PNG/JPG/GIF/WEBP 封面中，并支持恢复原文件')
    subparsers = parser.add_subparsers(dest='command', required=True)

    disguise_parser = subparsers.add_parser('disguise', help='把任意单文件伪装进图片封面')
    disguise_parser.add_argument('image')
    disguise_parser.add_argument('file')
    disguise_parser.add_argument('output', nargs='?')
    disguise_parser.set_defaults(func=cmd_disguise)

    recover_parser = subparsers.add_parser('recover', help='从图片中恢复原始单文件')
    recover_parser.add_argument('image')
    recover_parser.add_argument('output', nargs='?')
    recover_parser.set_defaults(func=cmd_recover)

    info_parser = subparsers.add_parser('info', help='查看图片中的附加文件信息')
    info_parser.add_argument('image')
    info_parser.set_defaults(func=cmd_info)

    merge_parser = subparsers.add_parser('merge', help='disguise 的兼容别名')
    merge_parser.add_argument('image')
    merge_parser.add_argument('file')
    merge_parser.add_argument('output')
    merge_parser.set_defaults(func=cmd_merge)

    extract_parser = subparsers.add_parser('extract', help='recover 的兼容别名')
    extract_parser.add_argument('image')
    extract_parser.add_argument('output', nargs='?')
    extract_parser.set_defaults(func=cmd_extract)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ZipAndPngError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
