from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional
from ..toolbox_app.core.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str | Path = None, max_size_mb: int = 100):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._cache_index: dict[str, dict[str, Any]] = {}
        self._load_index()

    def _load_index(self):
        """加载缓存索引"""
        index_file = self.cache_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self._cache_index = json.load(f)
            except Exception as e:
                logger.error(f"加载缓存索引失败: {e}")
                self._cache_index = {}

    def _save_index(self):
        """保存缓存索引"""
        index_file = self.cache_dir / "index.json"
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存索引失败: {e}")

    def _generate_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.cache"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        cache_key = self._generate_key(key)

        if cache_key not in self._cache_index:
            return None

        cache_info = self._cache_index[cache_key]

        # 检查是否过期
        if cache_info.get('expires_at') and time.time() > cache_info['expires_at']:
            self.delete(key)
            return None

        # 读取缓存文件
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            self._cache_index.pop(cache_key, None)
            self._save_index()
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新访问时间
            cache_info['last_accessed'] = time.time()
            self._save_index()

            return data.get('value')

        except Exception as e:
            logger.error(f"读取缓存失败 {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = None):
        """设置缓存"""
        cache_key = self._generate_key(key)

        # 准备缓存数据
        cache_data = {
            'value': value,
            'created_at': time.time(),
            'key': key
        }

        # 写入缓存文件
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            # 更新索引
            self._cache_index[cache_key] = {
                'key': key,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'expires_at': time.time() + ttl_seconds if ttl_seconds else None,
                'size': cache_path.stat().st_size
            }

            self._save_index()

            # 检查缓存大小
            self._cleanup_if_needed()

            logger.debug(f"设置缓存: {key}")

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")

    def delete(self, key: str) -> bool:
        """删除缓存"""
        cache_key = self._generate_key(key)

        if cache_key not in self._cache_index:
            return False

        # 删除缓存文件
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception as e:
                logger.error(f"删除缓存文件失败 {cache_path}: {e}")

        # 从索引中删除
        del self._cache_index[cache_key]
        self._save_index()

        logger.debug(f"删除缓存: {key}")
        return True

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        cache_key = self._generate_key(key)

        if cache_key not in self._cache_index:
            return False

        cache_info = self._cache_index[cache_key]

        # 检查是否过期
        if cache_info.get('expires_at') and time.time() > cache_info['expires_at']:
            self.delete(key)
            return False

        # 检查文件是否存在
        cache_path = self._get_cache_path(cache_key)
        return cache_path.exists()

    def clear(self):
        """清空所有缓存"""
        try:
            for cache_path in self.cache_dir.glob("*.cache"):
                cache_path.unlink()

            self._cache_index.clear()
            self._save_index()

            logger.info("清空所有缓存")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")

    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for cache_key, cache_info in self._cache_index.items():
            if cache_info.get('expires_at') and current_time > cache_info['expires_at']:
                expired_keys.append(cache_key)

        for cache_key in expired_keys:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            del self._cache_index[cache_key]

        if expired_keys:
            self._save_index()
            logger.info(f"清理 {len(expired_keys)} 个过期缓存")

    def _cleanup_if_needed(self):
        """如果需要，清理缓存"""
        total_size = sum(info.get('size', 0) for info in self._cache_index.values())

        if total_size <= self.max_size_bytes:
            return

        # 按最后访问时间排序
        sorted_items = sorted(
            self._cache_index.items(),
            key=lambda x: x[1].get('last_accessed', 0)
        )

        # 删除最旧的缓存
        for cache_key, cache_info in sorted_items:
            if total_size <= self.max_size_bytes:
                break

            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()

            total_size -= cache_info.get('size', 0)
            del self._cache_index[cache_key]

        self._save_index()
        logger.info("缓存大小超限，已清理")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_size = sum(info.get('size', 0) for info in self._cache_index.values())

        return {
            'count': len(self._cache_index),
            'total_size': total_size,
            'max_size': self.max_size_bytes,
            'usage_percent': (total_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0
        }

    def get_keys(self) -> list[str]:
        """获取所有缓存键"""
        return [info.get('key', '') for info in self._cache_index.values()]

    def get_size(self, key: str) -> int:
        """获取缓存大小"""
        cache_key = self._generate_key(key)
        if cache_key in self._cache_index:
            return self._cache_index[cache_key].get('size', 0)
        return 0

    def get_total_size(self) -> int:
        """获取缓存总大小"""
        return sum(info.get('size', 0) for info in self._cache_index.values())


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_dir: str | Path = None, max_size_mb: int = 100) -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, max_size_mb)
    return _cache_manager
