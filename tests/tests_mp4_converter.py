import importlib.util
import pathlib
import sys
import tempfile
from unittest.mock import patch, MagicMock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / 'modules' / 'audio-extractor' / 'converter.py'


def load_module():
    sys.modules.pop('tests_mp4_converter_module', None)
    spec = importlib.util.spec_from_file_location('tests_mp4_converter_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_output_path_with_explicit_mp3():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'song.mp4'
        src.write_bytes(b'\x00')
        dst = pathlib.Path(tmp) / 'out.mp3'
        result = module.resolve_output_path(src, dst)
        assert result.suffix == '.mp3'


def test_resolve_output_path_with_dir_output():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'song.mp4'
        src.write_bytes(b'\x00')
        out_dir = pathlib.Path(tmp) / 'outdir'
        out_dir.mkdir()
        result = module.resolve_output_path(src, out_dir)
        assert result.name == 'song.mp3'
        assert result.parent.resolve() == out_dir.resolve()


def test_resolve_output_path_raises_for_non_mp4():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'song.avi'
        src.write_bytes(b'\x00')
        try:
            module.resolve_output_path(src)
            assert False, 'Should have raised'
        except module.ConvertError:
            pass


def test_resolve_output_path_replaces_suffix_for_file_arg():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'track.mp4'
        src.write_bytes(b'\x00')
        out = pathlib.Path(tmp) / 'custom_name'
        result = module.resolve_output_path(src, out)
        assert result.suffix == '.mp3'
        assert result.stem == 'custom_name'


def test_resolve_output_path_default_same_dir():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'track.mp4'
        src.write_bytes(b'\x00')
        # Mock _get_default_output_dir to return None
        with patch.object(module, '_get_default_output_dir', return_value=None):
            result = module.resolve_output_path(src)
        assert result.name == 'track.mp3'
        assert result.parent.resolve() == src.parent.resolve()


def test_convert_mp4_to_mp3_raises_on_missing_input():
    module = load_module()
    try:
        module.convert_mp4_to_mp3('/nonexistent/file.mp4')
        assert False
    except module.ConvertError as e:
        assert '不存在' in str(e)


def test_convert_mp4_to_mp3_raises_on_dir_input():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            module.convert_mp4_to_mp3(tmp)
            assert False
        except module.ConvertError as e:
            assert '不是文件' in str(e)


@patch('shutil.which', return_value='/usr/bin/ffmpeg')
@patch('subprocess.run')
def test_convert_mp4_to_mp3_success(mock_run, mock_which):
    module = load_module()
    mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'song.mp4'
        src.write_bytes(b'\x00')
        with patch.object(module, '_get_default_output_dir', return_value=None):
            result = module.convert_mp4_to_mp3(src)
        assert result.suffix == '.mp3'
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert '-vn' in cmd
        assert 'libmp3lame' in cmd


@patch('shutil.which', return_value='/usr/bin/ffmpeg')
@patch('subprocess.run')
def test_convert_mp4_to_mp3_ffmpeg_failure(mock_run, mock_which):
    module = load_module()
    mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='codec error')
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'song.mp4'
        src.write_bytes(b'\x00')
        with patch.object(module, '_get_default_output_dir', return_value=None):
            try:
                module.convert_mp4_to_mp3(src)
                assert False
            except module.ConvertError as e:
                assert 'codec error' in str(e)


def test_ensure_ffmpeg_raises_when_not_found():
    module = load_module()
    with patch('shutil.which', return_value=None):
        try:
            module.ensure_ffmpeg()
            assert False
        except module.ConvertError as e:
            assert 'ffmpeg' in str(e)
