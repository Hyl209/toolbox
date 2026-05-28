import importlib.util
import pathlib
import subprocess

import pytest

MODULE_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parents[1]
SAMPLES_DIR = PROJECT_ROOT / "\u6d4b\u8bd5"
SCRIPT = MODULE_DIR / "ncm_to_mp3.py"
PYTHON = MODULE_DIR / ".venv/bin/python"
SAMPLE_NCM = SAMPLES_DIR / "\u7cbe\u5f69\u5f3aSir - \u540e\u5b98\u4f73\u4e3d\u4e09\u5343.ncm"
SAMPLE_MP3 = SAMPLES_DIR / "\u738b\u8273\u8587 - \u79bb\u5f00\u6211\u7684\u4f9d\u8d56\uff08\u6084\u6084\u505a\u4e2a\u68a6\u7ed9\u4f60\uff09.mp3"

_venv_exists = PYTHON.exists()
_sample_ncm_exists = SAMPLE_NCM.exists()
_ncmdump_available = importlib.util.find_spec("ncmdump") is not None


def run_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def load_module():
    spec = importlib.util.spec_from_file_location("ncm_to_mp3", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not _venv_exists, reason="local .venv not found")
def test_help_shows_usage():
    result = run_cmd(str(PYTHON), str(SCRIPT), "--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


@pytest.mark.skipif(not _venv_exists, reason="local .venv not found")
def test_missing_input_fails():
    result = run_cmd(str(PYTHON), str(SCRIPT), "/no/such/file.ncm")
    assert result.returncode != 0
    assert "input not found" in result.stderr.lower()


@pytest.mark.skipif(not _venv_exists or not _sample_ncm_exists, reason="local .venv or sample NCM not found")
def test_sample_ncm_path_is_accepted_for_scan_only():
    result = run_cmd(str(PYTHON), str(SCRIPT), str(SAMPLE_NCM), "--dry-run")
    assert result.returncode == 0
    assert "found" in result.stdout.lower()
    assert SAMPLE_NCM.name in result.stdout


def test_dependency_probe_reports_missing_ncmdump_cleanly():
    module = load_module()
    available, message = module.probe_converter_backend()
    if available:
        assert _ncmdump_available is True
        assert message == ""
    else:
        assert "ncmdump" in message.lower()


def test_extract_song_info_falls_back_to_stem_without_metadata(tmp_path):
    sample = tmp_path / "demo_song.ncm"
    sample.write_bytes(b"plain-bytes-without-metadata")
    module = load_module()
    info = module.extract_song_info(sample)
    assert info["title"] == "demo_song"
    assert info["artist"] == ""
    assert info["display_name"] == "demo_song"
    assert info["cover_data_url"] == ""


def test_extract_song_info_reads_embedded_metadata_and_sidecar_cover(tmp_path):
    metadata = (
        'prefix music:{"musicName":"demo title","artist":[["demo artist",1]],"albumPic":""} suffix'
    ).encode("utf-8")
    sample = tmp_path / "track.ncm"
    sample.write_bytes(metadata)
    cover = tmp_path / "track.png"
    cover.write_bytes(b"\x89PNG\r\n\x1a\ncover-bytes")
    module = load_module()
    info = module.extract_song_info(sample)
    assert info["title"] == "demo title"
    assert info["artist"] == "demo artist"
    assert info["display_name"] == "demo title - demo artist"
    assert info["cover_data_url"].startswith("data:image/png;base64,")


def test_extract_song_info_uses_common_folder_cover_names(tmp_path):
    sample = tmp_path / "demo_song.ncm"
    sample.write_bytes(b"plain-bytes-without-metadata")
    cover = tmp_path / "AlbumArtSmall.jpg"
    cover.write_bytes(b"\xff\xd8\xfffolder-cover")
    module = load_module()
    info = module.extract_song_info(sample)
    assert info["title"] == "demo_song"
    assert info["cover_data_url"].startswith("data:image/jpeg;base64,")


@pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample MP3 not found")
def test_enrich_song_info_from_mp3_reads_real_tags_and_cover():
    module = load_module()
    base_item = {
        "file_path": "/tmp/demo.ncm",
        "title": "old title",
        "artist": "",
        "cover_data_url": "",
    }
    enriched = module.enrich_song_info_from_mp3(base_item, SAMPLE_MP3)
    assert enriched["title"]
    assert enriched["artist"]
    assert enriched["display_name"]
    assert enriched["display_name"].startswith(enriched["title"])
    assert enriched["cover_data_url"].startswith("data:image/jpeg;base64,")
