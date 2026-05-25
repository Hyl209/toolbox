import importlib.util
import pathlib
import tempfile
import sys


ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / 'converter.py'
TAB_MODULE_PATH = ROOT / 'tab.py'


def load_module():
    sys.modules.pop('video_downloader_test_module', None)
    spec = importlib.util.spec_from_file_location('video_downloader_test_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_tab_module():
    sys.modules.pop('video_downloader_tab_test_module', None)
    spec = importlib.util.spec_from_file_location('video_downloader_tab_test_module', TAB_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_task_lines_deduplicates_and_preserves_order():
    module = load_module()
    text = '\nhttps://example.com/a\nhttps://example.com/a\n https://t.me/demo/1 \n\n'
    assert module.parse_task_lines(text) == ['https://example.com/a', 'https://t.me/demo/1']


def test_classify_source_distinguishes_telegram_message_chat_and_web():
    module = load_module()
    assert module.classify_source('https://t.me/demo/123') == 'telegram_message'
    assert module.classify_source('https://t.me/demo') == 'telegram_chat'
    assert module.classify_source('https://t.me/c/123456/7') == 'telegram_message'
    assert module.classify_source('https://example.com/video') == 'web'


def test_validate_download_request_requires_output_and_telegram_credentials():
    module = load_module()
    config = module.TelegramConfig(api_id='', api_hash='', phone='', session_file='telegram.session')
    errors = module.validate_download_request('https://t.me/demo/1', '', config, recent_limit='500')
    assert '请选择输出目录' in errors
    assert '请输入 Telegram API ID' in errors
    assert '请输入 Telegram API Hash' in errors
    assert '请输入 Telegram 手机号' in errors


def test_sanitize_filename_component_and_ensure_unique_path_work_for_windows_names():
    module = load_module()
    assert module.sanitize_filename_component('bad<>:"/\\\\|?*name') == 'bad_name'
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        first = root / 'video.mp4'
        first.write_text('x', encoding='utf-8')
        second = module.ensure_unique_path(first)
        assert second.name == 'video (1).mp4'


def test_ensure_unique_stem_avoids_existing_conflicts():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'demo.mp4').write_text('x', encoding='utf-8')
        assert module.ensure_unique_stem(root, 'demo') == 'demo (1)'


def test_download_batch_continues_when_web_task_fails():
    module = load_module()
    original_download = module._download_web_task
    original_require = module._require_web_backend
    try:
        module._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb):
            if 'bad' in task.source_url:
                raise module.DownloadError('boom')
            path = output_root / 'ok.mp4'
            path.write_text('ok', encoding='utf-8')
            return module._make_result(task, True, [path], '')

        module._download_web_task = fake_download
        tasks = [
            module.DownloadTask('https://example.com/good', 'web', 'good'),
            module.DownloadTask('https://example.com/bad', 'web', 'bad'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                module.download_batch(tasks, tmp, None, module.DownloadOptions())
            except module.DownloadError:
                raise AssertionError('download_batch should summarize per-task failures')
    except AssertionError:
        raise
    except Exception:
        raise
    finally:
        module._download_web_task = original_download
        module._require_web_backend = original_require


def test_normalize_date_range_rejects_invalid_and_reversed_dates():
    module = load_module()
    try:
        module.normalize_date_range('2026/01/01', '')
    except ValueError as exc:
        assert '开始日期必须是 YYYY-MM-DD 格式' == str(exc)
    else:
        raise AssertionError('expected invalid start date error')
    try:
        module.normalize_date_range('2026-02-01', '2026-01-01')
    except ValueError as exc:
        assert '开始日期不能晚于结束日期' == str(exc)
    else:
        raise AssertionError('expected reversed range error')


def test_validate_download_request_requires_one_telegram_media_type():
    module = load_module()
    config = module.TelegramConfig(api_id='1', api_hash='hash', phone='+123', session_file='telegram.session')
    errors = module.validate_download_request(
        'https://t.me/demo',
        '.',
        config,
        recent_limit='500',
        telegram_include_videos=False,
        telegram_include_photos=False,
    )
    assert 'Telegram 任务至少要勾选一种下载类型' in errors


def test_validate_download_request_allows_all_messages_with_zero_recent_limit():
    module = load_module()
    config = module.TelegramConfig(api_id='1', api_hash='hash', phone='+123', session_file='telegram.session')
    errors = module.validate_download_request(
        'https://t.me/demo',
        '.',
        config,
        recent_limit='0',
        telegram_download_all_messages=True,
    )
    assert errors == []


def test_download_batch_returns_failure_result_for_failed_web_task():
    module = load_module()
    original_download = module._download_web_task
    original_require = module._require_web_backend
    try:
        module._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb):
            if 'bad' in task.source_url:
                raise module.DownloadError('boom')
            path = output_root / 'ok.mp4'
            path.write_text('ok', encoding='utf-8')
            return module._make_result(task, True, [path], '')

        module._download_web_task = fake_download
        tasks = [
            module.DownloadTask('https://example.com/good', 'web', 'good'),
            module.DownloadTask('https://example.com/bad', 'web', 'bad'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            results = module.download_batch(tasks, tmp, None, module.DownloadOptions())
        assert results[0]['success'] is True
        assert results[1]['success'] is False
        assert results[1]['error'] == 'boom'
    finally:
        module._download_web_task = original_download
        module._require_web_backend = original_require


def test_extract_media_candidates_finds_absolute_and_relative_urls():
    module = load_module()
    html = '''
    <video src="/media/demo.mp4"></video>
    <script>var player={"file":"https://cdn.example.com/live/test.m3u8"};</script>
    '''
    result = module._extract_media_candidates(html, 'https://example.com/post/1')
    assert 'https://example.com/media/demo.mp4' in result
    assert 'https://cdn.example.com/live/test.m3u8' in result


def test_download_web_task_falls_back_to_page_media_candidates_when_ytdlp_rejects_page_url():
    module = load_module()
    original_runner = module._download_url_with_ytdlp
    original_fetch = module._fetch_webpage_html
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint=''):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                raise module.DownloadError('ERROR: Unsupported URL: https://example.com/post/1')
            path = output_root / 'demo.mp4'
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        module._download_url_with_ytdlp = fake_runner
        module._fetch_webpage_html = lambda url: '<video src="/media/demo.mp4"></video>'
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = module._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert seen == ['https://example.com/post/1', 'https://example.com/media/demo.mp4']
    finally:
        module._download_url_with_ytdlp = original_runner
        module._fetch_webpage_html = original_fetch


def test_download_web_task_can_download_all_page_media_candidates():
    module = load_module()
    original_runner = module._download_url_with_ytdlp
    original_fetch = module._fetch_webpage_html
    original_extract = module._extract_ytdlp_entry_candidates
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint=''):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                raise module.DownloadError('ERROR: Unsupported URL: https://example.com/post/1')
            file_name = pathlib.Path(source_url).name.split('?', 1)[0] or 'demo.mp4'
            path = output_root / file_name
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        module._download_url_with_ytdlp = fake_runner
        module._fetch_webpage_html = lambda url: '''
        <video src="/media/a.mp4"></video>
        <video src="/media/b.mp4"></video>
        '''
        module._extract_ytdlp_entry_candidates = lambda url: []
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            options = module.DownloadOptions(web_download_all_candidates=True)
            result = module._download_web_task(task, pathlib.Path(tmp), options, None)
        assert result['success'] is True
        assert result['downloaded_count'] == 2
        assert seen == [
            'https://example.com/post/1',
            'https://example.com/media/a.mp4',
            'https://example.com/media/b.mp4',
        ]
    finally:
        module._download_url_with_ytdlp = original_runner
        module._fetch_webpage_html = original_fetch
        module._extract_ytdlp_entry_candidates = original_extract


def test_download_web_task_uses_ytdlp_multi_entry_candidates_instead_of_collapsing_to_one():
    module = load_module()
    original_runner = module._download_url_with_ytdlp
    original_extract = module._extract_ytdlp_entry_candidates
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint=''):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                path = output_root / 'first-only.mp4'
            else:
                file_name = pathlib.Path(source_url).name.split('?', 1)[0] or 'demo.mp4'
                path = output_root / file_name
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        module._download_url_with_ytdlp = fake_runner
        module._extract_ytdlp_entry_candidates = lambda url: [
            'https://cdn.example.com/media/a.mp4',
            'https://cdn.example.com/media/b.mp4',
        ]
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            options = module.DownloadOptions(web_download_all_candidates=True)
            result = module._download_web_task(task, pathlib.Path(tmp), options, None)
        assert result['success'] is True
        assert result['downloaded_count'] == 2
        assert seen == [
            'https://cdn.example.com/media/a.mp4',
            'https://cdn.example.com/media/b.mp4',
        ]
    finally:
        module._download_url_with_ytdlp = original_runner
        module._extract_ytdlp_entry_candidates = original_extract


def test_emit_scan_progress_uses_structured_marker():
    module = load_module()
    captured: list[str] = []
    module._emit_scan_progress(captured.append, 25, 3)
    assert captured == ['__HYL_PROGRESS__|tg_scan|matched=3|scanned=25']


def test_normalize_positive_index_accepts_blank_and_rejects_non_positive_values():
    module = load_module()
    assert module.normalize_positive_index('', '网页候选序号') is None
    assert module.normalize_positive_index('2', '网页候选序号') == 2
    try:
        module.normalize_positive_index('0', '网页候选序号')
    except ValueError as exc:
        assert '网页候选序号必须大于 0' == str(exc)
    else:
        raise AssertionError('expected invalid index error')


def test_validate_video_downloader_form_accepts_preloaded_module():
    tab_module = load_tab_module()
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = tab_module.validate_video_downloader_form(
            'https://example.com/video',
            tmp,
            '',
            '',
            '',
            '500',
            module=module,
            get_video_downloader_module=lambda: (_ for _ in ()).throw(AssertionError('should not reload module')),
        )
    assert errors == []


def test_validate_video_downloader_form_rejects_web_link_on_telegram_page():
    tab_module = load_tab_module()
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = tab_module.validate_video_downloader_form(
            'https://example.com/video',
            tmp,
            '1',
            'hash',
            '+123',
            '500',
            module=module,
            source_mode='telegram',
        )
    assert '当前页仅支持 Telegram 链接，请移到“网页视频下载”页签处理网页链接' in errors


def test_validate_video_downloader_form_rejects_telegram_link_on_web_page():
    tab_module = load_tab_module()
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        errors = tab_module.validate_video_downloader_form(
            'https://t.me/demo/1',
            tmp,
            '',
            '',
            '',
            '500',
            module=module,
            source_mode='web',
        )
    assert '当前页仅支持网页视频链接，请移到“TG下载”页签处理 Telegram 链接' in errors


def test_build_source_mode_summary_for_web_hides_telegram_counts():
    tab_module = load_tab_module()
    summary = tab_module.build_source_mode_summary(['https://example.com/a', 'https://example.com/b'], 'web')
    assert '网页视频任务' in summary
    assert 'Telegram 消息' not in summary
    assert 'Telegram 群/频道' not in summary


def test_build_source_mode_summary_for_web_does_not_show_current_page_label():
    tab_module = load_tab_module()
    summary = tab_module.build_source_mode_summary(['https://example.com/a'], 'web')
    assert '当前页：仅网页视频' not in summary

def test_inspect_web_media_candidates_prefers_detected_candidates():
    module = load_module()
    original_extract = module._extract_ytdlp_entry_candidates
    original_fetch = module._fetch_webpage_html
    original_support = module._supports_ytdlp_direct_media
    try:
        module._extract_ytdlp_entry_candidates = lambda url: [
            'https://cdn.example.com/a.mp4',
            'https://cdn.example.com/b.mp4',
        ]
        module._fetch_webpage_html = lambda url: ''
        module._supports_ytdlp_direct_media = lambda url: False
        result = module.inspect_web_media_candidates('https://example.com/post/1')
    finally:
        module._extract_ytdlp_entry_candidates = original_extract
        module._fetch_webpage_html = original_fetch
        module._supports_ytdlp_direct_media = original_support
    assert result['success'] is True
    assert result['candidate_count'] == 2
    assert result['source'] == 'yt-dlp'


def test_build_source_mode_summary_for_web_hides_telegram_counts():
    tab_module = load_tab_module()
    summary = tab_module.build_source_mode_summary(['https://example.com/a', 'https://example.com/b'], 'web')
    assert '网页链接' in summary
    assert 'Telegram 消息' not in summary
    assert 'Telegram 群/频道' not in summary


def test_format_web_task_summary_can_show_scan_results():
    tab_module = load_tab_module()
    summary = tab_module.format_web_task_summary(
        ['https://example.com/a'],
        {'https://example.com/a': {'success': True, 'candidate_count': 2}},
    )
    assert '2 个候选' in summary
