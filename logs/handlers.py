from __future__ import annotations

import logging
import logging.handlers
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileHandler(logging.handlers.RotatingFileHandler):
    """文件日志处理器"""

    def __init__(self, filename: str | Path, max_bytes: int = 10*1024*1024,
                 backup_count: int = 5, encoding: str = 'utf-8'):
        # 确保目录存在
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            filename=str(file_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)


class CrashHandler(logging.Handler):
    """崩溃日志处理器"""

    def __init__(self, crash_dir: str | Path):
        super().__init__()
        self.crash_dir = Path(crash_dir)
        self.crash_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, record):
        """记录崩溃信息"""
        try:
            # 生成崩溃文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = self.crash_dir / f"crash_{timestamp}.log"

            # 写入崩溃信息
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"崩溃时间: {datetime.now().isoformat()}\n")
                f.write(f"日志级别: {record.levelname}\n")
                f.write(f"模块: {record.name}\n")
                f.write(f"消息: {record.getMessage()}\n")
                f.write(f"文件: {record.pathname}:{record.lineno}\n")
                f.write(f"函数: {record.funcName}\n\n")

                if record.exc_info:
                    f.write("异常信息:\n")
                    f.write(traceback.format_exception(*record.exc_info))
                elif record.stack_info:
                    f.write("堆栈信息:\n")
                    f.write(record.stack_info)

            logger.info(f"崩溃日志已保存: {crash_file}")

        except Exception as e:
            logger.error(f"保存崩溃日志失败: {e}")


class GUIHandler(logging.Handler):
    """GUI 异常处理器"""

    def __init__(self):
        super().__init__()
        self._callback = None

    def set_callback(self, callback):
        """设置回调函数"""
        self._callback = callback

    def emit(self, record):
        """记录 GUI 异常"""
        try:
            if self._callback:
                message = self.format(record)
                self._callback(message, record.levelno)
        except Exception:
            pass


class TaskHandler(logging.Handler):
    """任务日志处理器"""

    def __init__(self, filename: str | Path, max_bytes: int = 5*1024*1024,
                 backup_count: int = 3, encoding: str = 'utf-8'):
        super().__init__()
        self.file_path = Path(filename)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.encoding = encoding

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)

    def emit(self, record):
        """记录任务信息"""
        try:
            message = self.format(record)
            with open(self.file_path, 'a', encoding=self.encoding) as f:
                f.write(message + '\n')

            # 检查文件大小
            if self.file_path.stat().st_size > self.max_bytes:
                self._rotate()

        except Exception as e:
            logger.error(f"写入任务日志失败: {e}")

    def _rotate(self):
        """轮转日志"""
        try:
            for i in range(self.backup_count, 0, -1):
                old_file = self.file_path.with_suffix(f'.{i}.log')
                new_file = self.file_path.with_suffix(f'.{i+1}.log')
                if old_file.exists():
                    old_file.rename(new_file)

            # 轮转当前文件
            backup_file = self.file_path.with_suffix('.1.log')
            self.file_path.rename(backup_file)

        except Exception as e:
            logger.error(f"轮转任务日志失败: {e}")


class DebugHandler(logging.Handler):
    """调试处理器"""

    def __init__(self):
        super().__init__()
        self._enabled = False

    def enable(self):
        """启用调试"""
        self._enabled = True

    def disable(self):
        """禁用调试"""
        self._enabled = False

    def emit(self, record):
        """输出调试信息"""
        if self._enabled:
            try:
                message = self.format(record)
                print(f"[DEBUG] {message}")
            except Exception:
                pass


class MemoryHandler(logging.Handler):
    """内存处理器（用于日志缓冲）"""

    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity
        from collections import deque
        self.buffer = deque(maxlen=capacity)

    def emit(self, record):
        """缓冲日志"""
        self.buffer.append(record)

    def get_buffer(self):
        """获取缓冲区"""
        return list(self.buffer)

    def clear_buffer(self):
        """清空缓冲区"""
        self.buffer.clear()

    def flush_buffer(self, target_handler: logging.Handler):
        """刷新缓冲区到目标处理器"""
        for record in self.buffer:
            target_handler.emit(record)
        self.clear_buffer()
