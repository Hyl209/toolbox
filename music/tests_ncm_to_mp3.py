import pathlib
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parent / 'ncm_to_mp3.py'
PYTHON = pathlib.Path(__file__).resolve().parent / '.venv/bin/python'
SAMPLE_NCM = pathlib.Path('PROJECT_ROOT/music/绮惧僵寮篠ir - 鍚庡畼浣充附涓夊崈.ncm')


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
    import importlib.util
    spec = importlib.util.spec_from_file_location('ncm_to_mp3', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    available, message = module.probe_converter_backend()
    if available:
        assert message == ''
    else:
        assert 'ncmdump' in message.lower()

