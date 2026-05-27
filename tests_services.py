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
    """ImageService 测试 — 包装 ImageMagick converter"""

    def _make_service(self):
        from toolbox_app.services.image_service import ImageService
        return ImageService()

    def test_check_imagemagick_returns_tuple(self):
        svc = self._make_service()
        result = svc.check_imagemagick()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)

    def test_convert_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.convert(Path("/nonexistent/img.jpg"), Path("/tmp"), "png")

    def test_validate_target_size_empty(self):
        svc = self._make_service()
        result = svc.validate_target_size("")
        assert result is None

    def test_validate_target_size_valid(self):
        svc = self._make_service()
        result = svc.validate_target_size("100")
        assert result == 100

    def test_validate_target_size_invalid(self):
        svc = self._make_service()
        with pytest.raises(ValueError):
            svc.validate_target_size("abc")


# ---------------------------------------------------------------------------
# PDFService (mock, no PyPDF2 dependency)
# ---------------------------------------------------------------------------
class TestPDFService:
    """PDFService 测试 — 包装 pdf-tools/converter.py"""

    def _make_service(self):
        from toolbox_app.services.pdf_service import PDFService
        return PDFService()

    def test_merge_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.merge([Path("/nonexistent/a.pdf")], Path("/tmp/out.pdf"))

    def test_split_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.split(Path("/nonexistent/input.pdf"), Path("/tmp/out"), [0])

    def test_extract_text_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.extract_text(Path("/nonexistent/input.pdf"))

    def test_to_images_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.to_images(Path("/nonexistent/input.pdf"), Path("/tmp/out"))

    def test_export_text_file_not_exist(self):
        svc = self._make_service()
        with pytest.raises(Exception):
            svc.export_text(Path("/nonexistent/input.pdf"), Path("/tmp/out"))


# ---------------------------------------------------------------------------
# OCRService
# ---------------------------------------------------------------------------
class TestOCRService:
    """OCRService mock 测试"""

    def test_initialize_without_tesseract(self):
        """验证 tesseract 未安装时 initialize 抛出 ServiceError"""
        from toolbox_app.services.ocr_service import OCRService
        from toolbox_app.core.exceptions import ServiceError

        svc = OCRService()
        with patch("toolbox_app.services.ocr_service.OCRService._init_tesseract", side_effect=ServiceError("pytesseract 或 Pillow 未安装", "OCRService")):
            with pytest.raises(ServiceError, match="OCR 服务初始化失败"):
                svc.initialize("tesseract")

    def test_recognize_text_file_not_exist(self):
        """文件不存在时抛出 ServiceError"""
        from toolbox_app.services.ocr_service import OCRService
        from toolbox_app.core.exceptions import ServiceError

        svc = OCRService()
        svc._initialized = True
        svc._engine = "tesseract"

        with pytest.raises(ServiceError, match="文件不存在"):
            svc.recognize_text("/nonexistent/image.png")

    @patch("toolbox_app.services.ocr_service.OCRService._init_tesseract")
    def test_recognize_text_mock(self, mock_init):
        """mock pytesseract.image_to_string 验证 recognize_text"""
        from toolbox_app.services.ocr_service import OCRService

        svc = OCRService()
        svc._initialized = True
        svc._engine = "tesseract"

        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "test.png"
            img_path.write_bytes(b"fake image data")

            with patch("toolbox_app.services.ocr_service.OCRService._recognize_tesseract", return_value="Hello OCR") as mock_recognize:
                result = svc.recognize_text(img_path)
                assert result == "Hello OCR"
                mock_recognize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
