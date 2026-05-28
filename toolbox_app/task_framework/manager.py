from __future__ import annotations

from typing import Any, Callable, Optional
from .task import Task, TaskStatus
from .queue import TaskQueue
from .signals import TaskSignals
from ..core.logger import get_logger
from ..core.exceptions import TaskError

logger = get_logger(__name__)

_MAX_TASK_HISTORY = 200


class SimpleTask(Task):
    """简单任务实现"""

    def __init__(self, func: Callable, *args, name: str = None, **kwargs):
        super().__init__(name)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def execute(self) -> Any:
        """执行任务"""
        return self._func(*self._args, **self._kwargs)


class TaskManager:
    """任务管理器"""

    def __init__(self, max_workers: int = 5):
        self._queue = TaskQueue(max_workers)
        self._task_history: dict[str, Task] = {}

    @property
    def queue(self) -> TaskQueue:
        return self._queue

    @property
    def signals(self) -> TaskSignals:
        return self._queue.signals

    def _evict_old_history(self):
        """清理已完成的旧任务历史，防止无限增长"""
        if len(self._task_history) <= _MAX_TASK_HISTORY:
            return
        finished = [tid for tid, t in self._task_history.items() if t.is_finished]
        # Remove oldest half of finished tasks
        for tid in finished[:len(finished) // 2]:
            self._task_history.pop(tid, None)

    def submit(self, func: Callable, *args, name: str = None, **kwargs) -> Task:
        """提交任务"""
        task = SimpleTask(func, *args, name=name, **kwargs)
        self._evict_old_history()
        self._task_history[task.task_id] = task
        self._queue.add_task(task)
        return task

    def submit_task(self, task: Task) -> Task:
        """提交自定义任务"""
        self._evict_old_history()
        self._task_history[task.task_id] = task
        self._queue.add_task(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        # 先检查历史记录
        task = self._task_history.get(task_id)
        if task:
            return task

        # 再检查队列
        return self._queue.get_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self._queue.cancel_task(task_id)

    def cancel_all(self):
        """取消所有任务"""
        self._queue.cancel_all()

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        return self._queue.pause_task(task_id)

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        return self._queue.resume_task(task_id)

    def get_status(self) -> dict:
        """获取状态"""
        queue_status = self._queue.get_status()
        return {
            **queue_status,
            'total_tasks': len(self._task_history),
            'completed_tasks': sum(1 for t in self._task_history.values() if t.is_completed),
            'failed_tasks': sum(1 for t in self._task_history.values() if t.is_failed),
            'cancelled_tasks': sum(1 for t in self._task_history.values() if t.is_cancelled)
        }

    def get_running_tasks(self) -> list[Task]:
        """获取运行中的任务"""
        return [t for t in self._task_history.values() if t.is_running]

    def get_completed_tasks(self) -> list[Task]:
        """获取已完成的任务"""
        return [t for t in self._task_history.values() if t.is_completed]

    def get_failed_tasks(self) -> list[Task]:
        """获取失败的任务"""
        return [t for t in self._task_history.values() if t.is_failed]

    def clear_history(self):
        """清空历史记录"""
        self._task_history.clear()

    def cleanup(self):
        """清理已完成的任务"""
        self._queue.clear_finished()

    def wait_for_task(self, task_id: str, timeout: float = None) -> Any:
        """等待任务完成"""
        task = self.get_task(task_id)
        if task is None:
            raise TaskError(f"任务不存在: {task_id}", task_id)

        if task.is_finished:
            if task.is_failed:
                raise task.error
            return task.result

        # 简单的等待实现
        import time
        start_time = time.time()
        while not task.is_finished:
            if timeout and (time.time() - start_time) > timeout:
                raise TaskError(f"等待任务超时: {task_id}", task_id)
            time.sleep(0.1)

        if task.is_failed:
            raise task.error
        return task.result

    def on_task_started(self, callback: Callable[[Task], None]):
        """注册任务开始回调"""
        self.signals.task_started.connect(callback)

    def on_task_completed(self, callback: Callable[[Task, Any], None]):
        """注册任务完成回调"""
        self.signals.task_completed.connect(callback)

    def on_task_failed(self, callback: Callable[[Task, Exception], None]):
        """注册任务失败回调"""
        self.signals.task_failed.connect(callback)

    def on_task_cancelled(self, callback: Callable[[Task], None]):
        """注册任务取消回调"""
        self.signals.task_cancelled.connect(callback)

    def on_task_progress(self, callback: Callable[[Task, int], None]):
        """注册任务进度回调"""
        self.signals.task_progress.connect(callback)


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None


def get_task_manager(max_workers: int = 5) -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_workers)
    return _task_manager
