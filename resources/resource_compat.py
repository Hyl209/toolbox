"""资源兼容层 — 安全的资源路径操作工具"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def _get_base_path() -> Path:
    """获取基础路径（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def _resource_path(*path_parts: str) -> Path:
    """获取资源文件路径"""
    return _get_base_path().joinpath('resources', *path_parts)


def get_resource_path_safe(*path_parts: str) -> Optional[Path]:
    """安全获取资源路径，不存在返回 None"""
    path = _resource_path(*path_parts)
    return path if path.exists() else None


def ensure_resource_dir(*path_parts: str) -> Path:
    """确保资源目录存在，返回路径"""
    path = _resource_path(*path_parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_resources_by_type(extension: str) -> list[Path]:
    """按扩展名列出资源目录下的文件

    Args:
        extension: 文件扩展名，如 '.png' 或 'png'

    Returns:
        匹配的文件路径列表
    """
    if not extension.startswith('.'):
        extension = f'.{extension}'
    base = _resource_path()
    if not base.exists():
        return []
    return sorted(p for p in base.rglob(f'*{extension}') if p.is_file())
