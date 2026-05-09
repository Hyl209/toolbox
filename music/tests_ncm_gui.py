import pathlib
import tempfile


def test_settings_roundtrip():
    import ncm_gui
    with tempfile.TemporaryDirectory() as tmp:
        settings = ncm_gui.make_settings(tmp)
        sample = str(pathlib.Path(tmp) / 'out')
        ncm_gui.save_output_dir(settings, sample)
        assert ncm_gui.load_output_dir(settings) == sample


def test_collect_drop_paths_gathers_ncm_files():
    import ncm_gui
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
        result = ncm_gui.collect_drop_paths([str(a), str(root)])
        assert result == [a.resolve(), b.resolve()]
