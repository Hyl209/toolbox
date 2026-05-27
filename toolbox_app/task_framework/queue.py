from __future__ import annotations

import threading
from collections import deque
from typing import Optional
from .task import Task, TaskStatus
from .worker import TaskWorker
from .signals import TaskSignals
from ..core.logger import get_logger
from ..core.exceptions import TaskError

logger = get_logger(__name__)


class TaskQueue:
    """任务队列"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self._queue: deque[Task] = deque()
        self._workers: dict[str, TaskWorker] = {}
        self._lock = threading.Lock()
        self._signals = TaskSignals()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def active_workers(self) -> int:
        return len(self._workers)

    def add_task(self, task: Task) -> TaskWorker:
        """添加任务到队列"""
        with self._lock:
            if task.task_id in self._workers:
                raise TaskError(f"任务已存在: {task.task_id}", task.task_id)

            # 如果有空闲 worker，立即执行
            if len(self._workers) < self.max_workers:
                return self._start_task(task)

            # 否则加入队列
            self._queue.append(task)
            logger.info(f"任务加入队列: {task} (队列长度: {self.queue_size})")
            return None

    def _start_task(self, task: Task) -> TaskWorker:
        """启动任务"""
        worker = TaskWorker(task, self._signals)
        self._workers[task.task_id] = worker

        # 连接完成信号以清理 worker
        def on_finished(t: Task):
            self._remove_worker(t.task_id)
            self._process_queue()

        self._signals.task_finished.connect(on_finished)

        worker.start()
        logger.info(f"任务开始执行: {task} (活跃 workers: {self.active_workers})")
        return worker

    def _remove_worker(self, task_id: str):
        """移除 worker"""
        with self._lock:
            self._workers.pop(task_id, None)

    def _process_queue(self):
        """处理队列中的任务"""
        with self._lock:
            while self._queue and len(self._workers) < self.max_workers:
                task = self._queue.popleft()
                self._start_task(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定任务"""
        # 检查正在运行的任务
        worker = self._workers.get(task_id)
        if worker:
            return worker.task

        # 检查队列中的任务
        for task in self._queue:
            if task.task_id == task_id:
                return task

        return None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 检查正在运行的任务
        worker = self._workers.get(task_id)
        if worker:
            worker.cancel()
            return True

        # 检查队列中的任务
        for task in self._queue:
            if task.task_id == task_id:
                task.cancel()
                self._queue.remove(task)
                return True

        return False

    def cancel_all(self):
        """取消所有任务"""
        with self._lock:
            # 取消正在运行的任务
            for worker in self._workers.values():
                worker.cancel()

            # 取消队列中的任务
            for task in self._queue:
                task.cancel()

            self._queue.clear()

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        worker = self._workers.get(task_id)
        if worker:
            worker.pause()
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        worker = self._workers.get(task_id)
        if worker:
            worker.resume()
            return True
        return False

    def get_status(self) -> dict:
        """获取队列状态"""
        return {
            'queue_size': self.queue_size,
            'active_workers': self.active_workers,
            'max_workers': self.max_workers,
            'is_running': self.is_running
        }

    def get_all_tasks(self) -> list[Task]:
        """获取所有任务"""
        tasks = []
        # 正在运行的任务
        for worker in self._workers.values():
            tasks.append(worker.task)

        # 队列中的任务
        tasks.extend(self._queue)

        return tasks

    def clear_finished(self):
        """清理已完成的任务"""
        with self._lock:
            finished_tasks = [
                task_id for task_id, worker in self._workers.items()
                if worker.task.is_finished
            ]
            for task_id in finished_tasks:
                del self._workers[task_id]

    @property
    def signals(self) -> TaskSignals:
        """获取信号集"""
        return self._signals
