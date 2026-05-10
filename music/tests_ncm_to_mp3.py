import importlib.util
import pathlib
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parent / 'ncm_to_mp3.py'
PYTHON = pathlib.Path(__file__).resolve().parent / '.venv/bin/python'
SAMPLE_NCM = pathlib.Path('PROJECT_ROOT/娴嬭瘯/绮惧僵寮篠ir - 鍚庡畼浣充附涓夊崈.ncm')


def run_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_help_shows_usage():
    result = run_cmd(str(PYTHON), str(SCRIPT), '--help')
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower()


def test_missing_input_fails():
    result = run_cmd(str(PYTHON), str(SCRIPT), '/no/such/file.ncm')
    assert result.returncode != 0
    assert 'input not found' in result.stderr.lower()


def test_sample_ncm_path_is_accepted_for_scan_only():
    result = run_cmd(str(PYTHON), str(SCRIPT), str(SAMPLE_NCM), '--dry-run')
    assert result.returncode == 0
    assert 'found' in result.stdout.lower()
    assert SAMPLE_NCM.name in result.stdout


def test_dependency_probe_reports_missing_ncmdump_cleanly():
    spec = importlib.util.spec_from_file_location('ncm_to_mp3', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    available, message = module.probe_converter_backend()
    if available:
        assert message == ''
    else:
        assert 'ncmdump' in message.lower()


def test_extract_song_info_falls_back_to_stem_without_metadata(tmp_path):
    sample = tmp_path / 'demo_song.ncm'
    sample.write_bytes(b'plain-bytes-without-metadata')
    spec = importlib.util.spec_from_file_location('ncm_to_mp3', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    info = module.extract_song_info(sample)
    assert info['title'] == 'demo_song'
    assert info['artist'] == ''
    assert info['display_name'] == 'demo_song'
    assert info['cover_data_url'] == ''


def test_extract_song_info_reads_embedded_metadata_and_sidecar_cover(tmp_path):
    metadata = 'prefix music:{"musicName":"鍠靛柕姝?,"artist":[["鐚尗姝屾墜",1]],"albumPic":""} suffix'.encode('utf-8')
    sample = tmp_path / 'track.ncm'
    sample.write_bytes(metadata)
    cover = tmp_path / 'track.png'
    cover.write_bytes(b'\x89PNG\r\n\x1a\ncover-bytes')
    spec = importlib.util.spec_from_file_location('ncm_to_mp3', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    info = module.extract_song_info(sample)
    assert info['title'] == '鍠靛柕姝?
    assert info['artist'] == '鐚尗姝屾墜'
    assert info['display_name'] == '鍠靛柕姝?- 鐚尗姝屾墜'
    assert info['cover_data_url'].startswith('data:image/png;base64,')


