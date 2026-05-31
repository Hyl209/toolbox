from __future__ import annotations

import importlib.util
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "archive_extractor"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("archive_extractor_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_archive_extractor_plugin_loads(shared_plugin_manager):
    found = shared_plugin_manager.discovery.discover_plugins()
    assert "archive_extractor" in found
    plugin = shared_plugin_manager.get_plugin("archive_extractor")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "解压"


def test_extract_zip_archive(tmp_path):
    converter = _load_converter()
    archive = tmp_path / "demo.unknown"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a.txt", "hello")

    count = converter.extract_archive(archive, out_dir)

    assert count == 1
    assert (out_dir / "a.txt").read_text(encoding="utf-8") == "hello"


def test_rejects_zip_path_traversal(tmp_path):
    converter = _load_converter()
    archive = tmp_path / "bad.zip"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../evil.txt", "bad")

    try:
        converter.extract_archive(archive, out_dir)
    except converter.ArchiveExtractError as exc:
        assert "不安全路径" in str(exc)
    else:
        raise AssertionError("path traversal archive should be rejected")


def test_extract_tar_archive(tmp_path):
    converter = _load_converter()
    source = tmp_path / "source.txt"
    source.write_text("tar ok", encoding="utf-8")
    archive = tmp_path / "demo.bin"
    out_dir = tmp_path / "out"
    with tarfile.open(archive, "w") as tf:
        tf.add(source, arcname="source.txt")

    count = converter.extract_archive(archive, out_dir)

    assert count == 1
    assert (out_dir / "source.txt").read_text(encoding="utf-8") == "tar ok"


def test_detect_rejects_non_archive_even_with_zip_suffix(tmp_path):
    converter = _load_converter()
    fake = tmp_path / "fake.zip"
    fake.write_text("not an archive", encoding="utf-8")

    assert converter.detect_archive_type(fake) == ""
    assert converter.is_supported_archive(fake) is False


def test_extract_archive_accepts_password_argument_for_zip(tmp_path):
    converter = _load_converter()
    archive = tmp_path / "demo.locked"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.setpassword(b"secret")
        zf.writestr("a.txt", "hello")

    count = converter.extract_archive(archive, out_dir, password="secret")

    assert count == 1
    assert (out_dir / "a.txt").read_text(encoding="utf-8") == "hello"
