import importlib.util
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / 'name' / 'converter.py'


def load_module():
    sys.modules.pop('tests_name_converter_module', None)
    spec = importlib.util.spec_from_file_location('tests_name_converter_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_normalize_prefix_valid():
    module = load_module()
    assert module.normalize_prefix(' photos ') == 'photos'
    assert module.normalize_prefix('file.') == 'file'
    assert module.normalize_prefix('file..') == 'file'


def test_normalize_prefix_invalid():
    module = load_module()
    import pytest
    for bad in ['', '   ', 'a/b', 'a<b', 'a*b']:
        try:
            module.normalize_prefix(bad)
            assert False, f'Should have raised for: {bad!r}'
        except ValueError:
            pass


def test_scan_folder_returns_sorted_files():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'b.txt').write_text('b')
        (root / 'a.txt').write_text('a')
        (root / '.hidden').write_text('h')
        files = module.scan_folder(root)
        assert len(files) == 2
        assert files[0].name == 'a.txt'
        assert files[1].name == 'b.txt'


def test_scan_folder_raises_on_missing():
    module = load_module()
    try:
        module.scan_folder('/nonexistent_path_12345')
        assert False
    except FileNotFoundError:
        pass


def test_get_group_key_modes():
    module = load_module()
    p = pathlib.Path('photo.jpg')
    assert module.get_group_key(p, 'suffix') == '.jpg'
    assert module.get_group_key(p, 'type') == '图片'
    assert module.get_group_key(p, 'all') == '全部文件'


def test_build_rename_plan_generates_correct_names():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_text('a')
        (root / 'b.txt').write_text('b')
        (root / 'c.jpg').write_text('c')

        plan = module.build_rename_plan(root, 'Trip', 'all', 'name', 'asc')
        assert len(plan) == 3
        assert plan[0]['target_name'] == 'Trip_001.txt'
        assert plan[1]['target_name'] == 'Trip_002.txt'
        assert plan[2]['target_name'] == 'Trip_003.jpg'


def test_rename_files_executes_plan():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_text('a')
        (root / 'b.txt').write_text('b')

        results = module.rename_files(root, 'Doc', 'all', 'name', 'asc')
        assert len(results) == 2
        assert results[0]['success'] is True
        assert results[0]['target_name'] == 'Doc_001.txt'
        assert (root / 'Doc_001.txt').exists()
        assert (root / 'Doc_002.txt').exists()
        assert not (root / 'a.txt').exists()


def test_rename_files_group_by_suffix():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_text('a')
        (root / 'b.jpg').write_text('b')
        (root / 'c.txt').write_text('c')

        results = module.rename_files(root, 'File', 'suffix', 'name', 'asc')
        assert len(results) == 3
        # jpg group gets 001, txt group gets 001 and 002
        names = {r['source_name']: r['target_name'] for r in results}
        assert names['b.jpg'] == 'File_001.jpg'
        assert names['a.txt'] == 'File_001.txt'
        assert names['c.txt'] == 'File_002.txt'


def test_ensure_no_external_conflicts_raises():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'existing.txt').write_text('x')
        (root / 'a.txt').write_text('a')
        plan = [{'source': str(root / 'a.txt'), 'target_name': 'existing.txt'}]
        try:
            module._ensure_no_external_conflicts(root, plan)
            assert False
        except FileExistsError:
            pass


def test_build_rename_plan_empty_folder():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        plan = module.build_rename_plan(root, 'X', 'all', 'name', 'asc')
        assert plan == []
