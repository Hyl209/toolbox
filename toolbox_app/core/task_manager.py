from __future__ import annotations

from typing import Any, Callable, Optional
from .worker import Worker
from .logger import get_logger
from .exceptions import TaskError

logger = get_logger(__name__)


class TaskManager:
    """任务管理器"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._workers: dict[str, Worker] = {}
        self._task_queue: list[tuple[str, Callable, tuple, dict]] = []
        self._running_count = 0

    def create_worker(self, task_id: str = None) -> Worker:
        """创建新的 Worker"""
        if task_id and task_id in self._workers:
            raise TaskError(f"任务 ID 已存在: {task_id}", task_id)

        worker = Worker(task_id)
        self._workers[worker.task_id] = worker
        return worker

    def get_worker(self, task_id: str) -> Optional[Worker]:
        """获取指定 Worker"""
        return self._workers.get(task_id)

    def remove_worker(self, task_id: str) -> bool:
        """移除指定 Worker"""
        if task_id in self._workers:
            worker = self._workers[task_id]
            if worker.is_running:
                worker.cancel()
            del self._workers[task_id]
            return True
        return False

    def execute_task(self, task_id: str, func: Callable, *args, **kwargs) -> Worker:
        """执行任务"""
        worker = self.create_worker(task_id)

        if self._running_count >= self.max_concurrent:
            self._task_queue.append((task_id, func, args, kwargs))
            logger.info(f"任务 {task_id} 已加入队列，当前队列长度: {len(self._task_queue)}")
            return worker

        self._running_count += 1

        def wrapper():
            try:
                worker.execute(func, *args, **kwargs)
            finally:
                self._running_count -= 1
                self._process_queue()

        worker.execute_async(wrapper)
        return worker

    def _process_queue(self):
        """处理任务队列"""
        if not self._task_queue or self._running_count >= self.max_concurrent:
            return

        task_id, func, args, kwargs = self._task_queue.pop(0)
        self._running_count += 1

        worker = self.get_worker(task_id)
        if worker is None:
            worker = self.create_worker(task_id)

        def wrapper():
            try:
                worker.execute(func, *args, **kwargs)
            finally:
                self._running_count -= 1
                self._process_queue()

        worker.execute_async(wrapper)

    def cancel_all(self):
        """取消所有任务"""
        for worker in self._workers.values():
            if worker.is_running:
                worker.cancel()
        self._task_queue.clear()

    def get_running_tasks(self) -> list[str]:
        """获取所有运行中的任务 ID"""
        return [task_id for task_id, worker in self._workers.items() if worker.is_running]

    def get_queued_tasks(self) -> list[str]:
        """获取所有队列中的任务 ID"""
        return [task_id for task_id, _, _, _ in self._task_queue]

    def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态"""
        worker = self.get_worker(task_id)
        if worker is None:
            return None

        return {
            'task_id': task_id,
            'is_running': worker.is_running,
            'is_cancelled': worker.is_cancelled,
            'progress': worker.progress,
            'has_result': worker.result is not None,
            'has_error': worker.error is not None
        }

    def cleanup_completed(self):
        """清理已完成的任务"""
        completed_tasks = [
            task_id for task_id, worker in self._workers.items()
            if not worker.is_running and (worker.result is not None or worker.error is not None)
        ]
        for task_id in completed_tasks:
            del self._workers[task_id]


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None


def get_task_manager(max_concurrent: int = 5) -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_concurrent)
    return _task_manager
