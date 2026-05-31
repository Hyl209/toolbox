"""Public logging API — ``get_logger(name)``.

Backend implementation: ``logs.manager.LogManager`` provides richer handlers
(Crash, GUI, Task). This module is the stable public interface; all callers
should import ``get_logger`` from here.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

# Short module name mapping for readable prefixes
_SHORT_NAMES: dict[str, str] = {
    'toolbox_app.services.file_service': 'FileSort',
    'toolbox_app.services.download_service': 'Download',
    'toolbox_app.services.video_service': 'VideoConvert',
    'toolbox_app.services.duplicate_service': 'DuplicateFind',
    'toolbox_app.services.ocr_service': 'OCR',
    'toolbox_app.services.image_service': 'ImageConvert',
    'toolbox_app.services.pdf_service': 'PDF',
    'toolbox_app.services.mp4_service': 'MP4Convert',
    'toolbox_app.services.base64_service': 'Base64',
    'toolbox_app.services.hash_service': 'Hash',
    'toolbox_app.core.startup': 'Startup',
    'toolbox_app.core.config': 'Config',
    'toolbox_app.core.performance': 'Perf',
    'toolbox_app.core.worker': 'Worker',
    'toolbox_app.core.task_manager': 'TaskMgr',
    'toolbox_app.plugins.discovery': 'PluginDiscovery',
    'toolbox_app.plugins.manager': 'PluginMgr',
    'toolbox_app.plugins.registry': 'PluginRegistry',
    'resources.cache': 'Cache',
    'resources.temp_manager': 'TempFile',
    'resources.manager': 'Resource',
    'resources.validators': 'Validator',
}


class _ShortNameFormatter(logging.Formatter):
    """Formatter that uses short module prefixes for readability."""

    def format(self, record: logging.LogRecord) -> str:
        short = _SHORT_NAMES.get(record.name, record.name.rsplit('.', 1)[-1])
        record.shortname = short
        return super().format(record)


class LoggerManager:
    """集中式日志管理器"""

    def __init__(self, log_dir: str | Path = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers: dict[str, logging.Logger] = {}
        self._setup_root_logger()

    def _setup_root_logger(self):
        """配置根日志记录器"""
        import logging.handlers as _handlers

        root = logging.getLogger()
        if getattr(root, '_hyl_configured', False):
            return
        root.setLevel(logging.DEBUG)

        # 控制台处理器 — concise format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(_ShortNameFormatter(
            '%(asctime)s [%(shortname)s] %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        root.addHandler(console_handler)

        # 文件处理器 - 应用日志 — full detail for debugging
        app_handler = _handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s - %(message)s'
        ))
        root.addHandler(app_handler)

        # 文件处理器 - 错误日志
        error_handler = _handlers.RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s - %(message)s'
        ))
        root.addHandler(error_handler)
        root._hyl_configured = True

    def get_logger(self, name: str) -> logging.Logger:
        """获取或创建指定名称的日志记录器"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None
_logger_lock = threading.Lock()


def setup_logger(log_dir: str | Path = "logs") -> LoggerManager:
    """初始化全局日志管理器"""
    global _logger_manager
    if _logger_manager is None:
        with _logger_lock:
            if _logger_manager is None:
                _logger_manager = LoggerManager(log_dir)
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    if _logger_manager is None:
        setup_logger()
    return _logger_manager.get_logger(name)
