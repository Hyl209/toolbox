from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils

logger = get_logger(__name__)


class VideoService:
    """视频服务"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._initialized = False

    def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        try:
            # 检查 ffmpeg 是否可用
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self._initialized = True
                logger.info("视频服务初始化成功")
            else:
                raise ServiceError("ffmpeg 不可用", "VideoService")
        except FileNotFoundError:
            raise ServiceError("ffmpeg 未找到", "VideoService")

    def convert_video(self, input_path: str | Path, output_path: str | Path,
                      codec: str = None, resolution: str = None,
                      bitrate: str = None) -> bool:
        """转换视频格式"""
        self.initialize()

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "VideoService")

            file_utils.ensure_dir(output_path.parent)

            cmd = [self.ffmpeg_path, "-i", str(input_path), "-y"]

            if codec:
                cmd.extend(["-c:v", codec])
            if resolution:
                cmd.extend(["-s", resolution])
            if bitrate:
                cmd.extend(["-b:v", bitrate])

            cmd.append(str(output_path))

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise ServiceError(f"视频转换失败: {result.stderr}", "VideoService")

            logger.info(f"视频转换完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"视频转换失败: {e}")
            raise ServiceError(f"视频转换失败: {e}", "VideoService")

    def extract_audio(self, input_path: str | Path, output_path: str | Path,
                      format: str = "mp3") -> bool:
        """提取音频"""
        self.initialize()

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "VideoService")

            file_utils.ensure_dir(output_path.parent)

            cmd = [
                self.ffmpeg_path,
                "-i", str(input_path),
                "-vn",  # 不包含视频
                "-acodec", "libmp3lame" if format == "mp3" else "copy",
                "-y",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise ServiceError(f"音频提取失败: {result.stderr}", "VideoService")

            logger.info(f"音频提取完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            raise ServiceError(f"音频提取失败: {e}", "VideoService")

    def get_video_info(self, input_path: str | Path) -> Optional[dict]:
        """获取视频信息"""
        self.initialize()

        try:
            input_path = Path(input_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "VideoService")

            cmd = [
                self.ffmpeg_path,
                "-i", str(input_path),
                "-hide_banner"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # 解析输出信息
            info = {
                'path': str(input_path),
                'size': input_path.stat().st_size,
                'format': input_path.suffix.lower()
            }

            # 从 stderr 中提取信息
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    # 提取时长
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    info['duration'] = duration_str
                elif 'Video:' in line:
                    # 提取视频信息
                    info['video_codec'] = line.split('Video:')[1].split('(')[0].strip()
                elif 'Audio:' in line:
                    # 提取音频信息
                    info['audio_codec'] = line.split('Audio:')[1].split('(')[0].strip()

            return info

        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return None

    def compress_video(self, input_path: str | Path, output_path: str | Path,
                       quality: int = 23) -> bool:
        """压缩视频"""
        self.initialize()

        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "VideoService")

            file_utils.ensure_dir(output_path.parent)

            cmd = [
                self.ffmpeg_path,
                "-i", str(input_path),
                "-c:v", "libx264",
                "-crf", str(quality),
                "-preset", "medium",
                "-y",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise ServiceError(f"视频压缩失败: {result.stderr}", "VideoService")

            logger.info(f"视频压缩完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"视频压缩失败: {e}")
            raise ServiceError(f"视频压缩失败: {e}", "VideoService")
