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
    assert toolbox.format_music_drop_summary([]) == '鎷栧叆ncm鏂囦欢'
    one = toolbox.format_music_drop_summary([pathlib.Path('demo.ncm')])
    assert one == '鎷栧叆ncm鏂囦欢'
    many = toolbox.format_music_drop_summary([
        pathlib.Path('a.ncm'),
        pathlib.Path('b.ncm'),
        pathlib.Path('c.ncm'),
    ])
    assert many == '鎷栧叆ncm鏂囦欢'


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
    assert toolbox.APP_DIR == pathlib.Path(toolbox.__file__).resolve().parent


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


def test_image_convert_and_base64_drop_zones_preview_first_image_in_source():
    source = MODULE_PATH.read_text(encoding='utf-8')
    assert "self.drop_zone.set_preview_image(" in source
    assert "body_text=picked.name" in source
    assert source.count("body_text=picked.name") >= 2


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


def test_format_video_download_task_summary_counts_mixed_links():
    toolbox = load_module()
    text = '\n'.join([
        'https://t.me/demo/123',
        'https://t.me/demo',
        'https://example.com/watch?v=1',
    ])
    summary = toolbox.format_video_download_task_summary(text)
    assert '鍏?3 涓换鍔? in summary
    assert 'Telegram 娑堟伅: 1' in summary
    assert 'Telegram 缇?棰戦亾: 1' in summary
    assert '缃戦〉瑙嗛: 1' in summary


def test_validate_video_downloader_form_requires_output_and_telegram_credentials():
    toolbox = load_module()
    errors = toolbox.validate_video_downloader_form(
        'https://t.me/demo/1',
        '',
        '',
        '',
        '',
        '500',
        False,
        '',
        '',
        True,
        False,
    )
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors
    assert '璇疯緭鍏?Telegram API ID' in errors
    assert '璇疯緭鍏?Telegram API Hash' in errors
    assert '璇疯緭鍏?Telegram 鎵嬫満鍙? in errors


def test_validate_video_downloader_form_accepts_web_only_task_without_telegram_credentials():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = toolbox.validate_video_downloader_form(
            'https://example.com/video',
            tmp,
            '',
            '',
            '',
            '500',
            False,
            '',
            '',
            True,
            False,
        )
    assert errors == []


def test_validate_video_downloader_form_rejects_invalid_date_and_empty_media_selection():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = toolbox.validate_video_downloader_form(
            'https://t.me/demo',
            tmp,
            '1',
            'hash',
            '+123',
            '500',
            False,
            '2026/01/01',
            '',
            False,
            False,
            '',
            False,
        )
    assert '寮€濮嬫棩鏈熷繀椤绘槸 YYYY-MM-DD 鏍煎紡' in errors
    assert 'Telegram 浠诲姟鑷冲皯瑕佸嬀閫変竴绉嶄笅杞界被鍨? in errors


def test_validate_video_downloader_form_rejects_invalid_web_candidate_index():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = toolbox.validate_video_downloader_form(
            'https://example.com/post/1',
            tmp,
            '',
            '',
            '',
            '500',
            False,
            '',
            '',
            True,
            False,
            '0',
            False,
        )
    assert '缃戦〉鍊欓€夊簭鍙峰繀椤诲ぇ浜?0' in errors


def test_validate_file_sorter_form_requires_existing_folder():
    toolbox = load_module()
    assert '璇烽€夋嫨闇€瑕佸垎绫荤殑鏂囦欢澶? in toolbox.validate_file_sorter_form('')
    errors = toolbox.validate_file_sorter_form('Z:/not-found-folder')
    assert '閫夋嫨鐨勬枃浠跺す涓嶅瓨鍦? in errors


def test_validate_batch_rename_form_requires_existing_folder_and_prefix():
    toolbox = load_module()
    assert '璇烽€夋嫨闇€瑕佹壒閲忓懡鍚嶇殑鏂囦欢澶? in toolbox.validate_batch_rename_form('', '')
    errors = toolbox.validate_batch_rename_form('Z:/not-found-folder', '')
    assert '閫夋嫨鐨勬枃浠跺す涓嶅瓨鍦? in errors
    assert '璇疯緭鍏ュ懡鍚嶅墠缂€' in errors


def test_validate_same_form_requires_existing_folder():
    toolbox = load_module()
    assert '璇烽€夋嫨闇€瑕佹娴嬬殑鏂囦欢澶? in toolbox.validate_same_form('')
    errors = toolbox.validate_same_form('Z:/not-found-folder')
    assert '閫夋嫨鐨勬枃浠跺す涓嶅瓨鍦? in errors


def test_file_sorter_summary_only_counts_first_level_files():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'cover.jpg').write_text('x', encoding='utf-8')
        (root / 'movie.mp4').write_text('x', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'inside.png').write_text('x', encoding='utf-8')
        summary = module.summarize_folder(root)
        assert summary['total_files'] == 2
        assert summary['category_counts']['鍥剧墖'] == 1
        assert summary['category_counts']['瑙嗛'] == 1
        assert summary['category_counts']['鍏朵粬'] == 0
        text = toolbox.format_file_sorter_summary(summary)
        assert '褰撳墠鐩綍绗竴灞傚叡 2 涓枃浠? in text
        assert '鍥剧墖: 1' in text
        assert '瑙嗛: 1' in text


def test_file_sorter_classifies_files_creates_category_dirs_and_auto_renames():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'cover.jpg').write_text('img', encoding='utf-8')
        (root / 'movie.mp4').write_text('video', encoding='utf-8')
        (root / 'song.ncm').write_text('audio', encoding='utf-8')
        (root / 'report.pdf').write_text('doc', encoding='utf-8')
        (root / 'archive.zip').write_text('zip', encoding='utf-8')
        (root / 'tool.py').write_text('py', encoding='utf-8')
        (root / 'notes.xyz').write_text('other', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'inside.jpg').write_text('nested', encoding='utf-8')
        existing_doc_dir = root / '鏂囨。'
        existing_doc_dir.mkdir()
        (existing_doc_dir / 'report.pdf').write_text('existing', encoding='utf-8')

        results = module.classify_files(root)

        assert len(results) == 7
        assert (root / '鍥剧墖' / 'cover.jpg').exists()
        assert (root / '瑙嗛' / 'movie.mp4').exists()
        assert (root / '闊抽' / 'song.ncm').exists()
        assert (root / '鏂囨。' / 'report(1).pdf').exists()
        assert (root / '鍘嬬缉鍖? / 'archive.zip').exists()
        assert (root / '绋嬪簭' / 'tool.py').exists()
        assert (root / '鍏朵粬' / 'notes.xyz').exists()
        assert (nested / 'inside.jpg').exists()
        renamed = next(item for item in results if item['source_name'] == 'report.pdf')
        assert renamed['success'] is True
        assert renamed['renamed'] is True
        assert renamed['target_name'] == 'report(1).pdf'


def test_file_sorter_summary_respects_selected_categories():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'cover.jpg').write_text('x', encoding='utf-8')
        (root / 'movie.mp4').write_text('x', encoding='utf-8')
        (root / 'song.mp3').write_text('x', encoding='utf-8')
        video_category = module.CATEGORY_ORDER[1]
        summary = module.summarize_folder(root, [video_category])
        assert summary['total_files'] == 3
        assert summary['selected_total_files'] == 1
        assert tuple(summary['selected_categories']) == (video_category,)
        text = toolbox.format_file_sorter_summary(summary)
        assert '1' in text


def test_file_sorter_only_moves_selected_categories():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'cover.jpg').write_text('img', encoding='utf-8')
        (root / 'movie.mp4').write_text('video', encoding='utf-8')
        (root / 'song.mp3').write_text('audio', encoding='utf-8')
        video_category = module.CATEGORY_ORDER[1]

        results = module.classify_files(root, [video_category])

        assert len(results) == 1
        assert results[0]['source_name'] == 'movie.mp4'
        assert (root / video_category / 'movie.mp4').exists()
        assert (root / 'cover.jpg').exists()
        assert (root / 'song.mp3').exists()


def test_video_downloader_tab_source_contains_log_recent_limit_and_status_controls():
    source = (ROOT / 'video-downloader' / 'tab.py').read_text(encoding='utf-8')
    assert "make_card('涓嬭浇浠诲姟')" in source
    assert "make_card('TG 涓嬭浇')" in source
    assert "make_card('缃戦〉瑙嗛涓嬭浇')" in source
    assert 'self.backend_status_label' in source
    assert 'self.recent_count_edit' in source
    assert 'self.all_messages_checkbox' in source
    assert 'self.date_from_edit' in source
    assert 'self.date_to_edit' in source
    assert 'self.include_video_checkbox' in source
    assert 'self.include_photo_checkbox' in source
    assert 'self.log = QPlainTextEdit()' in source
    assert 'self.progress_bar = QProgressBar()' in source
    assert 'class DownloadWorker' in source
    assert "elif kind == 'tg_scan':" in source
    assert "elif kind == 'file':" in source
    assert 'self.web_candidate_index_edit' in source
    assert 'self.web_all_candidates_checkbox' in source
    assert 'self.send_code_button' in source
    assert 'self.check_status_button' in source


def test_file_sorter_scan_folder_skips_dotfiles_and_desktop_ini():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'visible.txt').write_text('ok', encoding='utf-8')
        (root / '.secret.txt').write_text('hidden', encoding='utf-8')
        (root / 'desktop.ini').write_text('system-ish', encoding='utf-8')
        scanned = module.scan_folder(root)
        assert [item.name for item in scanned] == ['visible.txt']


def test_file_sorter_scan_folder_skips_symlinks_when_supported():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        target = root / 'real.txt'
        target.write_text('ok', encoding='utf-8')
        link = root / 'real-link.txt'
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            return
        scanned = module.scan_folder(root)
        assert len(scanned) == 1
        assert scanned[0].name == 'real.txt'


def test_file_sorter_resolve_name_conflict_has_max_attempt_limit():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        base = root / 'report.pdf'
        base.write_text('x', encoding='utf-8')
        (root / 'report(1).pdf').write_text('x', encoding='utf-8')
        try:
            module.resolve_name_conflict(base, max_attempts=1)
        except RuntimeError as exc:
            assert '鏈€澶у皾璇曟鏁? in str(exc)
        else:
            raise AssertionError('expected rename attempt limit error')


def test_file_sorter_classify_files_captures_target_dir_creation_error():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        video_category = module.CATEGORY_ORDER[1]
        (root / 'movie.mp4').write_text('video', encoding='utf-8')
        (root / video_category).write_text('conflict', encoding='utf-8')
        results = module.classify_files(root, [video_category])
        assert len(results) == 1
        assert results[0]['success'] is False
        assert results[0]['source_name'] == 'movie.mp4'
        assert (root / 'movie.mp4').exists()


def test_batch_rename_plan_supports_group_sort_and_order_choices():
    toolbox = load_module()
    module = toolbox.get_name_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        small = root / 'alpha.mp4'
        medium = root / 'beta.mkv'
        large = root / 'gamma.mp4'
        small.write_bytes(b'a')
        medium.write_bytes(b'bb')
        large.write_bytes(b'ccc')

        plan = module.build_rename_plan(root, '瑙嗛', 'suffix', 'size', 'desc')

        plan_by_source = {item['source_name']: item for item in plan}
        assert plan_by_source['gamma.mp4']['target_name'] == '瑙嗛_001.mp4'
        assert plan_by_source['alpha.mp4']['target_name'] == '瑙嗛_002.mp4'
        assert plan_by_source['beta.mkv']['target_name'] == '瑙嗛_001.mkv'


def test_batch_rename_plan_supports_type_grouping_and_name_sort():
    toolbox = load_module()
    module = toolbox.get_name_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'b.png').write_text('img', encoding='utf-8')
        (root / 'a.jpg').write_text('img', encoding='utf-8')
        (root / 'c.mp3').write_text('audio', encoding='utf-8')

        plan = module.build_rename_plan(root, '璧勬簮', 'type', 'name', 'asc')

        assert [item['group_key'] for item in plan] == ['鍥剧墖', '鍥剧墖', '闊抽']
        assert [item['target_name'] for item in plan] == ['璧勬簮_001.jpg', '璧勬簮_002.png', '璧勬簮_001.mp3']


def test_batch_rename_files_renames_first_level_files_only_and_keeps_continuous_numbers():
    toolbox = load_module()
    module = toolbox.get_name_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        nested = root / 'nested'
        nested.mkdir()
        (root / 'c.txt').write_text('1', encoding='utf-8')
        (root / 'a.txt').write_text('2', encoding='utf-8')
        (nested / 'inside.txt').write_text('3', encoding='utf-8')

        results = module.rename_files(root, '鏂囨。', 'all', 'name', 'asc')

        assert [item['target_name'] for item in results] == ['鏂囨。_001.txt', '鏂囨。_002.txt']
        assert (root / '鏂囨。_001.txt').exists()
        assert (root / '鏂囨。_002.txt').exists()
        assert (nested / 'inside.txt').exists()


def test_batch_rename_detects_external_target_conflict_before_changing_files():
    toolbox = load_module()
    module = toolbox.get_name_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'b.txt').write_text('one', encoding='utf-8')
        (root / 'a.txt').write_text('two', encoding='utf-8')
        (root / '鎵归噺_001.txt').mkdir()

        try:
            module.rename_files(root, '鎵归噺', 'all', 'name', 'asc')
        except FileExistsError as exc:
            assert '鐩爣鏂囦欢宸插瓨鍦? in str(exc)
        else:
            raise AssertionError('expected external conflict error')
        assert (root / 'a.txt').exists()
        assert (root / 'b.txt').exists()


def test_same_module_groups_only_same_suffix_and_keeps_first_file():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        (root / 'b.txt').write_bytes(b'duplicate')
        (root / 'c.md').write_bytes(b'duplicate')
        (root / 'd.txt').write_bytes(b'unique')

        result = module.find_duplicate_groups(root, recursive=False)

        assert result['scanned_files'] == 4
        assert result['duplicate_group_count'] == 1
        assert result['duplicate_file_count'] == 1
        group = result['groups'][0]
        assert pathlib.Path(group['keeper']).name == 'a.txt'
        assert [pathlib.Path(item).name for item in group['duplicates']] == ['b.txt']
        text = toolbox.format_same_summary(result)
        assert '鍙戠幇 1 缁勯噸澶嶆枃浠? in text
        assert '寰呯Щ鍔?1 涓噸澶嶆枃浠? in text


def test_same_module_recursive_scan_skips_duplicate_target_dir():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'b.txt').write_bytes(b'duplicate')
        skipped = root / '閲嶅鏂囦欢'
        skipped.mkdir()
        (skipped / 'c.txt').write_bytes(b'duplicate')

        first_level = module.find_duplicate_groups(root, recursive=False)
        recursive = module.find_duplicate_groups(root, recursive=True)

        assert first_level['scanned_files'] == 1
        assert first_level['duplicate_group_count'] == 0
        assert recursive['scanned_files'] == 2
        assert recursive['duplicate_group_count'] == 1
        assert recursive['duplicate_file_count'] == 1


def test_same_module_normalizes_target_dir_name_with_path_separators():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        (root / 'b.txt').write_bytes(b'duplicate')
        skipped = root / '閲嶅鏂囦欢'
        skipped.mkdir()
        (skipped / 'c.txt').write_bytes(b'duplicate')

        result = module.find_duplicate_groups(root, recursive=True, target_dir_name='ignore/me/閲嶅鏂囦欢/')

        assert result['target_dir_name'] == '閲嶅鏂囦欢'
        assert result['scanned_files'] == 2
        assert result['duplicate_group_count'] == 1


def test_same_module_moves_duplicates_to_root_duplicate_dir_and_auto_renames():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        nested = root / 'nested'
        nested.mkdir()
        source_duplicate = nested / 'a.txt'
        source_duplicate.write_bytes(b'duplicate')
        target_dir = root / '閲嶅鏂囦欢' / 'nested'
        target_dir.mkdir(parents=True)
        (target_dir / 'a.txt').write_text('existing', encoding='utf-8')

        result = module.find_duplicate_groups(root, recursive=True)
        moved = module.move_duplicates(root, result)

        assert len(moved) == 1
        assert moved[0]['success'] is True
        assert moved[0]['renamed'] is True
        assert (root / 'a.txt').exists()
        assert not source_duplicate.exists()
        assert (target_dir / 'a(1).txt').exists()

        refreshed = module.find_duplicate_groups(root, recursive=True)
        assert refreshed['duplicate_group_count'] == 0
        assert refreshed['duplicate_file_count'] == 0


def test_same_module_moves_outside_directory_targets_when_existing_path_is_directory():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        nested = root / 'nested'
        nested.mkdir()
        source_duplicate = nested / 'a.txt'
        source_duplicate.write_bytes(b'duplicate')
        target_dir = root / '閲嶅鏂囦欢' / 'nested' / 'a.txt'
        target_dir.mkdir(parents=True)

        result = module.find_duplicate_groups(root, recursive=True)
        moved = module.move_duplicates(root, result)

        assert len(moved) == 1
        assert moved[0]['success'] is True
        assert moved[0]['target_path'].name == 'a(1).txt'
        assert (root / '閲嶅鏂囦欢' / 'nested' / 'a.txt').is_dir()
        assert (root / '閲嶅鏂囦欢' / 'nested' / 'a(1).txt').exists()
        assert not source_duplicate.exists()


def test_same_module_rejects_mismatched_target_dir_name_between_scan_and_move():
    toolbox = load_module()
    module = toolbox.get_same_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        (root / 'b.txt').write_bytes(b'duplicate')

        result = module.find_duplicate_groups(root, recursive=False, target_dir_name='閲嶅鏂囦欢')

        try:
            module.move_duplicates(root, result, target_dir_name='鍏朵粬鏂囦欢澶?)
        except ValueError as exc:
            assert 'target_dir_name' in str(exc)
        else:
            raise AssertionError('expected target_dir_name mismatch error')


def test_light_theme_nav_panel_matches_background():
    toolbox = load_module()
    assert "QFrame[navPanel='true']" in toolbox.LIGHT_STYLESHEET
    assert "background-color: #eef1f5;" in toolbox.LIGHT_STYLESHEET
    assert "QFrame[panel='true']" in toolbox.LIGHT_STYLESHEET


def test_dark_theme_nav_panel_matches_background():
    toolbox = load_module()
    assert "QFrame[navPanel='true']" in toolbox.DARK_STYLESHEET
    assert "background-color: #1f2329;" in toolbox.DARK_STYLESHEET


def test_nav_list_theme_rules_exist_for_both_modes():
    toolbox = load_module()
    assert "QListWidget[navList='true']" in toolbox.LIGHT_STYLESHEET
    assert "QListWidget[navList='true']::viewport" in toolbox.LIGHT_STYLESHEET
    assert "QListWidget[navList='true']" in toolbox.DARK_STYLESHEET
    assert "QListWidget[navList='true']::viewport" in toolbox.DARK_STYLESHEET


def test_global_scrollbar_style_covers_both_axes_and_is_applied_to_scroll_hosts():
    toolbox = load_module()
    style = toolbox.build_global_scrollbar_style()
    assert 'QScrollBar:vertical' in style
    assert 'QScrollBar:horizontal' in style
    assert 'QScrollBar::handle:vertical:hover' in style

    source = MODULE_PATH.read_text(encoding='utf-8')
    assert "self.song_list_scroll.setStyleSheet(build_music_scroll_area_style())" in source
    assert source.count("self.log.setStyleSheet(build_global_scrollbar_style())") >= 6
    assert "self.base64_edit.setStyleSheet(build_global_scrollbar_style())" in source
    assert "self.sidebar.setStyleSheet(build_global_scrollbar_style())" in source
    assert "min-height: 18px;" in source
    assert "max-height: 18px;" in source

