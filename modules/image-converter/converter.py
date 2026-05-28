from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SUPPORTED_INPUT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
FORMAT_SUFFIXES = {
    'jpg': '.jpg',
    'jpeg': '.jpg',
    'png': '.png',
    'webp': '.webp',
    'heic': '.heic',
}
JPG_BACKGROUND_MAP = {
    'white': 'white',
    'black': 'black',
    'transparent': 'white',
}


class ImageConvertError(Exception):
    pass


def probe_imagemagick() -> tuple[bool, str]:
    command = shutil.which('magick')
    if not command:
        return False, '未检测到 ImageMagick（magick），请先安装后再使用图片格式互转功能'
    return True, ''


def collect_image_inputs(paths: list[str]) -> list[Path]:
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


def choose_image_output_suffix(target_format: str) -> str:
    normalized = target_format.strip().lower()
    if normalized not in FORMAT_SUFFIXES:
        raise ValueError(f'不支持的目标格式: {target_format}')
    return FORMAT_SUFFIXES[normalized]


def map_jpg_background_option(option: str) -> str:
    normalized = option.strip().lower() if option else 'white'
    return JPG_BACKGROUND_MAP.get(normalized, 'white')


def validate_target_size_kb(raw: str):
    text = raw.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError('目标大小必须是正数') from exc
    if value <= 0:
        raise ValueError('目标大小必须是正数')
    return int(value) if value.is_integer() else value


def build_output_path(input_path: Path, output_dir: Path, target_format: str) -> Path:
    return output_dir / f'{input_path.stem}{choose_image_output_suffix(target_format)}'


def generate_quality_candidates(start_quality: int, minimum: int = 25, step: int = 10) -> list[int]:
    quality = max(minimum, min(100, int(start_quality)))
    values: list[int] = []
    while quality >= minimum:
        values.append(quality)
        quality -= step
    if values[-1] != minimum:
        values.append(minimum)
    return values


def generate_resize_candidates() -> list[int]:
    return list(range(100, 49, -5))


def plan_target_attempts(start_quality: int) -> list[tuple[int, int]]:
    attempts: list[tuple[int, int]] = []
    qualities = generate_quality_candidates(start_quality)
    for resize in generate_resize_candidates():
        for quality in qualities:
            attempts.append((quality, resize))
    return attempts


def build_magick_command(
    input_path: Path,
    output_path: Path,
    target_format: str,
    quality: int,
    preserve_alpha: bool,
    jpg_background: str,
    resize_percent: int | None,
) -> list[str]:
    command = ['magick', str(input_path)]
    if resize_percent is not None and resize_percent < 100:
        command.extend(['-resize', f'{resize_percent}%'])
    command.extend(['-quality', str(int(quality))])
    if target_format.strip().lower() in {'jpg', 'jpeg'}:
        background = map_jpg_background_option(jpg_background)
        command.extend(['-background', background, '-alpha', 'remove', '-alpha', 'off'])
    elif preserve_alpha:
        command.extend(['-alpha', 'on'])
    command.append(str(output_path))
    return command


def run_magick_command(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or 'ImageMagick 转换失败'
        raise ImageConvertError(message)


def compress_to_target_size(
    input_path: Path,
    output_path: Path,
    target_format: str,
    start_quality: int,
    preserve_alpha: bool,
    jpg_background: str,
    target_size_kb: float,
) -> Path:
    target_bytes = int(target_size_kb * 1024)
    for quality, resize_percent in plan_target_attempts(start_quality):
        command = build_magick_command(
            input_path=input_path,
            output_path=output_path,
            target_format=target_format,
            quality=quality,
            preserve_alpha=preserve_alpha,
            jpg_background=jpg_background,
            resize_percent=resize_percent,
        )
        run_magick_command(command)
        if output_path.exists() and output_path.stat().st_size <= target_bytes:
            return output_path
    raise ImageConvertError('未能压缩到目标大小，请调大目标体积或降低图片要求')


def convert_image(
    input_path: Path,
    output_dir: Path,
    target_format: str,
    quality: int,
    preserve_alpha: bool,
    jpg_background: str,
    target_size_kb: float | None = None,
) -> Path:
    available, message = probe_imagemagick()
    if not available:
        raise ImageConvertError(message)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = build_output_path(input_path, output_dir, target_format)
    if target_size_kb is not None:
        return compress_to_target_size(
            input_path=input_path,
            output_path=output_path,
            target_format=target_format,
            start_quality=quality,
            preserve_alpha=preserve_alpha,
            jpg_background=jpg_background,
            target_size_kb=target_size_kb,
        )
    command = build_magick_command(
        input_path=input_path,
        output_path=output_path,
        target_format=target_format,
        quality=quality,
        preserve_alpha=preserve_alpha,
        jpg_background=jpg_background,
        resize_percent=None,
    )
    run_magick_command(command)
    return output_path
