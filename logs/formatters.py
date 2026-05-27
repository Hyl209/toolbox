from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Any


class LogFormatter(logging.Formatter):
    """日志格式化器"""

    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'

        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 调用父类格式化
        message = super().format(record)

        # 添加额外信息
        if hasattr(record, 'task_id'):
            message = f"[Task:{record.task_id}] {message}"

        if hasattr(record, 'user'):
            message = f"[User:{record.user}] {message}"

        return message


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def __init__(self, include_stack_info: bool = False):
        super().__init__()
        self.include_stack_info = include_stack_info

    def format(self, record: logging.LogRecord) -> str:
        """格式化为 JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'file': record.pathname
        }

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # 添加堆栈信息
        if self.include_stack_info and record.stack_info:
            log_data['stack_info'] = record.stack_info

        # 添加额外字段
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id

        if hasattr(record, 'user'):
            log_data['user'] = record.user

        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色格式化器（用于控制台）"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def __init__(self, fmt: str = None, datefmt: str = None):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'

        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """格式化为彩色"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # 格式化消息
        message = super().format(record)

        # 添加颜色
        return f"{color}{message}{reset}"


class CompactFormatter(logging.Formatter):
    """紧凑格式化器"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """格式化为紧凑格式"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname[0]  # 只取首字母
        message = record.getMessage()

        return f"{timestamp} {level} {message}"


class DetailedFormatter(logging.Formatter):
    """详细格式化器"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """格式化为详细格式"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname.ljust(8)
        name = record.name.ljust(20)
        location = f"{record.pathname}:{record.lineno}"
        message = record.getMessage()

        formatted = f"{timestamp} {level} {name} {location}\n  {message}"

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class TaskFormatter(logging.Formatter):
    """任务日志格式化器"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """格式化任务日志"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        task_id = getattr(record, 'task_id', 'unknown')
        message = record.getMessage()

        return f"{timestamp} [{level}] [Task:{task_id}] {message}"


class SecurityFormatter(logging.Formatter):
    """安全日志格式化器"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """格式化安全日志"""
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        user = getattr(record, 'user', 'anonymous')
        action = getattr(record, 'action', 'unknown')
        message = record.getMessage()

        return f"{timestamp} {level} user={user} action={action} {message}"
