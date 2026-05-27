from __future__ import annotations

import json
import requests
from pathlib import Path
from typing import Optional, Callable
from .logger import get_logger
from .exceptions import ToolboxError

logger = get_logger(__name__)


class UpdateInfo:
    """更新信息"""

    def __init__(self, version: str, url: str, changelog: str = "",
                 file_size: int = 0, checksum: str = ""):
        self.version = version
        self.url = url
        self.changelog = changelog
        self.file_size = file_size
        self.checksum = checksum

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'url': self.url,
            'changelog': self.changelog,
            'file_size': self.file_size,
            'checksum': self.checksum
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UpdateInfo':
        return cls(
            version=data.get('version', ''),
            url=data.get('url', ''),
            changelog=data.get('changelog', ''),
            file_size=data.get('file_size', 0),
            checksum=data.get('checksum', '')
        )


class UpdateChecker:
    """更新检查器"""

    def __init__(self, update_url: str = None, current_version: str = "2.0.0"):
        self.update_url = update_url
        self.current_version = current_version
        self._last_check: Optional[float] = None
        self._last_update_info: Optional[UpdateInfo] = None

    def check_for_updates(self) -> Optional[UpdateInfo]:
        """检查更新"""
        if not self.update_url:
            logger.warning("未配置更新 URL")
            return None

        try:
            response = requests.get(self.update_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            update_info = UpdateInfo.from_dict(data)

            # 比较版本
            if self._is_newer_version(update_info.version, self.current_version):
                self._last_update_info = update_info
                logger.info(f"发现新版本: {update_info.version}")
                return update_info
            else:
                logger.info("当前已是最新版本")
                return None

        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return None

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """比较版本号"""
        try:
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]

            # 补齐版本号长度
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return new_parts > current_parts
        except Exception:
            return False

    def get_last_check_time(self) -> Optional[float]:
        """获取最后检查时间"""
        return self._last_check

    def get_last_update_info(self) -> Optional[UpdateInfo]:
        """获取最后更新信息"""
        return self._last_update_info


class UpdateDownloader:
    """更新下载器"""

    def __init__(self, download_dir: str | Path = None):
        if download_dir is None:
            download_dir = Path(__file__).parent.parent / "updates"

        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self._progress_callbacks: list[Callable[[int, int], None]] = []

    def on_progress(self, callback: Callable[[int, int], None]):
        """注册进度回调"""
        self._progress_callbacks.append(callback)

    def _emit_progress(self, downloaded: int, total: int):
        """触发进度回调"""
        for callback in self._progress_callbacks:
            try:
                callback(downloaded, total)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    def download_update(self, update_info: UpdateInfo) -> Optional[Path]:
        """下载更新"""
        try:
            # 生成文件名
            filename = f"update_{update_info.version}.zip"
            output_path = self.download_dir / filename

            # 下载文件
            response = requests.get(update_info.url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self._emit_progress(downloaded_size, total_size)

            logger.info(f"更新下载完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"下载更新失败: {e}")
            return None


class UpdateInstaller:
    """更新安装器"""

    def __init__(self, backup_dir: str | Path = None):
        if backup_dir is None:
            backup_dir = Path(__file__).parent.parent / "backups"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def install_update(self, update_path: Path, app_dir: Path) -> bool:
        """安装更新"""
        try:
            # 创建备份
            self._create_backup(app_dir)

            # 解压更新
            self._extract_update(update_path, app_dir)

            logger.info("更新安装完成")
            return True

        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            # 恢复备份
            self._restore_backup(app_dir)
            return False

    def _create_backup(self, app_dir: Path):
        """创建备份"""
        import shutil
        import time

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"

        shutil.copytree(app_dir, backup_path, dirs_exist_ok=True)
        logger.info(f"创建备份: {backup_path}")

    def _restore_backup(self, app_dir: Path):
        """恢复备份"""
        import shutil

        # 找到最新的备份
        backups = sorted(self.backup_dir.glob("backup_*"), reverse=True)
        if not backups:
            logger.error("没有可用的备份")
            return

        latest_backup = backups[0]
        shutil.copytree(latest_backup, app_dir, dirs_exist_ok=True)
        logger.info(f"恢复备份: {latest_backup}")

    def _extract_update(self, update_path: Path, app_dir: Path):
        """解压更新"""
        import zipfile

        with zipfile.ZipFile(update_path, 'r') as zip_ref:
            zip_ref.extractall(app_dir)

        logger.info(f"解压更新到: {app_dir}")


class UpdateManager:
    """更新管理器"""

    def __init__(self, update_url: str = None, current_version: str = "2.0.0"):
        self.checker = UpdateChecker(update_url, current_version)
        self.downloader = UpdateDownloader()
        self.installer = UpdateInstaller()

        self._update_callbacks: list[Callable[[UpdateInfo], None]] = []

    def on_update_available(self, callback: Callable[[UpdateInfo], None]):
        """注册更新可用回调"""
        self._update_callbacks.append(callback)

    def _emit_update_available(self, update_info: UpdateInfo):
        """触发更新可用回调"""
        for callback in self._update_callbacks:
            try:
                callback(update_info)
            except Exception as e:
                logger.error(f"更新回调执行失败: {e}")

    def check_and_notify(self) -> Optional[UpdateInfo]:
        """检查并通知更新"""
        update_info = self.checker.check_for_updates()
        if update_info:
            self._emit_update_available(update_info)
        return update_info

    def download_and_install(self, update_info: UpdateInfo, app_dir: Path) -> bool:
        """下载并安装更新"""
        # 下载更新
        update_path = self.downloader.download_update(update_info)
        if not update_path:
            return False

        # 安装更新
        return self.installer.install_update(update_path, app_dir)


# 全局更新管理器实例
_update_manager: Optional[UpdateManager] = None


def get_update_manager(update_url: str = None, current_version: str = "2.0.0") -> UpdateManager:
    """获取全局更新管理器实例"""
    global _update_manager
    if _update_manager is None:
        _update_manager = UpdateManager(update_url, current_version)
    return _update_manager
