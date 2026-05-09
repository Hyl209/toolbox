from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

ROOT = pathlib.Path('PROJECT_ROOT')
MODULE_PATH = ROOT / 'pdf-tools' / 'converter.py'


def load_module():
    sys.modules.pop('pdf_tools_test_module', None)
    spec = importlib.util.spec_from_file_location('pdf_tools_test_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collect_pdf_inputs_filters_supported_extensions_recursively():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.pdf').write_text('x', encoding='utf-8')
        (root / 'b.txt').write_text('x', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'c.PDF').write_text('x', encoding='utf-8')
        paths = mod.collect_pdf_inputs([str(root)])
    assert [p.name for p in paths] == ['a.pdf', 'c.PDF']


def test_parse_page_ranges_supports_single_pages_and_ranges():
    mod = load_module()
    assert mod.parse_page_ranges('1-3,5,7-8', total_pages=10) == [0, 1, 2, 4, 6, 7]


def test_parse_page_ranges_rejects_invalid_values():
    mod = load_module()
    for raw in ['', '0', '3-1', 'a-b', '99']:
        try:
            mod.parse_page_ranges(raw, total_pages=5)
        except ValueError as exc:
            assert '椤电爜' in str(exc)
        else:
            raise AssertionError(f'expected ValueError for {raw!r}')


def test_probe_tesseract_reports_missing_dependency_cleanly():
    mod = load_module()
    original = mod.shutil.which
    try:
        mod.shutil.which = lambda _name: None
        available, message = mod.probe_tesseract()
    finally:
        mod.shutil.which = original
    assert available is False
    assert 'Tesseract' in message


def test_build_pdf_output_path_uses_source_stem_and_suffix():
    mod = load_module()
    output = mod.build_pdf_output_path(pathlib.Path('/tmp/demo/input.pdf'), pathlib.Path('/tmp/out'), '.docx')
    assert output == pathlib.Path('/tmp/out/input.docx')


def test_extract_strategy_prefers_text_layer_then_ocr():
    mod = load_module()
    assert mod.choose_text_extraction_mode('hello world', True) == 'text'
    assert mod.choose_text_extraction_mode('   ', True) == 'ocr'
    assert mod.choose_text_extraction_mode('', False) == 'empty'


def test_merge_pdfs_requires_at_least_two_inputs():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        one = pathlib.Path(tmp) / 'a.pdf'
        one.write_bytes(b'%PDF-1.4')
        try:
            mod.merge_pdfs([one], pathlib.Path(tmp) / 'merged.pdf')
        except mod.PdfToolsError as exc:
            assert '鑷冲皯' in str(exc)
        else:
            raise AssertionError('expected PdfToolsError for single input merge')


def test_split_output_paths_follow_page_numbers():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        outputs = mod.build_split_output_paths(pathlib.Path('/tmp/demo/input.pdf'), pathlib.Path(tmp), [0, 2, 4])
    assert [p.name for p in outputs] == ['input_page_001.pdf', 'input_page_003.pdf', 'input_page_005.pdf']


def test_build_image_output_paths_follow_page_numbers_and_format():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        outputs = mod.build_image_output_paths(pathlib.Path('/tmp/demo/input.pdf'), pathlib.Path(tmp), 3, 'png')
    assert [p.name for p in outputs] == ['input_page_001.png', 'input_page_002.png', 'input_page_003.png']


def test_validate_pdf_action_rejects_wrong_input_counts():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        one = pathlib.Path(tmp) / 'a.pdf'
        two = pathlib.Path(tmp) / 'b.pdf'
        one.write_bytes(b'%PDF-1.4')
        two.write_bytes(b'%PDF-1.4')
        assert '璇烽€夋嫨鑷冲皯涓や釜 PDF 鏂囦欢' in mod.validate_pdf_action('merge', [one], '')
        assert '鎷嗗垎鍔熻兘鍙敮鎸佸崟涓?PDF' in mod.validate_pdf_action('split', [one, two], '1-2')
        assert '璇疯緭鍏ユ媶鍒嗛〉鐮佽寖鍥? in mod.validate_pdf_action('split', [one], '')


def test_merge_pdfs_writes_output_via_writer_when_inputs_valid():
    mod = load_module()

    class FakeReader:
        def __init__(self, path):
            self.path = pathlib.Path(path)
            self.pages = [f'{self.path.name}-page1']

    class FakeWriter:
        def __init__(self):
            self.added = []
        def add_page(self, page):
            self.added.append(page)
        def write(self, stream):
            stream.write(b'merged-pdf')

    mod.PdfReader = FakeReader
    mod.PdfWriter = FakeWriter
    with tempfile.TemporaryDirectory() as tmp:
        a = pathlib.Path(tmp) / 'a.pdf'
        b = pathlib.Path(tmp) / 'b.pdf'
        out = pathlib.Path(tmp) / 'merged.pdf'
        a.write_bytes(b'%PDF-1.4')
        b.write_bytes(b'%PDF-1.4')
        result = mod.merge_pdfs([a, b], out)
        assert result == out
        assert out.read_bytes() == b'merged-pdf'


def test_split_pdf_writes_selected_pages_via_writer():
    mod = load_module()

    class FakeReader:
        def __init__(self, path):
            self.pages = ['p1', 'p2', 'p3']

    class FakeWriter:
        written = []
        def __init__(self):
            self.added = []
        def add_page(self, page):
            self.added.append(page)
        def write(self, stream):
            FakeWriter.written.append(list(self.added))
            stream.write(b'page-pdf')

    mod.PdfReader = FakeReader
    mod.PdfWriter = FakeWriter
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        outputs = mod.split_pdf(source, pathlib.Path(tmp), [0, 2])
        assert [p.name for p in outputs] == ['input_page_001.pdf', 'input_page_003.pdf']
        assert FakeWriter.written == [['p1'], ['p3']]


def test_pdf_to_images_requires_renderer_dependency():
    mod = load_module()
    mod.fitz = None
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        try:
            mod.pdf_to_images(source, pathlib.Path(tmp), 'png', 150)
        except mod.PdfToolsError as exc:
            assert 'PyMuPDF' in str(exc)
        else:
            raise AssertionError('expected PdfToolsError when fitz missing')


def test_pdf_to_images_writes_rendered_pages_when_fitz_available():
    mod = load_module()

    class FakePixmap:
        def __init__(self, page_no):
            self.page_no = page_no
        def save(self, path):
            pathlib.Path(path).write_bytes(f'image-{self.page_no}'.encode('utf-8'))

    class FakePage:
        def __init__(self, page_no):
            self.page_no = page_no
            self.last_matrix = None
        def get_pixmap(self, matrix=None, alpha=False):
            self.last_matrix = matrix
            return FakePixmap(self.page_no)

    class FakeDocument:
        def __init__(self):
            self.pages = [FakePage(1), FakePage(2)]
        def __iter__(self):
            return iter(self.pages)
        def close(self):
            self.closed = True

    opened = FakeDocument()

    class FakeMatrix:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class FakeFitz:
        Matrix = FakeMatrix
        @staticmethod
        def open(_path):
            return opened

    mod.fitz = FakeFitz
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        outputs = mod.pdf_to_images(source, pathlib.Path(tmp), 'png', 144)
        assert [p.name for p in outputs] == ['input_page_001.png', 'input_page_002.png']
        assert outputs[0].read_bytes() == b'image-1'
        assert outputs[1].read_bytes() == b'image-2'
        assert opened.pages[0].last_matrix.x == 2.0
        assert opened.pages[0].last_matrix.y == 2.0


def test_export_text_writes_txt_when_text_layer_available():
    mod = load_module()

    class FakePage:
        def get_text(self, mode='text'):
            return '绗竴椤垫枃瀛?

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage()])
        def close(self):
            pass

    class FakeFitz:
        @staticmethod
        def open(_path):
            return FakeDocument()

    mod.fitz = FakeFitz
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        output = mod.export_pdf_text(source, pathlib.Path(tmp), 'txt')
        assert output.name == 'input.txt'
        assert output.read_text(encoding='utf-8') == '绗竴椤垫枃瀛?


def test_export_text_uses_ocr_fallback_when_enabled_and_text_blank():
    mod = load_module()

    class FakePage:
        def __init__(self, page_no):
            self.page_no = page_no
        def get_text(self, mode='text'):
            return '   '
        def get_pixmap(self, matrix=None, alpha=False):
            class FakePixmap:
                def save(self, path):
                    pathlib.Path(path).write_bytes(b'img')
            return FakePixmap()

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage(1)])
        def close(self):
            pass

    class FakeMatrix:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class FakeFitz:
        Matrix = FakeMatrix
        @staticmethod
        def open(_path):
            return FakeDocument()

    mod.fitz = FakeFitz
    mod.probe_tesseract = lambda: (True, '')
    mod.run_ocr_on_image = lambda _path: 'OCR鏂囧瓧'
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        output = mod.export_pdf_text(source, pathlib.Path(tmp), 'txt', ocr_fallback=True)
        assert output.read_text(encoding='utf-8') == 'OCR鏂囧瓧'


def test_export_text_requires_docx_dependency_for_word_output():
    mod = load_module()
    mod.Document = None

    class FakePage:
        def get_text(self, mode='text'):
            return '绗竴椤垫枃瀛?

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage()])
        def close(self):
            pass

    class FakeFitz:
        @staticmethod
        def open(_path):
            return FakeDocument()

    mod.fitz = FakeFitz
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / 'input.pdf'
        source.write_bytes(b'%PDF-1.4')
        try:
            mod.export_pdf_text(source, pathlib.Path(tmp), 'docx')
        except mod.PdfToolsError as exc:
            assert 'python-docx' in str(exc)
        else:
            raise AssertionError('expected PdfToolsError when python-docx missing')

