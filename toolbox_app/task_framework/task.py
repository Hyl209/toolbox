from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from ..core.logger import get_logger
from ..core.exceptions import TaskError

logger = get_logger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class Task(ABC):
    """任务基类"""

    def __init__(self, name: str = None, task_id: str = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or f"Task-{self.task_id[:8]}"
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result: Any = None
        self.error: Optional[Exception] = None
        self._is_cancelled = False
        self._is_paused = False
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._metadata: dict[str, Any] = {}

    @property
    def is_running(self) -> bool:
        return self.status == TaskStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == TaskStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.status == TaskStatus.CANCELLED

    @property
    def is_paused(self) -> bool:
        return self.status == TaskStatus.PAUSED

    @property
    def is_finished(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def duration(self) -> Optional[float]:
        """任务持续时间（秒）"""
        if self._start_time is None:
            return None
        end_time = self._end_time or self._start_time
        return end_time - self._start_time

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)

    def start(self):
        """开始任务"""
        import time
        self.status = TaskStatus.RUNNING
        self._start_time = time.time()
        self._is_cancelled = False
        self._is_paused = False
        logger.info(f"任务开始: {self.name} ({self.task_id})")

    def complete(self, result: Any = None):
        """完成任务"""
        import time
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.progress = 100
        self._end_time = time.time()
        logger.info(f"任务完成: {self.name} ({self.task_id})")

    def fail(self, error: Exception):
        """任务失败"""
        import time
        self.status = TaskStatus.FAILED
        self.error = error
        self._end_time = time.time()
        logger.error(f"任务失败: {self.name} ({self.task_id}) - {error}")

    def cancel(self):
        """取消任务"""
        import time
        self.status = TaskStatus.CANCELLED
        self._is_cancelled = True
        self._end_time = time.time()
        logger.info(f"任务取消: {self.name} ({self.task_id})")

    def pause(self):
        """暂停任务"""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.PAUSED
            self._is_paused = True
            logger.info(f"任务暂停: {self.name} ({self.task_id})")

    def resume(self):
        """恢复任务"""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            self._is_paused = False
            logger.info(f"任务恢复: {self.name} ({self.task_id})")

    def update_progress(self, progress: int):
        """更新进度"""
        self.progress = max(0, min(100, progress))

    def should_cancel(self) -> bool:
        """检查是否应该取消"""
        return self._is_cancelled

    def should_pause(self) -> bool:
        """检查是否应该暂停"""
        return self._is_paused

    @abstractmethod
    def execute(self) -> Any:
        """执行任务（子类实现）"""
        pass

    def run(self) -> Any:
        """运行任务"""
        try:
            self.start()
            result = self.execute()
            if not self._is_cancelled:
                self.complete(result)
            return result
        except Exception as e:
            self.fail(e)
            raise TaskError(f"任务执行失败: {e}", self.task_id)

    def __str__(self):
        return f"{self.name} ({self.task_id}) - {self.status.value}"

    def __repr__(self):
        return f"<Task: {self.name} ({self.task_id}) - {self.status.value}>"
