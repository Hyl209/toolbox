import importlib.util
import pathlib
import tempfile
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
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
        'title': '小猫之歌',
        'artist': 'daddy',
        'file_path': '/tmp/test_song.ncm',
    }
    assert ncm_gui.build_music_item_text(item) == '小猫之歌\ndaddy'


def test_build_music_item_text_falls_back_to_file_stem():
    ncm_gui = load_module()
    item = {
        'title': '',
        'artist': '',
        'file_path': '/tmp/fallback_song.ncm',
    }
    assert ncm_gui.build_music_item_text(item) == 'fallback_song'


def test_format_music_drop_summary_matches_unified_drop_area_copy():
    ncm_gui = load_module()
    assert ncm_gui.format_music_drop_summary([]) == '拖入ncm文件'
    files = [
        pathlib.Path('/tmp/alpha.ncm'),
        pathlib.Path('/tmp/beta.ncm'),
        pathlib.Path('/tmp/gamma.ncm'),
        pathlib.Path('/tmp/delta.ncm'),
    ]
    assert ncm_gui.format_music_drop_summary(files) == '拖入ncm文件'


def test_enrich_song_info_from_mp3_keeps_existing_values_when_file_missing():
    ncm_gui = load_module()
    module = ncm_gui._load_ncm_module()
    base_item = {
        'file_path': '/tmp/test_song.ncm',
        'title': '原歌名',
        'artist': '原歌手',
        'cover_data_url': 'data:image/png;base64,abc',
    }
    enriched = module.enrich_song_info_from_mp3(base_item, pathlib.Path('/tmp/not_found.mp3'))
    assert enriched == base_item


def test_build_music_scroll_area_style_contains_pretty_scrollbar_rules():
    ncm_gui = load_module()
    style = ncm_gui.build_music_scroll_area_style()
    assert 'QScrollBar:vertical' in style
    assert 'QScrollBar::handle:vertical:hover' in style
    assert 'border-radius: 5px' in style
    assert 'background: transparent' in style


def test_music_tab_rendered_song_item_uses_cover_pixmap_when_available():
    ncm_gui = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        window, app = ncm_gui.build_main_window_for_test(tmp)
        item = {
            'file_path': '/tmp/demo_song.ncm',
            'title': '封面测试',
            'artist': 'Daddy',
            'cover_data_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn8n0cAAAAASUVORK5CYII=',
        }
        widget = window.music_tab.build_song_item_widget(1, item)
        labels = widget.findChildren(ncm_gui.QLabel)
        cover_label = labels[0]
        pixmap = cover_label.pixmap()
        assert pixmap is not None
        assert not pixmap.isNull()
        window.close()
        app.quit()


def test_music_tab_add_paths_collects_cover_data_from_real_ncm_sample():
    ncm_gui = load_module()
    samples = sorted(ROOT.glob('**/*.ncm'))
    if not samples:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = ncm_gui.build_main_window_for_test(tmp)
        window.music_tab.add_paths([str(samples[0])])
        assert len(window.music_tab.file_items) == 1
        assert window.music_tab.file_items[0].get('cover_data_url', '').startswith('data:image')
        window.close()
        app.quit()


def test_music_tab_clear_and_remove_hooks_exist_in_source():
    source = MODULE_PATH.read_text(encoding='utf-8')
    assert "self.clear_files_button = QPushButton('清空文件')" in source
    assert "self.clear_files_button.clicked.connect(self.clear_selected_files)" in source
    assert "def clear_selected_files(self):" in source
    assert "def remove_song_item(self, file_path: str):" in source
    assert "remove_button = QPushButton('✕')" in source
    assert "remove_button.setFlat(True)" in source
    assert "background: transparent" in source
    assert "cover_data_url" in source
    assert "cover_label.setPixmap" in source
    assert "self.log.appendPlainText(f'已清空 {cleared_count} 个待转换文件')" in source
    assert "self.log.appendPlainText(f'已移除: {target.stem}')" in source
