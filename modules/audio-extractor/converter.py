from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class ConvertError(Exception):
    pass


def _get_default_output_dir():
    """Lazy import to avoid bare 'from config_store' at module level."""
    from config_store import get_default_output_dir
    return get_default_output_dir()


def ensure_ffmpeg() -> str:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise ConvertError('未检测到 ffmpeg，请先安装并加入 PATH。')
    return ffmpeg


def resolve_output_path(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    src = Path(input_path).expanduser().resolve()
    if src.suffix.lower() != '.mp4':
        raise ConvertError('只支持 mp4 文件。')

    if output_path:
        out = Path(output_path).expanduser()
        if out.suffix.lower() != '.mp3':
            if out.exists() and out.is_dir():
                out = out / f'{src.stem}.mp3'
            elif str(out).endswith(('\\', '/')):
                out = out / f'{src.stem}.mp3'
            else:
                out = out.with_suffix('.mp3')
        return out.resolve()

    default_dir = _get_default_output_dir()
    if default_dir:
        return (default_dir / f'{src.stem}.mp3').resolve()

    return src.with_suffix('.mp3')


def convert_mp4_to_mp3(input_path: str | Path, output_path: str | Path | None = None, overwrite: bool = True) -> Path:
    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise ConvertError(f'输入文件不存在：{src}')
    if not src.is_file():
        raise ConvertError(f'输入路径不是文件：{src}')

    dst = resolve_output_path(src, output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = ensure_ffmpeg()
    command = [
        ffmpeg,
        '-y' if overwrite else '-n',
        '-i', str(src),
        '-vn',
        '-acodec', 'libmp3lame',
        '-q:a', '2',
        str(dst),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or 'ffmpeg 转换失败'
        raise ConvertError(message)
    return dst
