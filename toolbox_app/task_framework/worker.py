from __future__ import annotations

import threading
from typing import Optional
from .task import Task, TaskStatus
from .signals import TaskSignals
from ..core.logger import get_logger
from ..core.exceptions import TaskError

logger = get_logger(__name__)


class TaskWorker(threading.Thread):
    """任务工作线程"""

    def __init__(self, task: Task, signals: TaskSignals = None):
        super().__init__(daemon=True)
        self.task = task
        self.signals = signals or TaskSignals()
        self._exception: Optional[Exception] = None

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    def run(self):
        """执行任务"""
        try:
            logger.info("Worker 开始执行任务: %s", self.task)
            self.signals.task_started.emit(self.task)

            result = self.task.run()

            if self.task.is_completed:
                logger.info("Worker 任务完成: %s", self.task)
                self.signals.task_completed.emit(self.task, result)
            elif self.task.is_cancelled:
                logger.info("Worker 任务取消: %s", self.task)
                self.signals.task_cancelled.emit(self.task)

        except TaskError as e:
            self._exception = e
            logger.error("Worker 任务失败: %s - %s", self.task, e)
            self.signals.task_failed.emit(self.task, e)

        except Exception as e:
            self._exception = TaskError(f"未预期的错误: {e}", self.task.task_id)
            logger.error("Worker 未预期错误: %s - %s", self.task, e)
            self.signals.task_failed.emit(self.task, self._exception)

        finally:
            logger.info("Worker 结束: %s", self.task)
            self.signals.task_finished.emit(self.task)
            # 释放引用，防止长时间运行的应用中内存泄漏
            self.task = None
            self._exception = None
            self.signals = None

    def cancel(self):
        """取消任务"""
        self.task.cancel()
        logger.info("Worker 收到取消指令: %s", self.task)

    def pause(self):
        """暂停任务"""
        self.task.pause()
        logger.info("Worker 收到暂停指令: %s", self.task)

    def resume(self):
        """恢复任务"""
        self.task.resume()
        logger.info("Worker 收到恢复指令: %s", self.task)
