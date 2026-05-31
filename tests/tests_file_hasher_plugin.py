from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "file_hasher"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("file_hasher_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_file_hasher_plugin_loads(shared_plugin_manager):
    found = shared_plugin_manager.discovery.discover_plugins()
    assert "file_hasher" in found
    plugin = shared_plugin_manager.get_plugin("file_hasher")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "哈希校验"


def test_calculate_hashes(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    hashes = converter.calculate_hashes(sample)

    payload = b"hello"
    assert hashes["md5"] == hashlib.md5(payload).hexdigest()
    assert hashes["sha1"] == hashlib.sha1(payload).hexdigest()
    assert hashes["sha256"] == hashlib.sha256(payload).hexdigest()


def test_calculate_hashes_supports_subset_and_normalizes_algorithm_names(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    hashes = converter.calculate_hashes(sample, ["SHA256"])

    assert list(hashes) == ["sha256"]
    assert hashes["sha256"] == hashlib.sha256(b"hello").hexdigest()


def test_verify_file_hash_auto_detects_algorithm(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")
    expected = hashlib.sha256(b"hello").hexdigest().upper()

    state = converter.verify_file_hash(sample, f"  {expected}  ")

    assert state["algorithm"] == "sha256"
    assert state["matched"] is True
    assert state["expected"] == expected.lower()


def test_verify_file_hash_rejects_unknown_checksum_length(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    try:
        converter.verify_file_hash(sample, "abc")
    except converter.FileHashError as exc:
        assert "无法根据校验值长度识别算法" in str(exc)
    else:
        raise AssertionError("short checksum should be rejected")


def test_calculate_file_hash_single_algorithm(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    result = converter.calculate_file_hash(sample, "md5")

    assert result == hashlib.md5(b"hello").hexdigest()


def test_calculate_file_hash_rejects_unsupported_algorithm(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    try:
        converter.calculate_file_hash(sample, "sha512")
    except converter.FileHashError as exc:
        assert "不支持" in str(exc)
    else:
        raise AssertionError("unsupported algorithm should be rejected")


def test_calculate_file_hash_rejects_missing_file():
    converter = _load_converter()

    try:
        converter.calculate_file_hash("/nonexistent/file.txt")
    except converter.FileHashError as exc:
        assert "请选择有效文件" in str(exc)
    else:
        raise AssertionError("missing file should be rejected")


def test_verify_file_hash_reports_mismatch(tmp_path):
    converter = _load_converter()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    state = converter.verify_file_hash(sample, hashlib.sha256(b"wrong").hexdigest())

    assert state["matched"] is False
