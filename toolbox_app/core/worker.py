from __future__ import annotations

from typing import Any, Callable, Optional
from .logger import get_logger
from .exceptions import TaskError

logger = get_logger(__name__)


class Worker:
    """后台任务 Worker 抽象"""

    def __init__(self, task_id: str = None):
        self.task_id = task_id or id(self)
        self._is_running = False
        self._is_cancelled = False
        self._progress = 0
        self._result: Any = None
        self._error: Optional[Exception] = None
        self._callbacks: dict[str, list[Callable]] = {
            'progress': [],
            'completed': [],
            'error': [],
            'cancelled': []
        }

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def progress(self) -> int:
        return self._progress

    @property
    def result(self) -> Any:
        return self._result

    @property
    def error(self) -> Optional[Exception]:
        return self._error

    def on_progress(self, callback: Callable[[int], None]):
        """注册进度回调"""
        self._callbacks['progress'].append(callback)

    def on_completed(self, callback: Callable[[Any], None]):
        """注册完成回调"""
        self._callbacks['completed'].append(callback)

    def on_error(self, callback: Callable[[Exception], None]):
        """注册错误回调"""
        self._callbacks['error'].append(callback)

    def on_cancelled(self, callback: Callable[[], None]):
        """注册取消回调"""
        self._callbacks['cancelled'].append(callback)

    def clear_callbacks(self):
        """清空所有回调，释放引用"""
        for key in self._callbacks:
            self._callbacks[key].clear()

    def _emit_progress(self, progress: int):
        """触发进度回调"""
        self._progress = progress
        for callback in self._callbacks['progress']:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    def _emit_completed(self, result: Any):
        """触发完成回调"""
        self._result = result
        for callback in self._callbacks['completed']:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"完成回调执行失败: {e}")

    def _emit_error(self, error: Exception):
        """触发错误回调"""
        self._error = error
        for callback in self._callbacks['error']:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}")

    def _emit_cancelled(self):
        """触发取消回调"""
        for callback in self._callbacks['cancelled']:
            try:
                callback()
            except Exception as e:
                logger.error(f"取消回调执行失败: {e}")

    def cancel(self):
        """取消任务"""
        self._is_cancelled = True
        self._emit_cancelled()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行任务"""
        if self._is_running:
            raise TaskError("任务已在运行中", self.task_id)

        self._is_running = True
        self._is_cancelled = False
        self._progress = 0
        self._result = None
        self._error = None

        try:
            result = func(*args, **kwargs)
            if not self._is_cancelled:
                self._emit_completed(result)
            return result
        except Exception as e:
            self._emit_error(e)
            raise
        finally:
            self._is_running = False
            self.clear_callbacks()

    def execute_async(self, func: Callable, *args, **kwargs):
        """异步执行任务"""
        import threading

        def wrapper():
            try:
                self.execute(func, *args, **kwargs)
            except Exception as e:
                logger.error(f"异步任务执行失败: {e}")

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        return thread
