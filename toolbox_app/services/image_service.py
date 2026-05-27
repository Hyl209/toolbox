from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils

logger = get_logger(__name__)


class ImageService:
    """图片服务"""

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        try:
            from PIL import Image
            self._initialized = True
            logger.info("图片服务初始化成功")
        except ImportError:
            raise ServiceError("Pillow 未安装", "ImageService")

    def convert_format(self, input_path: str | Path, output_path: str | Path,
                       format: str = None) -> bool:
        """转换图片格式"""
        self.initialize()

        try:
            from PIL import Image
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "ImageService")

            file_utils.ensure_dir(output_path.parent)

            # 如果未指定格式，从输出路径推断
            if format is None:
                format = output_path.suffix.upper().lstrip('.')

            # 特殊处理 ICO 格式
            if format == 'ICO':
                img = Image.open(input_path)
                img.save(str(output_path), format='ICO', sizes=[(256, 256)])
            else:
                img = Image.open(input_path)
                img.save(str(output_path), format=format)

            logger.info(f"图片格式转换完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"图片格式转换失败: {e}")
            raise ServiceError(f"图片格式转换失败: {e}", "ImageService")

    def resize_image(self, input_path: str | Path, output_path: str | Path,
                     size: Tuple[int, int], maintain_aspect: bool = True) -> bool:
        """调整图片大小"""
        self.initialize()

        try:
            from PIL import Image
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "ImageService")

            file_utils.ensure_dir(output_path.parent)

            img = Image.open(input_path)

            if maintain_aspect:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            else:
                img = img.resize(size, Image.Resampling.LANCZOS)

            img.save(str(output_path))

            logger.info(f"图片大小调整完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"图片大小调整失败: {e}")
            raise ServiceError(f"图片大小调整失败: {e}", "ImageService")

    def rotate_image(self, input_path: str | Path, output_path: str | Path,
                     angle: float) -> bool:
        """旋转图片"""
        self.initialize()

        try:
            from PIL import Image
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "ImageService")

            file_utils.ensure_dir(output_path.parent)

            img = Image.open(input_path)
            rotated = img.rotate(angle, expand=True)
            rotated.save(str(output_path))

            logger.info(f"图片旋转完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"图片旋转失败: {e}")
            raise ServiceError(f"图片旋转失败: {e}", "ImageService")

    def crop_image(self, input_path: str | Path, output_path: str | Path,
                   box: Tuple[int, int, int, int]) -> bool:
        """裁剪图片"""
        self.initialize()

        try:
            from PIL import Image
            input_path = Path(input_path)
            output_path = Path(output_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "ImageService")

            file_utils.ensure_dir(output_path.parent)

            img = Image.open(input_path)
            cropped = img.crop(box)
            cropped.save(str(output_path))

            logger.info(f"图片裁剪完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"图片裁剪失败: {e}")
            raise ServiceError(f"图片裁剪失败: {e}", "ImageService")

    def get_image_info(self, input_path: str | Path) -> Optional[dict]:
        """获取图片信息"""
        self.initialize()

        try:
            from PIL import Image
            input_path = Path(input_path)

            if not input_path.exists():
                raise ServiceError(f"文件不存在: {input_path}", "ImageService")

            img = Image.open(input_path)
            info = {
                'path': str(input_path),
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size': input_path.stat().st_size
            }

            return info

        except Exception as e:
            logger.error(f"获取图片信息失败: {e}")
            return None

    def create_thumbnail(self, input_path: str | Path, output_path: str | Path,
                         size: Tuple[int, int] = (128, 128)) -> bool:
        """创建缩略图"""
        return self.resize_image(input_path, output_path, size, maintain_aspect=True)
