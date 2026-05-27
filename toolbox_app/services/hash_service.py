"""文件哈希服务 — 提供统一的文件哈希计算接口"""
from __future__ import annotations

import hashlib
from pathlib import Path
from ..core.logger import get_logger
from ..core.exceptions import ServiceError

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1MB


class HashService:
    """文件哈希计算服务"""

    @staticmethod
    def compute_hash(file_path: str | Path, algorithm: str = 'md5') -> str:
        """计算文件哈希值"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ServiceError(f'文件不存在: {file_path}', 'HashService')

            h = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f'哈希计算失败: {e}', 'HashService')

    @staticmethod
    def compute_md5(file_path: str | Path) -> str:
        """计算 MD5 哈希"""
        return HashService.compute_hash(file_path, 'md5')

    @staticmethod
    def compute_sha256(file_path: str | Path) -> str:
        """计算 SHA256 哈希"""
        return HashService.compute_hash(file_path, 'sha256')

    @staticmethod
    def compute_quick_hash(file_path: str | Path) -> str:
        """快速哈希（只读取首尾各 1MB）"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ServiceError(f'文件不存在: {file_path}', 'HashService')

            file_size = file_path.stat().st_size
            h = hashlib.md5()
            h.update(file_size.to_bytes(8, 'big'))

            with open(file_path, 'rb') as f:
                head = f.read(CHUNK_SIZE)
                h.update(head)
                if file_size > CHUNK_SIZE:
                    f.seek(max(0, file_size - CHUNK_SIZE))
                    tail = f.read(CHUNK_SIZE)
                    h.update(tail)

            return h.hexdigest()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f'快速哈希计算失败: {e}', 'HashService')

    @staticmethod
    def verify_hash(file_path: str | Path, expected_hash: str, algorithm: str = 'md5') -> bool:
        """验证文件哈希"""
        actual = HashService.compute_hash(file_path, algorithm)
        return actual == expected_hash
