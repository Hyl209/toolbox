import pathlib

SPEC_PATH = pathlib.Path('PROJECT_ROOT/HylToolbox.spec')


def test_spec_includes_pdf_tools_converter_data_file():
    content = SPEC_PATH.read_text(encoding='utf-8')
    assert "('modules/pdf-tools/converter.py', 'modules/pdf-tools')" in content

