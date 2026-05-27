from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class LoggerManager:
    """集中式日志管理器"""

    def __init__(self, log_dir: str | Path = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers: dict[str, logging.Logger] = {}
        self._setup_root_logger()

    def _setup_root_logger(self):
        """配置根日志记录器"""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        root.addHandler(console_handler)

        # 文件处理器 - 应用日志
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        app_handler.setFormatter(app_format)
        root.addHandler(app_handler)

        # 文件处理器 - 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(app_format)
        root.addHandler(error_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取或创建指定名称的日志记录器"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def setup_logger(log_dir: str | Path = "logs") -> LoggerManager:
    """初始化全局日志管理器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager(log_dir)
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    if _logger_manager is None:
        setup_logger()
    return _logger_manager.get_logger(name)
