import importlib.util
import pathlib
import tempfile
import sys

ROOT = pathlib.Path('PROJECT_ROOT')
MODULE_PATH = ROOT / 'hyl_toolbox.py'


def load_module():
    sys.modules.pop('tests_tool_pages_module', None)
    spec = importlib.util.spec_from_file_location('tests_tool_pages_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collect_music_inputs_filters_to_ncm_only():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.ncm').write_text('x', encoding='utf-8')
        (root / 'b.mp3').write_text('y', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'c.ncm').write_text('z', encoding='utf-8')
        paths = toolbox.collect_music_inputs([str(root)])
    assert [p.name for p in paths] == ['a.ncm', 'c.ncm']


def test_music_drop_summary_shows_selected_files_in_same_area():
    toolbox = load_module()
    assert toolbox.format_music_drop_summary([]) == '鎷栧叆 .ncm 鏂囦欢鎴栨枃浠跺す'
    one = toolbox.format_music_drop_summary([pathlib.Path('demo.ncm')])
    assert '宸叉坊鍔?1 棣栨瓕鏇? in one
    assert 'demo' in one
    many = toolbox.format_music_drop_summary([
        pathlib.Path('a.ncm'),
        pathlib.Path('b.ncm'),
        pathlib.Path('c.ncm'),
    ])
    assert '宸叉坊鍔?3 棣栨瓕鏇? in many
    assert 'a' in many and 'b' in many
    assert '.ncm' not in many


def test_collect_mp4_inputs_filters_nested_mp4_only():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'movie.mp4').write_text('x', encoding='utf-8')
        (root / 'ignore.mov').write_text('y', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'clip.mp4').write_text('z', encoding='utf-8')
        paths = toolbox.collect_mp4_inputs([str(root)])
        assert [p.name for p in paths] == ['movie.mp4', 'clip.mp4']


def test_get_mp4_module_loads_converter_with_local_config_dependency():
    toolbox = load_module()
    module = toolbox.get_mp4_module()
    assert hasattr(module, 'convert_mp4_to_mp3')


def test_app_dir_uses_source_dir_when_not_frozen():
    toolbox = load_module()
    assert toolbox.APP_DIR == pathlib.Path('PROJECT_ROOT')


def test_mp4_drop_summary_shows_selected_videos_in_same_area():
    toolbox = load_module()
    assert toolbox.format_mp4_drop_summary([]) == '鎷栧叆 .mp4 鏂囦欢鎴栨枃浠跺す'
    one = toolbox.format_mp4_drop_summary([pathlib.Path('lesson.mp4')])
    assert '宸叉坊鍔?1 涓棰? in one
    assert 'lesson' in one
    many = toolbox.format_mp4_drop_summary([
        pathlib.Path('a.mp4'),
        pathlib.Path('b.mp4'),
        pathlib.Path('c.mp4'),
    ])
    assert '宸叉坊鍔?3 涓棰? in many
    assert 'a' in many and 'b' in many
    assert '.mp4' not in many


def test_validate_mp4_form_requires_files_and_output_dir():
    toolbox = load_module()
    errors = toolbox.validate_mp4_form([], '')
    assert '璇峰厛娣诲姞瑕佽浆鎹㈢殑 .mp4 鏂囦欢' in errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors


def test_split_dropped_files_accepts_jpg_cover_and_payload():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        payload = root / 'secret.zip'
        cover = root / 'cover.jpg'
        payload.write_text('x', encoding='utf-8')
        cover.write_text('y', encoding='utf-8')
        result = toolbox.split_dropped_files([str(payload), str(cover)])
        assert result['payload'].endswith('secret.zip')
        assert result['cover_png'].endswith('cover.jpg')


def test_validate_zipandpng_form_accepts_non_png_cover_extension():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        payload = root / 'secret.zip'
        cover = root / 'cover.webp'
        payload.write_text('x', encoding='utf-8')
        cover.write_text('y', encoding='utf-8')
        errors = toolbox.validate_zipandpng_form(str(payload), str(cover), str(root), 'demo.png')
        assert errors == []


def test_choose_output_suffix_follows_cover_extension():
    toolbox = load_module()
    assert toolbox.choose_output_suffix('cover.jpg') == '.jpg'
    assert toolbox.choose_output_suffix('cover.jpeg') == '.jpeg'
    assert toolbox.choose_output_suffix('cover.gif') == '.gif'
    assert toolbox.choose_output_suffix('cover.webp') == '.webp'
    assert toolbox.choose_output_suffix('cover.png') == '.png'
    assert toolbox.choose_output_suffix('') == '.png'


def test_normalize_output_name_uses_payload_name_and_cover_suffix():
    toolbox = load_module()
    assert toolbox.normalize_output_name('secret', 'cover.jpg') == 'secret.jpg'
    assert toolbox.normalize_output_name('secret.png', 'cover.webp') == 'secret.webp'
    assert toolbox.normalize_output_name('', 'cover.gif', 'archive.zip') == 'archive.gif'


def test_format_drop_card_text_shows_payload_filename():
    toolbox = load_module()
    assert toolbox.format_drop_card_text('', '鎷栧叆鏂囦欢') == '鎷栧叆鏂囦欢'
    text = toolbox.format_drop_card_text('/tmp/demo/archive.zip', '鎷栧叆鏂囦欢')
    assert text == 'archive.zip'


def test_collect_image_convert_inputs_filters_supported_images_only():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.jpg').write_text('x', encoding='utf-8')
        (root / 'b.txt').write_text('y', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'c.heic').write_text('z', encoding='utf-8')
        paths = toolbox.collect_image_convert_inputs([str(root)])
    assert [p.name for p in paths] == ['a.jpg', 'c.heic']


def test_image_convert_drop_summary_shows_selected_images_in_same_area():
    toolbox = load_module()
    assert toolbox.format_image_convert_drop_summary([]) == '鎷栧叆 JPG / PNG / WebP / HEIC 鍥剧墖鎴栨枃浠跺す'
    one = toolbox.format_image_convert_drop_summary([pathlib.Path('cover.png')])
    assert '宸叉坊鍔?1 寮犲浘鐗? in one
    assert 'cover' in one


def test_validate_image_convert_form_requires_files_output_format_and_valid_numbers():
    toolbox = load_module()
    errors = toolbox.validate_image_convert_form([], '', '', '0', 'abc')
    assert '璇峰厛娣诲姞瑕佽浆鎹㈢殑鍥剧墖' in errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors
    assert '璇烽€夋嫨杈撳嚭鏍煎紡' in errors
    assert '璐ㄩ噺蹇呴』鍦?1 鍒?100 涔嬮棿' in errors
    assert any('鐩爣澶у皬' in item for item in errors)


def test_validate_image_convert_form_accepts_valid_target_size():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        image = pathlib.Path(tmp) / 'demo.png'
        image.write_text('x', encoding='utf-8')
        errors = toolbox.validate_image_convert_form([image], tmp, 'webp', '85', '128')
    assert errors == []


def test_validate_pdf_form_requires_text_options_for_text_export():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        pdf = pathlib.Path(tmp) / 'demo.pdf'
        pdf.write_bytes(b'%PDF-1.4')
        errors = toolbox.validate_pdf_form('text', [pdf], '', '', '', '', '')
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors
    assert '璇烽€夋嫨鏂囨湰瀵煎嚭鏍煎紡' in errors


def test_validate_pdf_form_accepts_valid_text_export():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        pdf = pathlib.Path(tmp) / 'demo.pdf'
        pdf.write_bytes(b'%PDF-1.4')
        errors = toolbox.validate_pdf_form('text', [pdf], tmp, '', '', '', 'txt')
    assert errors == []


def test_collect_base64_image_inputs_filters_supported_images_only():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.png').write_text('x', encoding='utf-8')
        (root / 'b.txt').write_text('y', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'c.webp').write_text('z', encoding='utf-8')
        paths = toolbox.collect_base64_image_inputs([str(root)])
    assert [p.name for p in paths] == ['a.png']


def test_base64_drop_summary_shows_selected_images():
    toolbox = load_module()
    assert toolbox.format_base64_drop_summary([]) == '鎷栧叆 PNG / JPG / JPEG / WebP / GIF / BMP 鍥剧墖'
    one = toolbox.format_base64_drop_summary([pathlib.Path('cover.png')])
    assert '宸叉坊鍔?1 寮犲浘鐗? in one
    assert 'cover.png' in one


def test_validate_base64_form_requires_mode_specific_inputs():
    toolbox = load_module()
    encode_errors = toolbox.validate_base64_form('encode', [], '', '', '')
    assert '璇峰厛娣诲姞瑕佽浆鎹㈢殑鍥剧墖' in encode_errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in encode_errors
    assert '璇疯緭鍏ヨ緭鍑烘枃浠跺悕' in encode_errors
    decode_errors = toolbox.validate_base64_form('decode', [], '', '', '')
    assert '璇疯緭鍏?Base64 鍐呭' in decode_errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in decode_errors


def test_validate_base64_form_accepts_valid_encode_request():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        image = pathlib.Path(tmp) / 'demo.png'
        image.write_text('x', encoding='utf-8')
        errors = toolbox.validate_base64_form('encode', [image], '', tmp, 'demo')
    assert errors == []

