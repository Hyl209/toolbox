"""QThread → TaskFramework 适配器

将现有的 QThread worker 模式桥接到统一任务框架，
使现有 tab 文件可以逐步迁移到 task_framework。
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from .task import Task, TaskStatus
from .manager import TaskManager
from ..core.logger import get_logger

logger = get_logger(__name__)


class QThreadTaskAdapter(Task):
    """将 QThread worker 包装为 Task 对象

    用法:
        adapter = QThreadTaskAdapter("download", worker_func, arg1, arg2)
        manager.submit_task(adapter)
    """

    def __init__(self, name: str, func: Callable, *args, **kwargs):
        super().__init__(name)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def execute(self) -> Any:
        return self._func(*self._args, **self._kwargs)


def run_in_background(func: Callable, *args, name: str = None, **kwargs) -> Task:
    """快捷函数：将同步函数提交到后台任务框架执行

    用法:
        from toolbox_app.task_framework.qthread_adapter import run_in_background

        def do_work(folder, recursive):
            return find_duplicates(folder, recursive)

        task = run_in_background(do_work, folder_path, recursive=True)
        task_manager.submit_task(task)
    """
    task_name = name or func.__name__
    return QThreadTaskAdapter(task_name, func, *args, **kwargs)


class TaskUIBridge:
    """任务框架 ↔ UI 桥接器

    将 task_framework 的信号连接到 UI 更新回调，
    替代手动创建 QThread + moveToThread 的模式。

    用法:
        bridge = TaskUIBridge(task_manager)

        def on_progress(task, pct):
            progress_bar.setValue(pct)

        def on_done(task, result):
            show_themed_success(self, '完成', [str(result)])

        def on_error(task, exc):
            show_themed_error(self, '失败', str(exc))

        bridge.connect(on_progress=on_progress, on_done=on_done, on_error=on_error)
        bridge.submit("my_task", my_func, arg1, arg2)
    """

    def __init__(self, manager: TaskManager = None):
        self._manager = manager or TaskManager()
        self._progress_cb: Optional[Callable] = None
        self._done_cb: Optional[Callable] = None
        self._error_cb: Optional[Callable] = None

    def connect(self, on_progress: Callable = None, on_done: Callable = None,
                on_error: Callable = None):
        """连接 UI 回调"""
        if on_progress:
            self._progress_cb = on_progress
            self._manager.on_task_progress(lambda t, p: on_progress(t, p))
        if on_done:
            self._done_cb = on_done
            self._manager.on_task_completed(lambda t, r: on_done(t, r))
        if on_error:
            self._error_cb = on_error
            self._manager.on_task_failed(lambda t, e: on_error(t, e))

    def submit(self, name: str, func: Callable, *args, **kwargs) -> Task:
        """提交任务到后台"""
        return self._manager.submit(func, *args, name=name, **kwargs)

    @property
    def manager(self) -> TaskManager:
        return self._manager
