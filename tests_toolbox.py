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


def test_tool_definitions_include_image_convert_pdf_and_base64_tools():
    toolbox = load_module()
    titles = [item['title'] for item in toolbox.get_tool_definitions()]
    assert '鍥剧墖鏍煎紡浜掕浆' in titles
    assert 'PDF宸ュ叿' in titles
    assert '鍥剧墖Base64' in titles


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


def test_get_base64_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_base64_module()
    assert hasattr(module, 'encode_image_to_base64')
    assert hasattr(module, 'decode_base64_to_file')


def test_validate_pdf_form_requires_output_and_extra_fields_for_text_actions():
    toolbox = load_module()
    errors = toolbox.validate_pdf_form('text', [], '', '', '', '150')
    assert '璇ュ姛鑳藉彧鏀寔鍗曚釜 PDF' in errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors


def test_build_main_window_sidebar_includes_image_convert_pdf_and_base64_tab_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
        assert '鍥剧墖鏍煎紡浜掕浆' in sidebar_titles
        assert 'PDF宸ュ叿' in sidebar_titles
        assert '鍥剧墖Base64' in sidebar_titles
        assert window.stack.count() == 6
        assert bool(window.windowFlags() & toolbox.Qt.FramelessWindowHint)
        assert window.drag_bar.minimumHeight() == 34
        assert window.drag_bar.maximumHeight() == 34
        assert window.drag_bar.layout().contentsMargins().top() == 7
        assert window.drag_bar.layout().contentsMargins().right() == 20
        assert window.centralWidget().property('windowSurface') is True
        assert window.centralWidget().layout().contentsMargins().left() == 10
        assert window.content_surface.property('contentSurface') is True
        assert window.centralWidget().graphicsEffect() is None
        assert not hasattr(toolbox, 'QPainterPath') or toolbox.QPainterPath is None
        assert window.window_controls_layout.count() == 3
        assert hasattr(window, 'max_button')
        assert window.max_button is not None
        assert window.min_button.toolTip() == '鏈€灏忓寲'
        assert window.max_button.toolTip() in {'鏈€澶у寲', '杩樺師'}
        assert window.close_button.toolTip() == '鍏抽棴'
        assert window.min_button.width() == 24
        assert window.min_button.height() == 24
        assert window.sidebar.width() == 196
        assert 'Clean local toolbox' in window.findChildren(toolbox.QLabel)[1].text()
        stylesheet = toolbox.get_theme_stylesheet(window.current_theme)
        assert 'background-color: #1b1f25;' in toolbox.DARK_STYLESHEET
        assert 'background-color: #e5e9ef;' in toolbox.LIGHT_STYLESHEET
        assert "QWidget[contentSurface='true']" in toolbox.DARK_STYLESHEET
        assert "QWidget[contentSurface='true']" in toolbox.LIGHT_STYLESHEET
        assert 'border-radius: 32px;' in toolbox.DARK_STYLESHEET
        assert 'border-radius: 32px;' in toolbox.LIGHT_STYLESHEET
        assert "QFrame[dragBar='true']" in toolbox.DARK_STYLESHEET
        assert "QPushButton[windowControl='true']" in toolbox.DARK_STYLESHEET
        assert '#9aa6b5' in toolbox.DARK_STYLESHEET
        assert '#d8dee7' in toolbox.LIGHT_STYLESHEET
        assert 'background-color: #2a3038;' in toolbox.DARK_STYLESHEET
        assert 'QComboBox::drop-down {' in toolbox.DARK_STYLESHEET
        assert 'width: 26px;' in toolbox.DARK_STYLESHEET
        assert 'background: transparent;' in toolbox.DARK_STYLESHEET
        assert 'arrow-dark.svg' in toolbox.DARK_STYLESHEET
        assert 'arrow-light.svg' in toolbox.LIGHT_STYLESHEET
        assert 'padding: 8px 48px 8px 16px;' in toolbox.DARK_STYLESHEET
        assert 'background-color: rgba(44, 50, 59, 0.88);' in toolbox.DARK_STYLESHEET
        assert 'border: 1px solid #3f4652;' in toolbox.DARK_STYLESHEET
        assert 'background-color: #eef1f5;' in toolbox.LIGHT_STYLESHEET
        assert 'QComboBox::drop-down {' in toolbox.LIGHT_STYLESHEET
        assert 'border: 1px solid #d9dfe7;' in toolbox.LIGHT_STYLESHEET
        assert window.image_convert_tab.format_combo.minimumWidth() == 132
        assert window.image_convert_tab.jpg_background_combo.minimumWidth() == 154
        assert window.image_convert_tab.jpg_background_combo.itemText(0) == '鐧借壊'
        assert window.image_convert_tab.jpg_background_combo.itemText(1) == '榛戣壊'
        assert not window.image_convert_tab.format_combo.isEditable()
        assert not window.image_convert_tab.jpg_background_combo.isEditable()
        assert window.pdf_tools_tab.action_combo.minimumWidth() == 132
        assert window.pdf_tools_tab.image_format_combo.minimumWidth() == 132
        assert window.pdf_tools_tab.action_combo.itemText(0) == '鍚堝苟'
        assert window.pdf_tools_tab.action_combo.itemText(2) == '杞浘鐗?
        assert not window.pdf_tools_tab.action_combo.isEditable()
        assert not window.pdf_tools_tab.image_format_combo.isEditable()
        assert window.base64_tab.mode_combo.minimumWidth() == 144
        assert window.base64_tab.mode_combo.itemText(0) == '鍥剧墖杞珺ase64'
        assert window.base64_tab.mode_combo.itemText(1) == 'Base64杞浘鐗?
        assert not window.base64_tab.mode_combo.isEditable()
        initial_maximized = window.isMaximized()
        window.toggle_max_restore()
        assert window.isMaximized() != initial_maximized
        window.toggle_max_restore()
        assert window.isMaximized() == initial_maximized
        window.close()
        app.quit()

