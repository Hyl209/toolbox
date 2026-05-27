from __future__ import annotations

import requests
from pathlib import Path
from typing import Optional, Callable
from ..core.logger import get_logger
from ..core.exceptions import ServiceError
from ..core.file_utils import file_utils
from ..core.downloader_base import DownloaderBase, DownloadProgress

logger = get_logger(__name__)


class DownloadService(DownloaderBase):
    """下载服务"""

    def __init__(self, name: str = "HTTPDownloader"):
        super().__init__(name)
        self._session = None
        self._chunk_size = 8192

    def _get_session(self) -> requests.Session:
        """获取 HTTP 会话"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        return self._session

    def download(self, url: str, output_path: str | Path, **kwargs) -> bool:
        """下载文件"""
        try:
            if not self.validate_url(url):
                raise ServiceError(f"无效的 URL: {url}", self.name)

            output_path = self.prepare_output_path(output_path, self.get_filename_from_url(url))
            session = self._get_session()

            # 发起请求
            response = session.get(url, stream=True, timeout=kwargs.get('timeout', 30))
            response.raise_for_status()

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            progress = DownloadProgress(total_size)

            # 下载文件
            downloaded_size = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self._chunk_size):
                    if self.is_cancelled:
                        logger.info(f"下载已取消: {url}")
                        return False

                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress.update(downloaded_size)
                        self._emit_progress(progress)

            logger.info(f"下载完成: {output_path}")
            self._emit_completion(True, f"下载完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"下载失败: {e}")
            self._emit_completion(False, f"下载失败: {e}")
            raise ServiceError(f"下载失败: {e}", self.name)

    def get_filename_from_url(self, url: str) -> str:
        """从 URL 获取文件名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        if path:
            filename = Path(path).name
            if filename:
                return filename
        return "downloaded_file"

    def download_with_progress(self, url: str, output_path: str | Path,
                               progress_callback: Callable[[DownloadProgress], None] = None) -> bool:
        """带进度回调的下载"""
        if progress_callback:
            self.on_progress(progress_callback)
        return self.download(url, output_path)

    def download_multiple(self, urls: list[str], output_dir: str | Path) -> list[Path]:
        """批量下载"""
        output_dir = Path(output_dir)
        file_utils.ensure_dir(output_dir)

        downloaded_files = []
        for url in urls:
            try:
                filename = self.get_filename_from_url(url)
                output_path = output_dir / filename
                if self.download(url, output_path):
                    downloaded_files.append(output_path)
            except Exception as e:
                logger.error(f"批量下载失败 {url}: {e}")

        return downloaded_files

    def get_file_size(self, url: str) -> Optional[int]:
        """获取文件大小"""
        try:
            session = self._get_session()
            response = session.head(url, timeout=10)
            response.raise_for_status()
            content_length = response.headers.get('content-length')
            return int(content_length) if content_length else None
        except Exception as e:
            logger.error(f"获取文件大小失败: {e}")
            return None

    def check_url_valid(self, url: str) -> bool:
        """检查 URL 是否有效"""
        try:
            session = self._get_session()
            response = session.head(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False


# 全局下载服务实例
_download_service: Optional[DownloadService] = None


def get_download_service() -> DownloadService:
    """获取全局下载服务实例"""
    global _download_service
    if _download_service is None:
        _download_service = DownloadService()
    return _download_service
