from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .handlers import FileHandler, CrashHandler, GUIHandler, TaskHandler
from .formatters import LogFormatter

logger = logging.getLogger(__name__)


class LogManager:
    """日志管理器"""

    def __init__(self, log_dir: str | Path = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._loggers: dict[str, logging.Logger] = {}
        self._handlers: dict[str, logging.Handler] = {}
        self._initialized = False

        # 初始化默认处理器
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """设置默认处理器"""
        if self._initialized:
            return

        # 应用日志处理器
        app_handler = FileHandler(
            self.log_dir / "app.log",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
        app_handler.setLevel(logging.DEBUG)
        self._handlers['app'] = app_handler

        # 错误日志处理器
        error_handler = FileHandler(
            self.log_dir / "error.log",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
        error_handler.setLevel(logging.ERROR)
        self._handlers['error'] = error_handler

        # 崩溃日志处理器
        crash_handler = CrashHandler(self.log_dir / "crash")
        crash_handler.setLevel(logging.CRITICAL)
        self._handlers['crash'] = crash_handler

        # 任务日志处理器
        task_handler = TaskHandler(
            self.log_dir / "task.log",
            max_bytes=5*1024*1024,  # 5MB
            backup_count=3
        )
        task_handler.setLevel(logging.INFO)
        self._handlers['task'] = task_handler

        # GUI 异常处理器
        gui_handler = GUIHandler()
        gui_handler.setLevel(logging.ERROR)
        self._handlers['gui'] = gui_handler

        self._initialized = True

    def get_logger(self, name: str, handlers: list[str] = None) -> logging.Logger:
        """获取或创建日志记录器"""
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 添加处理器
        if handlers is None:
            handlers = ['app', 'error', 'crash']

        for handler_name in handlers:
            if handler_name in self._handlers:
                logger.addHandler(self._handlers[handler_name])

        self._loggers[name] = logger
        return logger

    def get_task_logger(self, task_id: str) -> logging.Logger:
        """获取任务专用日志记录器"""
        name = f"task.{task_id}"
        return self.get_logger(name, handlers=['app', 'task'])

    def get_gui_logger(self) -> logging.Logger:
        """获取 GUI 专用日志记录器"""
        return self.get_logger("gui", handlers=['app', 'gui'])

    def get_crash_logger(self) -> logging.Logger:
        """获取崩溃专用日志记录器"""
        return self.get_logger("crash", handlers=['app', 'crash'])

    def set_level(self, level: str):
        """设置全局日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        log_level = level_map.get(level.upper(), logging.INFO)

        for handler in self._handlers.values():
            if not isinstance(handler, CrashHandler):
                handler.setLevel(log_level)

        logger.info(f"日志级别设置为: {level}")

    def add_handler(self, name: str, handler: logging.Handler):
        """添加自定义处理器"""
        self._handlers[name] = handler

    def remove_handler(self, name: str):
        """移除处理器"""
        if name in self._handlers:
            del self._handlers[name]

    def get_handler(self, name: str) -> Optional[logging.Handler]:
        """获取处理器"""
        return self._handlers.get(name)

    def flush_all(self):
        """刷新所有处理器"""
        for handler in self._handlers.values():
            handler.flush()

    def close_all(self):
        """关闭所有处理器"""
        for handler in self._handlers.values():
            handler.close()
        self._handlers.clear()
        self._loggers.clear()

    def get_log_files(self) -> list[Path]:
        """获取所有日志文件"""
        return list(self.log_dir.glob("*.log"))

    def get_log_size(self) -> int:
        """获取日志总大小"""
        total_size = 0
        for log_file in self.get_log_files():
            total_size += log_file.stat().st_size
        return total_size

    def cleanup_old_logs(self, max_age_days: int = 30):
        """清理旧日志"""
        import time

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        for log_file in self.get_log_files():
            file_age = current_time - log_file.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    log_file.unlink()
                    logger.info(f"清理旧日志: {log_file}")
                except Exception as e:
                    logger.error(f"清理旧日志失败 {log_file}: {e}")

    def rotate_logs(self):
        """轮转日志"""
        for handler in self._handlers.values():
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()

    def get_log_content(self, log_name: str, lines: int = 100) -> str:
        """获取日志内容"""
        log_file = self.log_dir / f"{log_name}.log"
        if not log_file.exists():
            return ""

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            logger.error(f"读取日志失败 {log_file}: {e}")
            return ""

    def search_logs(self, keyword: str, log_name: str = None) -> list[str]:
        """搜索日志"""
        results = []

        if log_name:
            log_files = [self.log_dir / f"{log_name}.log"]
        else:
            log_files = self.get_log_files()

        for log_file in log_files:
            if not log_file.exists():
                continue

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if keyword in line:
                            results.append(line.strip())
            except Exception as e:
                logger.error(f"搜索日志失败 {log_file}: {e}")

        return results


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def get_log_manager(log_dir: str | Path = "logs") -> LogManager:
    """获取全局日志管理器实例"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(log_dir)
    return _log_manager
