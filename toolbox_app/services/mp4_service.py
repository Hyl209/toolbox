"""MP4→MP3 转换服务 — 包装 mp4-mp3/converter.py"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)


class MP4Service:
    """MP4 转 MP3 服务"""

    def __init__(self):
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from ..loaders import load_module_once
            converter_path = Path(__file__).resolve().parent.parent.parent / 'mp4-mp3' / 'converter.py'
            self._converter = load_module_once('mp4_converter_module', converter_path)
        return self._converter

    def check_ffmpeg(self) -> tuple[bool, str]:
        """检查 ffmpeg 是否可用"""
        try:
            conv = self._get_converter()
            conv.ensure_ffmpeg()
            return True, 'ffmpeg 可用'
        except Exception as e:
            return False, str(e)

    def convert(self, input_path: str | Path, output_path: str | Path | None = None,
                overwrite: bool = True) -> Path:
        """转换单个 MP4 为 MP3"""
        try:
            conv = self._get_converter()
            return conv.convert_mp4_to_mp3(input_path, output_path, overwrite)
        except Exception as e:
            raise ServiceError(f'MP4 转换失败: {e}', 'MP4Service')

    def batch_convert(self, files: list[Path], output_dir: str | Path,
                      overwrite: bool = True) -> list[tuple[Path, Path]]:
        """批量转换，返回 (源文件, 输出文件) 列对"""
        results = []
        for src in files:
            out = self.convert(src, Path(output_dir) / f'{src.stem}.mp3', overwrite)
            results.append((src, out))
        return results
