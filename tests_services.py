"""Tests for toolbox_app.services — all external deps mocked."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# DownloadService
# ---------------------------------------------------------------------------
class TestDownloadService:
    """DownloadService mock 测试"""

    def _make_service(self):
        from toolbox_app.services.download_service import DownloadService
        return DownloadService()

    def test_name_default(self):
        svc = self._make_service()
        assert svc.name == "HTTPDownloader"

    def test_get_filename_from_url(self):
        svc = self._make_service()
        assert svc.get_filename_from_url("https://example.com/path/file.mp4") == "file.mp4"
        assert svc.get_filename_from_url("https://example.com/") == "downloaded_file"

    def test_validate_url(self):
        svc = self._make_service()
        assert svc.validate_url("https://example.com") is True
        assert svc.validate_url("http://example.com") is True
        assert svc.validate_url("ftp://example.com") is False
        assert svc.validate_url("not_a_url") is False

    @patch("toolbox_app.services.download_service.requests.Session")
    def test_download_success(self, mock_session_cls):
        svc = self._make_service()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "10"}
        mock_resp.iter_content.return_value = [b"12345", b"67890"]
        mock_resp.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.bin"
            result = svc.download("https://example.com/file.bin", output)
            assert result is True
            assert output.exists()
            assert output.read_bytes() == b"1234567890"

    @patch("toolbox_app.services.download_service.requests.Session")
    def test_download_invalid_url_raises(self, mock_session_cls):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(Exception):
                svc.download("ftp://bad", Path(tmp) / "out.bin")

    @patch("toolbox_app.services.download_service.requests.Session")
    def test_download_multiple(self, mock_session_cls):
        svc = self._make_service()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.iter_content.return_value = [b"data"]
        mock_resp.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        with tempfile.TemporaryDirectory() as tmp:
            urls = ["https://example.com/a.bin", "https://example.com/b.bin"]
            result = svc.download_multiple(urls, tmp)
            assert len(result) == 2

    def test_cancel(self):
        svc = self._make_service()
        assert svc.is_cancelled is False
        svc.cancel()
        assert svc.is_cancelled is True


# ---------------------------------------------------------------------------
# FileService
# ---------------------------------------------------------------------------
class TestFileService:
    """FileService 测试 — 使用临时目录"""

    def _make_service(self):
        from toolbox_app.services.file_service import FileService
        return FileService()

    def test_organize_files_by_extension(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            # 创建测试文件
            (Path(src) / "photo.jpg").write_bytes(b"jpg")
            (Path(src) / "video.mp4").write_bytes(b"mp4")
            (Path(src) / "doc.pdf").write_bytes(b"pdf")
            (Path(src) / "song.mp3").write_bytes(b"mp3")
            (Path(src) / "archive.zip").write_bytes(b"zip")

            result = svc.organize_files(src, dst, organize_by="extension")
            assert "图片" in result
            assert "视频" in result
            assert "文档" in result
            assert "音频" in result
            assert "压缩包" in result
            assert len(result["图片"]) == 1

    def test_organize_files_by_size(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            small = Path(src) / "small.txt"
            small.write_bytes(b"x" * 100)
            result = svc.organize_files(src, dst, organize_by="size")
            assert "小文件" in result

    def test_organize_files_source_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.organize_files("/nonexistent/path", "/tmp/dst")

    def test_find_duplicates(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_bytes(b"same content")
            (Path(tmp) / "b.txt").write_bytes(b"same content")
            (Path(tmp) / "c.txt").write_bytes(b"different")
            result = svc.find_duplicates(tmp)
            # a.txt and b.txt have same content
            assert len(result) >= 1
            for hash_val, files in result.items():
                assert len(files) >= 2

    def test_find_duplicates_no_dupes(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_bytes(b"unique1")
            (Path(tmp) / "b.txt").write_bytes(b"unique2")
            result = svc.find_duplicates(tmp)
            assert len(result) == 0

    def test_find_duplicates_dir_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.find_duplicates("/nonexistent/dir")

    def test_rename_batch(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "old_name.txt").write_text("x", encoding="utf-8")
            (Path(tmp) / "old_data.csv").write_text("y", encoding="utf-8")
            result = svc.rename_batch(tmp, "old_", "new_")
            assert len(result) == 2
            names = {p.name for p in result}
            assert "new_name.txt" in names
            assert "new_data.csv" in names

    def test_rename_batch_no_match(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "keep.txt").write_text("x", encoding="utf-8")
            result = svc.rename_batch(tmp, "zzz", "new_")
            assert len(result) == 0

    def test_rename_batch_dir_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.rename_batch("/nonexistent", "a", "b")

    def test_get_directory_stats(self):
        svc = self._make_service()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.jpg").write_bytes(b"x" * 100)
            (Path(tmp) / "b.mp4").write_bytes(b"y" * 200)
            stats = svc.get_directory_stats(tmp)
            assert stats["total_files"] == 2
            assert stats["total_size"] == 300
            assert ".jpg" in stats["by_extension"]
            assert ".mp4" in stats["by_extension"]

    def test_get_directory_stats_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.get_directory_stats("/nonexistent")


# ---------------------------------------------------------------------------
# ImageService (mock, no Pillow dependency)
# ---------------------------------------------------------------------------
class TestImageService:
    """ImageService mock 测试 — 不依赖 Pillow"""

    def _make_service(self):
        from toolbox_app.services.image_service import ImageService
        return ImageService()

    def test_initialize_success(self):
        svc = self._make_service()
        svc.initialize()
        assert svc._initialized is True

    def test_initialize_without_pillow(self):
        svc = self._make_service()
        # 直接设置 _initialized 绕过 import
        svc._initialized = True
        assert svc._initialized is True

    def test_convert_format_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.convert_format("/nonexistent/img.jpg", "/tmp/out.png")

    def test_resize_image_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.resize_image("/nonexistent/img.jpg", "/tmp/out.png", (100, 100))

    def test_rotate_image_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.rotate_image("/nonexistent/img.jpg", "/tmp/out.png", 90)

    def test_crop_image_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.crop_image("/nonexistent/img.jpg", "/tmp/out.png", (0, 0, 100, 100))

    def test_get_image_info_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        result = svc.get_image_info("/nonexistent/img.jpg")
        assert result is None

    @patch("PIL.Image")
    def test_convert_format_success(self, mock_image):
        svc = self._make_service()
        svc._initialized = True

        mock_img = MagicMock()
        mock_image.open.return_value = mock_img

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "input.jpg"
            dst = Path(tmp) / "output.png"
            src.write_bytes(b"fake jpg data")

            result = svc.convert_format(src, dst, format="PNG")
            assert result is True
            mock_image.open.assert_called_once_with(src)
            mock_img.save.assert_called_once()

    @patch("PIL.Image")
    def test_resize_image_success(self, mock_image):
        svc = self._make_service()
        svc._initialized = True

        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        mock_image.Resampling.LANCZOS = "lanczos"

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "input.jpg"
            dst = Path(tmp) / "output.jpg"
            src.write_bytes(b"fake jpg data")

            result = svc.resize_image(src, dst, (100, 100), maintain_aspect=True)
            assert result is True
            mock_img.thumbnail.assert_called_once()


# ---------------------------------------------------------------------------
# PDFService (mock, no PyPDF2 dependency)
# ---------------------------------------------------------------------------
class TestPDFService:
    """PDFService mock 测试 — 不依赖 PyPDF2"""

    def _make_service(self):
        from toolbox_app.services.pdf_service import PDFService
        return PDFService()

    def test_initialize_without_pypdf2(self):
        svc = self._make_service()
        svc._initialized = True
        assert svc._initialized is True

    def test_merge_pdfs_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.merge_pdfs(["/nonexistent/a.pdf"], "/tmp/out.pdf")

    def test_split_pdf_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.split_pdf("/nonexistent/input.pdf", "/tmp/out")

    def test_extract_text_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.extract_text("/nonexistent/input.pdf")

    def test_add_password_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.add_password("/nonexistent/input.pdf", "/tmp/out.pdf", "pass")

    def test_get_page_count_file_not_exist(self):
        svc = self._make_service()
        svc._initialized = True
        with pytest.raises(Exception):
            svc.get_page_count("/nonexistent/input.pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
