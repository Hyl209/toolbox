from __future__ import annotations

from pathlib import Path
from typing import Optional
from toolbox_app.core.logger import get_logger
from toolbox_app.core.exceptions import ResourceError

logger = get_logger(__name__)


class ResourceValidator:
    """资源验证器"""

    def __init__(self, resources_dir: str | Path):
        self.resources_dir = Path(resources_dir)

    def validate_file(self, *path_parts: str) -> bool:
        """验证文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not file_path.exists():
            logger.error("文件不存在: %s", file_path)
            return False

        if not file_path.is_file():
            logger.error("不是文件: %s", file_path)
            return False

        return True

    def validate_directory(self, *path_parts: str) -> bool:
        """验证目录"""
        dir_path = self.resources_dir.joinpath(*path_parts)

        if not dir_path.exists():
            logger.error("目录不存在: %s", dir_path)
            return False

        if not dir_path.is_dir():
            logger.error("不是目录: %s", dir_path)
            return False

        return True

    def validate_readable(self, *path_parts: str) -> bool:
        """验证文件是否可读"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        try:
            with open(file_path, 'r') as f:
                f.read(1)
            return True
        except Exception as e:
            logger.error("文件不可读 %s: %s", file_path, e)
            return False

    def validate_writable(self, *path_parts: str) -> bool:
        """验证文件是否可写"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not file_path.exists():
            # 检查父目录是否可写
            parent_dir = file_path.parent
            if not parent_dir.exists():
                return False
            try:
                test_file = parent_dir / "test_write.tmp"
                test_file.touch()
                test_file.unlink()
                return True
            except Exception:
                return False

        try:
            with open(file_path, 'a') as f:
                f.write("")
            return True
        except Exception as e:
            logger.error("文件不可写 %s: %s", file_path, e)
            return False

    def validate_image(self, *path_parts: str) -> bool:
        """验证图片文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.error("不是有效的图片格式: %s", file_path)
            return False

        try:
            from PIL import Image
            img = Image.open(file_path)
            img.verify()
            return True
        except ImportError:
            logger.warning("Pillow 未安装，跳过图片验证")
            return True
        except Exception as e:
            logger.error("图片验证失败 %s: %s", file_path, e)
            return False

    def validate_json(self, *path_parts: str) -> bool:
        """验证 JSON 文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_readable(*path_parts):
            return False

        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except Exception as e:
            logger.error("JSON 验证失败 %s: %s", file_path, e)
            return False

    def validate_manifest(self, *path_parts: str) -> bool:
        """验证 manifest 文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_json(*path_parts):
            return False

        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            required_fields = ['name', 'version', 'description', 'author']
            for field in required_fields:
                if field not in manifest:
                    logger.error("manifest 缺少必需字段: %s", field)
                    return False

            return True
        except Exception as e:
            logger.error("manifest 验证失败 %s: %s", file_path, e)
            return False

    def validate_executable(self, *path_parts: str) -> bool:
        """验证可执行文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        valid_extensions = {'.exe', '.bat', '.cmd', '.sh', '.ps1'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.error("不是有效的可执行文件格式: %s", file_path)
            return False

        return True

    def validate_audio(self, *path_parts: str) -> bool:
        """验证音频文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        valid_extensions = {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.error("不是有效的音频格式: %s", file_path)
            return False

        return True

    def validate_video(self, *path_parts: str) -> bool:
        """验证视频文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        valid_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.error("不是有效的视频格式: %s", file_path)
            return False

        return True

    def validate_font(self, *path_parts: str) -> bool:
        """验证字体文件"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not self.validate_file(*path_parts):
            return False

        valid_extensions = {'.ttf', '.otf', '.woff', '.woff2', '.eot'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.error("不是有效的字体格式: %s", file_path)
            return False

        return True

    def get_file_info(self, *path_parts: str) -> Optional[dict]:
        """获取文件信息"""
        file_path = self.resources_dir.joinpath(*path_parts)

        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'extension': file_path.suffix.lower(),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
        except Exception as e:
            logger.error("获取文件信息失败 %s: %s", file_path, e)
            return None

    def validate_all(self) -> dict[str, bool]:
        """验证所有资源"""
        results = {}

        # 检查资源目录
        results['resources_dir'] = self.validate_directory()

        # 检查必需文件
        required_files = ['logo.png', 'logo.ico']
        for file_name in required_files:
            results[file_name] = self.validate_file(file_name)

        # 检查子目录
        subdirs = ['images', 'icons', 'fonts', 'sounds']
        for subdir in subdirs:
            results[f"{subdir}/"] = self.validate_directory(subdir)

        return results


# 全局资源验证器实例
_resource_validator: Optional[ResourceValidator] = None


def get_resource_validator(resources_dir: str | Path = None) -> ResourceValidator:
    """获取全局资源验证器实例"""
    global _resource_validator
    if _resource_validator is None:
        if resources_dir is None:
            resources_dir = Path(__file__).parent
        _resource_validator = ResourceValidator(resources_dir)
    return _resource_validator
