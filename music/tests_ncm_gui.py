import importlib.util
import pathlib
import tempfile
import sys

ROOT = pathlib.Path('PROJECT_ROOT')
MODULE_PATH = ROOT / 'hyl_toolbox.py'


def load_module():
    sys.modules.pop('hyl_toolbox_test_module', None)
    spec = importlib.util.spec_from_file_location('hyl_toolbox_test_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_settings_roundtrip():
    ncm_gui = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        settings = ncm_gui.make_settings(tmp)
        sample = str(pathlib.Path(tmp) / 'out')
        ncm_gui.save_setting(settings, 'music/output_dir', sample)
        assert ncm_gui.load_setting(settings, 'music/output_dir') == sample


def test_collect_drop_paths_gathers_ncm_files():
    ncm_gui = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        a = root / 'a.ncm'
        a.write_bytes(b'x')
        sub = root / 'sub'
        sub.mkdir()
        b = sub / 'b.ncm'
        b.write_bytes(b'y')
        c = root / 'c.txt'
        c.write_text('nope')
        result = ncm_gui.collect_music_inputs([str(a), str(root)])
        assert result == [a.resolve(), b.resolve()]


def test_build_music_item_text_prefers_title_and_artist():
    ncm_gui = load_module()
    item = {
        'title': '灏忕尗涔嬫瓕',
        'artist': 'daddy',
        'file_path': '/tmp/test_song.ncm',
    }
    assert ncm_gui.build_music_item_text(item) == '灏忕尗涔嬫瓕\ndaddy'


def test_build_music_item_text_falls_back_to_file_stem():
    ncm_gui = load_module()
    item = {
        'title': '',
        'artist': '',
        'file_path': '/tmp/fallback_song.ncm',
    }
    assert ncm_gui.build_music_item_text(item) == 'fallback_song'

