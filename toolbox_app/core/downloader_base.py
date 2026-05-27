from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable
from .logger import get_logger
from .exceptions import ServiceError
from .file_utils import file_utils

logger = get_logger(__name__)


class DownloadProgress:
    """下载进度信息"""

    def __init__(self, total: int = 0, downloaded: int = 0):
        self.total = total
        self.downloaded = downloaded
        self.start_time = time.time()
        self._last_update = self.start_time
        self._speed_samples: list[float] = []

    @property
    def percentage(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.downloaded / self.total) * 100)

    @property
    def speed(self) -> float:
        """当前下载速度（字节/秒）"""
        if len(self._speed_samples) < 2:
            return 0.0
        return sum(self._speed_samples) / len(self._speed_samples)

    @property
    def eta(self) -> float:
        """预计剩余时间（秒）"""
        if self.speed <= 0:
            return 0.0
        remaining = self.total - self.downloaded
        return remaining / self.speed

    def update(self, downloaded: int):
        """更新下载进度"""
        now = time.time()
        time_diff = now - self._last_update
        if time_diff > 0:
            bytes_diff = downloaded - self.downloaded
            speed = bytes_diff / time_diff
            self._speed_samples.append(speed)
            if len(self._speed_samples) > 10:
                self._speed_samples.pop(0)

        self.downloaded = downloaded
        self._last_update = now

    def format_speed(self) -> str:
        """格式化下载速度"""
        speed = self.speed
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed / (1024 * 1024):.1f} MB/s"

    def format_eta(self) -> str:
        """格式化预计剩余时间"""
        eta = self.eta
        if eta < 60:
            return f"{eta:.0f}秒"
        elif eta < 3600:
            return f"{eta / 60:.0f}分钟"
        else:
            return f"{eta / 3600:.1f}小时"


class DownloaderBase(ABC):
    """下载器基类"""

    def __init__(self, name: str):
        self.name = name
        self._is_cancelled = False
        self._progress_callbacks: list[Callable[[DownloadProgress], None]] = []
        self._completion_callbacks: list[Callable[[bool, str], None]] = []

    def on_progress(self, callback: Callable[[DownloadProgress], None]):
        """注册进度回调"""
        self._progress_callbacks.append(callback)

    def on_completion(self, callback: Callable[[bool, str], None]):
        """注册完成回调"""
        self._completion_callbacks.append(callback)

    def _emit_progress(self, progress: DownloadProgress):
        """触发进度回调"""
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    def _emit_completion(self, success: bool, message: str):
        """触发完成回调"""
        for callback in self._completion_callbacks:
            try:
                callback(success, message)
            except Exception as e:
                logger.error(f"完成回调执行失败: {e}")

    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
        logger.info(f"下载器 {self.name} 已取消")

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @abstractmethod
    def download(self, url: str, output_path: str | Path, **kwargs) -> bool:
        """下载文件"""
        pass

    @abstractmethod
    def get_filename_from_url(self, url: str) -> str:
        """从 URL 获取文件名"""
        pass

    def validate_url(self, url: str) -> bool:
        """验证 URL 是否有效"""
        return url.startswith(('http://', 'https://'))

    def prepare_output_path(self, output_path: str | Path, filename: str = None) -> Path:
        """准备输出路径"""
        output_path = Path(output_path)
        if output_path.is_dir():
            if filename:
                output_path = output_path / filename
            else:
                raise ServiceError("输出路径为目录时必须提供文件名", self.name)

        file_utils.ensure_dir(output_path.parent)
        return file_utils.get_unique_filename(output_path)
