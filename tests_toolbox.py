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


def test_tool_definitions_include_image_convert_and_pdf_tools():
    toolbox = load_module()
    titles = [item['title'] for item in toolbox.get_tool_definitions()]
    assert '鍥剧墖鏍煎紡浜掕浆' in titles
    assert 'PDF宸ュ叿' in titles


def test_get_image_convert_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_image_convert_module()
    assert hasattr(module, 'convert_image')
    assert hasattr(module, 'validate_target_size_kb')


def test_get_pdf_tools_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_pdf_tools_module()
    assert hasattr(module, 'merge_pdfs')
    assert hasattr(module, 'pdf_to_images')
    assert hasattr(module, 'export_pdf_text')


def test_validate_pdf_form_requires_output_and_extra_fields_for_text_actions():
    toolbox = load_module()
    errors = toolbox.validate_pdf_form('text', [], '', '', '', '150')
    assert '璇ュ姛鑳藉彧鏀寔鍗曚釜 PDF' in errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors


def test_build_main_window_sidebar_includes_image_convert_and_pdf_tab_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
        assert '鍥剧墖鏍煎紡浜掕浆' in sidebar_titles
        assert 'PDF宸ュ叿' in sidebar_titles
        assert window.stack.count() == 5
        window.close()
        app.quit()

