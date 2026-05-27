from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def resource_path(*path_parts: str) -> Path:
    """获取资源文件路径（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包环境
        base_path = Path(sys.executable).parent
    else:
        # 开发环境
        base_path = Path(__file__).parent.parent

    return base_path.joinpath("resources", *path_parts)


def get_resource_path(*path_parts: str, must_exist: bool = False) -> Optional[Path]:
    """获取资源文件路径，可选择检查是否存在"""
    path = resource_path(*path_parts)
    if must_exist and not path.exists():
        return None
    return path


def temp_path(*path_parts: str) -> Path:
    """获取临时文件路径"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent

    return base_path.joinpath("temp", *path_parts)


def cache_path(*path_parts: str) -> Path:
    """获取缓存文件路径"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent

    return base_path.joinpath("cache", *path_parts)


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_base_path() -> Path:
    """获取基础路径"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def is_frozen() -> bool:
    """检查是否为打包环境"""
    return getattr(sys, 'frozen', False)


def get_executable_path() -> Path:
    """获取可执行文件路径"""
    return Path(sys.executable)


def get_script_path() -> Path:
    """获取脚本文件路径"""
    return Path(__file__).parent.parent


def normalize_path(path: str | Path) -> Path:
    """规范化路径"""
    return Path(path).resolve()


def relative_to_base(path: str | Path) -> Path:
    """获取相对于基础路径的路径"""
    base_path = get_base_path()
    try:
        return Path(path).relative_to(base_path)
    except ValueError:
        return Path(path)


def join_paths(*paths: str | Path) -> Path:
    """连接路径"""
    result = Path(paths[0])
    for path in paths[1:]:
        result = result / path
    return result


def get_file_extension(path: str | Path) -> str:
    """获取文件扩展名"""
    return Path(path).suffix.lower()


def get_file_name(path: str | Path) -> str:
    """获取文件名"""
    return Path(path).name


def get_file_stem(path: str | Path) -> str:
    """获取文件名（不含扩展名）"""
    return Path(path).stem


def get_parent_dir(path: str | Path) -> Path:
    """获取父目录"""
    return Path(path).parent


def is_absolute(path: str | Path) -> bool:
    """检查是否为绝对路径"""
    return Path(path).is_absolute()


def make_absolute(path: str | Path, base: str | Path = None) -> Path:
    """转换为绝对路径"""
    path = Path(path)
    if path.is_absolute():
        return path

    if base is None:
        base = get_base_path()

    return Path(base) / path


def get_unique_path(path: str | Path) -> Path:
    """获取唯一路径（避免冲突）"""
    path = Path(path)
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
