import importlib.util
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / '分类' / 'converter.py'


def load_module():
    sys.modules.pop('tests_分类_converter_module', None)
    spec = importlib.util.spec_from_file_location('tests_分类_converter_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_get_category_for_file_returns_correct_category():
    module = load_module()
    assert module.get_category_for_file('photo.jpg') == module.IMAGE_CATEGORY
    assert module.get_category_for_file('clip.mp4') == module.VIDEO_CATEGORY
    assert module.get_category_for_file('doc.pdf') == '文档'
    assert module.get_category_for_file('unknown.zzz') == module.OTHER_CATEGORY


def test_normalize_mode_defaults_to_category():
    module = load_module()
    assert module.normalize_mode(None) == module.MODE_CATEGORY
    assert module.normalize_mode('category') == module.MODE_CATEGORY
    assert module.normalize_mode('resolution') == module.MODE_RESOLUTION
    assert module.normalize_mode('invalid') == module.MODE_CATEGORY


def test_is_sortable_file_rejects_hidden_and_symlinks():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        normal = root / 'normal.txt'
        normal.write_text('x')
        hidden = root / '.hidden'
        hidden.write_text('x')
        assert module.is_sortable_file(normal) is True
        assert module.is_sortable_file(hidden) is False
        assert module.is_sortable_file(root) is False


def test_classify_files_moves_files_into_category_subdirs():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'photo.jpg').write_bytes(b'\xff\xd8')  # fake jpg
        (root / 'video.mp4').write_bytes(b'\x00\x00')
        (root / 'notes.zzx').write_bytes(b'hello')

        results = module.classify_files(root)

        assert len(results) == 3
        assert all(r['success'] for r in results)
        categories = {r['category'] for r in results}
        assert module.IMAGE_CATEGORY in categories
        assert module.VIDEO_CATEGORY in categories
        assert module.OTHER_CATEGORY in categories
        # files should now be in subdirs
        assert (root / module.IMAGE_CATEGORY / 'photo.jpg').exists()
        assert (root / module.VIDEO_CATEGORY / 'video.mp4').exists()
        assert (root / module.OTHER_CATEGORY / 'notes.zzx').exists()


def test_classify_files_empty_directory():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        results = module.classify_files(root)
        assert results == []


def test_classify_files_skips_hidden_files():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / '.hidden.jpg').write_bytes(b'\xff\xd8')
        (root / 'visible.jpg').write_bytes(b'\xff\xd8')
        results = module.classify_files(root)
        assert len(results) == 1
        assert results[0]['source_name'] == 'visible.jpg'


def test_classify_files_with_selected_categories_filter():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'photo.jpg').write_bytes(b'\xff\xd8')
        (root / 'doc.txt').write_bytes(b'hello')
        results = module.classify_files(root, selected_categories=[module.IMAGE_CATEGORY])
        assert len(results) == 1
        assert results[0]['category'] == module.IMAGE_CATEGORY


def test_resolve_folder_raises_on_missing():
    module = load_module()
    try:
        module._resolve_folder('/nonexistent/path_12345')
        assert False, 'Should have raised'
    except FileNotFoundError:
        pass


def test_get_resolution_bucket():
    module = load_module()
    assert module.get_resolution_bucket(320, 240) == '480p及以下'
    assert module.get_resolution_bucket(1280, 720) == '720p'
    assert module.get_resolution_bucket(1920, 1080) == '1080p'
    assert module.get_resolution_bucket(2560, 1440) == '2K'
    assert module.get_resolution_bucket(3840, 2160) == '4K'
    assert module.get_resolution_bucket(7680, 4320) == '8K及以上'


def test_classify_files_handles_name_conflict():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        # pre-create category subdir with a file of the same name
        cat_dir = root / module.IMAGE_CATEGORY
        cat_dir.mkdir()
        (cat_dir / 'photo.jpg').write_bytes(b'existing')
        (root / 'photo.jpg').write_bytes(b'new')

        results = module.classify_files(root, selected_categories=[module.IMAGE_CATEGORY])
        assert len(results) == 1
        assert results[0]['success'] is True
        assert results[0]['renamed'] is True
