from __future__ import annotations

from typing import Any, Callable
from ..core.logger import get_logger

logger = get_logger(__name__)


class Signal:
    """信号基类"""

    def __init__(self, name: str):
        self.name = name
        self._callbacks: list[Callable] = []

    def connect(self, callback: Callable):
        """连接回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def disconnect(self, callback: Callable):
        """断开回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit(self, *args, **kwargs):
        """发射信号"""
        for callback in self._callbacks[:]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"信号 {self.name} 回调执行失败: {e}")

    def clear(self):
        """清空所有回调"""
        self._callbacks.clear()

    def __len__(self):
        return len(self._callbacks)


class TaskSignals:
    """任务信号集"""

    def __init__(self):
        # 任务开始信号
        self.task_started = Signal("task_started")

        # 任务进度信号
        self.task_progress = Signal("task_progress")

        # 任务完成信号
        self.task_completed = Signal("task_completed")

        # 任务失败信号
        self.task_failed = Signal("task_failed")

        # 任务取消信号
        self.task_cancelled = Signal("task_cancelled")

        # 任务结束信号（无论成功、失败或取消）
        self.task_finished = Signal("task_finished")

    def connect_all(self, callbacks: dict[str, Callable]):
        """连接所有信号"""
        signal_map = {
            'started': self.task_started,
            'progress': self.task_progress,
            'completed': self.task_completed,
            'failed': self.task_failed,
            'cancelled': self.task_cancelled,
            'finished': self.task_finished
        }

        for event_name, callback in callbacks.items():
            if event_name in signal_map:
                signal_map[event_name].connect(callback)

    def disconnect_all(self):
        """断开所有信号"""
        self.task_started.clear()
        self.task_progress.clear()
        self.task_completed.clear()
        self.task_failed.clear()
        self.task_cancelled.clear()
        self.task_finished.clear()
