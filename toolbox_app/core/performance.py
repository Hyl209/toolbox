from __future__ import annotations

import time
import functools
from typing import Any, Callable
from .logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self._metrics: dict[str, list[float]] = {}
        self._start_times: dict[str, float] = {}

    def start_timer(self, name: str):
        """开始计时"""
        self._start_times[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """停止计时并返回耗时"""
        if name not in self._start_times:
            return 0.0

        elapsed = time.time() - self._start_times.pop(name)

        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(elapsed)

        return elapsed

    def get_average(self, name: str) -> float:
        """获取平均耗时"""
        if name not in self._metrics or not self._metrics[name]:
            return 0.0
        return sum(self._metrics[name]) / len(self._metrics[name])

    def get_min(self, name: str) -> float:
        """获取最小耗时"""
        if name not in self._metrics or not self._metrics[name]:
            return 0.0
        return min(self._metrics[name])

    def get_max(self, name: str) -> float:
        """获取最大耗时"""
        if name not in self._metrics or not self._metrics[name]:
            return 0.0
        return max(self._metrics[name])

    def get_total(self, name: str) -> float:
        """获取总耗时"""
        if name not in self._metrics:
            return 0.0
        return sum(self._metrics[name])

    def get_count(self, name: str) -> int:
        """获取调用次数"""
        if name not in self._metrics:
            return 0
        return len(self._metrics[name])

    def get_stats(self, name: str) -> dict[str, Any]:
        """获取统计信息"""
        if name not in self._metrics or not self._metrics[name]:
            return {}

        values = self._metrics[name]
        return {
            'count': len(values),
            'total': sum(values),
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有统计信息"""
        stats = {}
        for name in self._metrics:
            stats[name] = self.get_stats(name)
        return stats

    def reset(self, name: str = None):
        """重置统计"""
        if name:
            self._metrics.pop(name, None)
            self._start_times.pop(name, None)
        else:
            self._metrics.clear()
            self._start_times.clear()

    def log_stats(self):
        """记录统计信息"""
        stats = self.get_all_stats()
        for name, stat in stats.items():
            logger.info(f"性能统计 {name}: {stat}")


def timer(name: str = None):
    """计时装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer_name = name or func.__name__
            monitor = get_performance_monitor()

            monitor.start_timer(timer_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = monitor.stop_timer(timer_name)
                logger.debug(f"{timer_name} 耗时: {elapsed:.4f}秒")

        return wrapper
    return decorator


def async_timer(name: str = None):
    """异步计时装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            timer_name = name or func.__name__
            monitor = get_performance_monitor()

            monitor.start_timer(timer_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = monitor.stop_timer(timer_name)
                logger.debug(f"{timer_name} 耗时: {elapsed:.4f}秒")

        return wrapper
    return decorator


class MemoryMonitor:
    """内存监控器"""

    def __init__(self):
        self._snapshots: list[dict[str, Any]] = []

    def take_snapshot(self, label: str = None):
        """获取内存快照"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            snapshot = {
                'label': label or f"snapshot_{len(self._snapshots)}",
                'timestamp': time.time(),
                'rss': memory_info.rss,  # 物理内存
                'vms': memory_info.vms,  # 虚拟内存
                'percent': process.memory_percent()
            }

            self._snapshots.append(snapshot)
            return snapshot

        except ImportError:
            logger.warning("psutil 未安装，无法监控内存")
            return None

    def get_snapshots(self) -> list[dict[str, Any]]:
        """获取所有快照"""
        return self._snapshots.copy()

    def get_memory_usage(self) -> dict[str, Any]:
        """获取当前内存使用"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available
            }

        except ImportError:
            return {}

    def log_memory_usage(self, label: str = ""):
        """记录内存使用"""
        usage = self.get_memory_usage()
        if usage:
            logger.info(f"内存使用 {label}: RSS={usage['rss'] / 1024 / 1024:.2f}MB, "
                       f"VMS={usage['vms'] / 1024 / 1024:.2f}MB, "
                       f"使用率={usage['percent']:.1f}%")


# 全局性能监控器实例
_performance_monitor: PerformanceMonitor = None
_memory_monitor: MemoryMonitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控器实例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor
