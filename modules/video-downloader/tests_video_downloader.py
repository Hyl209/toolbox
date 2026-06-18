import importlib.util
import os
import pathlib
import tempfile
import sys
import threading
import time
import types


ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / 'converter.py'
TAB_MODULE_PATH = ROOT / 'tab.py'

_PKG_NAME = 'video_downloader_pkg'


def _ensure_package():
    """Register video-downloader as a fake package so relative imports work."""
    if _PKG_NAME in sys.modules:
        return
    pkg = types.ModuleType(_PKG_NAME)
    pkg.__path__ = [str(ROOT)]
    pkg.__package__ = _PKG_NAME
    sys.modules[_PKG_NAME] = pkg
    # Load sub-modules in dependency order
    sub_modules = ['_shared', 'models', 'source_parser', 'progress', 'telegram_backend', 'web_backend', 'tab_constants', 'tab_formatters', 'tab_task_list', 'tab_workers', 'tab_panels']
    for name in sub_modules:
        fpath = ROOT / f'{name}.py'
        if fpath.exists():
            fqn = f'{_PKG_NAME}.{name}'
            spec = importlib.util.spec_from_file_location(fqn, fpath, submodule_search_locations=[])
            mod = importlib.util.module_from_spec(spec)
            mod.__package__ = _PKG_NAME
            sys.modules[fqn] = mod
            setattr(pkg, name, mod)
            spec.loader.exec_module(mod)


def load_module():
    _ensure_package()
    fqn = f'{_PKG_NAME}.converter'
    sys.modules.pop(fqn, None)
    spec = importlib.util.spec_from_file_location(fqn, MODULE_PATH, submodule_search_locations=[])
    module = importlib.util.module_from_spec(spec)
    module.__package__ = _PKG_NAME
    sys.modules[fqn] = module
    spec.loader.exec_module(module)
    return module


def load_tab_module():
    _ensure_package()
    fqn = f'{_PKG_NAME}.tab'
    sys.modules.pop(fqn, None)
    spec = importlib.util.spec_from_file_location(fqn, TAB_MODULE_PATH, submodule_search_locations=[])
    module = importlib.util.module_from_spec(spec)
    module.__package__ = _PKG_NAME
    sys.modules[fqn] = module
    spec.loader.exec_module(module)
    return module


def load_web_backend():
    """Load the web_backend sub-module for mocking."""
    _ensure_package()
    fqn = f'{_PKG_NAME}.web_backend'
    if fqn in sys.modules:
        return sys.modules[fqn]
    wb_path = ROOT / 'web_backend.py'
    spec = importlib.util.spec_from_file_location(fqn, wb_path, submodule_search_locations=[])
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG_NAME
    sys.modules[fqn] = mod
    spec.loader.exec_module(mod)
    return mod


def load_shared():
    _ensure_package()
    fqn = f'{_PKG_NAME}._shared'
    if fqn in sys.modules:
        return sys.modules[fqn]
    path = ROOT / '_shared.py'
    spec = importlib.util.spec_from_file_location(fqn, path, submodule_search_locations=[])
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG_NAME
    sys.modules[fqn] = mod
    spec.loader.exec_module(mod)
    return mod


def load_progress():
    _ensure_package()
    fqn = f'{_PKG_NAME}.progress'
    if fqn in sys.modules:
        return sys.modules[fqn]
    path = ROOT / 'progress.py'
    spec = importlib.util.spec_from_file_location(fqn, path, submodule_search_locations=[])
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG_NAME
    sys.modules[fqn] = mod
    spec.loader.exec_module(mod)
    return mod



def test_parse_task_lines_deduplicates_and_preserves_order():
    module = load_module()
    text = '\nhttps://example.com/a\nhttps://example.com/a\n https://t.me/demo/1 \n\n'
    assert module.parse_task_lines(text) == ['https://example.com/a', 'https://t.me/demo/1']


def test_parse_task_lines_extracts_douyin_share_url_from_share_text():
    module = load_module()
    text = '7.53 复制打开抖音，看看【示例】 https://v.douyin.com/ABC123/ 09/01 F@x '
    assert module.parse_task_lines(text) == ['https://v.douyin.com/ABC123/']


def test_build_download_tasks_treats_douyin_share_url_as_web():
    module = load_module()
    tasks = module.build_download_tasks([
        '7.53 复制打开抖音，看看【示例】 https://v.douyin.com/ABC123/ 09/01 F@x ',
    ])
    assert len(tasks) == 1
    assert tasks[0].source_url == 'https://v.douyin.com/ABC123/'
    assert tasks[0].source_kind == 'web'


def test_normalize_proxy_url_adds_default_http_scheme():
    module = load_module()

    assert module.normalize_proxy_url('127.0.0.1:7890') == 'http://127.0.0.1:7890'
    assert module.normalize_proxy_url('socks5://127.0.0.1:7891') == 'socks5://127.0.0.1:7891'
    assert module.normalize_proxy_url('   ') == ''
    assert module.build_proxy_url('127.0.0.1', '7890') == 'http://127.0.0.1:7890'
    assert module.build_proxy_url('http://127.0.0.1:7890', '') == 'http://127.0.0.1:7890'
    assert module.build_proxy_url('socks5://user:pass@127.0.0.1', '7891') == 'socks5://user:pass@127.0.0.1:7891'
    assert module.build_proxy_url('', '') == ''
    assert module.split_proxy_url('http://127.0.0.1:7890') == ('127.0.0.1', '7890')
    assert module.split_proxy_url('socks5://user:pass@127.0.0.1:7891') == ('socks5://user:pass@127.0.0.1', '7891')


def test_inspect_web_media_batch_passes_same_proxy_to_scan_sources():
    module = load_module()
    wb = load_web_backend()
    calls: list[tuple[str, str]] = []
    original_douyin = wb._extract_douyin_share_candidates
    original_ytdlp = wb._extract_ytdlp_entry_candidates
    original_fetch = wb._fetch_webpage_html
    original_supports = wb._supports_ytdlp_direct_media
    try:
        def fake_douyin(url, options=None):
            calls.append(('douyin', options.proxy_url))
            return []

        def fake_ytdlp(url, options=None):
            calls.append(('yt-dlp', options.proxy_url))
            return []

        def fake_fetch(url, proxy_url=''):
            calls.append(('html', proxy_url))
            return ''

        def fake_supports(url, options=None):
            calls.append(('page', options.proxy_url))
            return False

        wb._extract_douyin_share_candidates = fake_douyin
        wb._extract_ytdlp_entry_candidates = fake_ytdlp
        wb._fetch_webpage_html = fake_fetch
        wb._supports_ytdlp_direct_media = fake_supports

        wb.inspect_web_media_batch(
            ['https://example.com/page'],
            options=module.DownloadOptions(proxy_url='127.0.0.1:7890'),
        )

        assert calls == [
            ('douyin', '127.0.0.1:7890'),
            ('yt-dlp', '127.0.0.1:7890'),
            ('html', 'http://127.0.0.1:7890'),
            ('page', '127.0.0.1:7890'),
        ]
    finally:
        wb._extract_douyin_share_candidates = original_douyin
        wb._extract_ytdlp_entry_candidates = original_ytdlp
        wb._fetch_webpage_html = original_fetch
        wb._supports_ytdlp_direct_media = original_supports


def test_apply_output_subdirs_by_title_keeps_each_custom_name():
    tab_module = load_tab_module()
    module = load_module()
    tasks = [
        module.DownloadTask('https://example.com/a', 'web', '片头'),
        module.DownloadTask('https://example.com/b', 'web', '正片'),
    ]

    updated = tab_module.apply_output_subdirs_by_title(tasks, True)

    assert [task.output_subdir for task in updated] == ['片头', '正片']
    assert tab_module.apply_output_subdirs_by_title(tasks, False) is tasks


def test_apply_output_subdirs_by_title_strips_web_queue_suffix_for_subdir():
    tab_module = load_tab_module()
    module = load_module()
    tasks = [
        module.DownloadTask('https://cdn.example.com/a.mp4', 'web', 'course_001'),
        module.DownloadTask('https://cdn.example.com/b.mp4', 'web', 'course_002'),
    ]

    updated = tab_module.apply_output_subdirs_by_title(
        tasks,
        True,
        tab_module.web_queue_output_subdir_title,
    )

    assert [task.output_subdir for task in updated] == ['course', 'course']


def test_output_subdir_by_title_only_applies_to_web_mode():
    tab_module = load_tab_module()

    checked = types.SimpleNamespace(isChecked=lambda: True)
    assert tab_module.output_subdir_by_title_enabled(
        types.SimpleNamespace(source_mode='web', output_subdir_checkbox=checked)
    ) is True
    assert tab_module.output_subdir_by_title_enabled(
        types.SimpleNamespace(source_mode='telegram', output_subdir_checkbox=checked)
    ) is False


def test_parse_task_lines_deduplicates_plain_url_and_douyin_share_text():
    module = load_module()
    text = '\nhttps://v.douyin.com/ABC123/\n7.53 复制打开抖音，看看【示例】 https://v.douyin.com/ABC123/ 09/01 F@x \n'
    assert module.parse_task_lines(text) == ['https://v.douyin.com/ABC123/']


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
    wb = load_web_backend()
    original_download = wb._download_web_task
    original_require = wb._require_web_backend
    wb._INTER_TASK_DELAY_RANGE = (0, 0)
    try:
        wb._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb, **kwargs):
            if 'bad' in task.source_url:
                raise module.DownloadError('boom')
            path = output_root / 'ok.mp4'
            path.write_text('ok', encoding='utf-8')
            return module._make_result(task, True, [path], '')

        wb._download_web_task = fake_download
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
        wb._download_web_task = original_download
        wb._require_web_backend = original_require


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
    wb = load_web_backend()
    original_download = wb._download_web_task
    original_require = wb._require_web_backend
    wb._INTER_TASK_DELAY_RANGE = (0, 0)
    try:
        wb._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb, **kwargs):
            if 'bad' in task.source_url:
                raise module.DownloadError('boom')
            path = output_root / 'ok.mp4'
            path.write_text('ok', encoding='utf-8')
            pr = load_progress()
            return pr._make_result(task, True, [path], '')

        wb._download_web_task = fake_download
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
        wb._download_web_task = original_download
        wb._require_web_backend = original_require


def test_download_batch_reraises_cancelled_error():
    module = load_module()
    wb = load_web_backend()
    original_download = wb._download_web_task
    original_require = wb._require_web_backend
    wb._INTER_TASK_DELAY_RANGE = (0, 0)
    try:
        wb._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb, **kwargs):
            raise module.CancelledError('cancelled')

        wb._download_web_task = fake_download
        tasks = [module.DownloadTask('https://example.com/a', 'web', 'a')]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                module.download_batch(tasks, tmp, None, module.DownloadOptions())
            except module.CancelledError:
                pass
            else:
                raise AssertionError('download_batch should reraise CancelledError')
    finally:
        wb._download_web_task = original_download
        wb._require_web_backend = original_require


def test_extract_media_candidates_finds_absolute_and_relative_urls():
    module = load_module()
    wb = load_web_backend()
    html = '''
    <video src="/media/demo.mp4"></video>
    <script>var player={"file":"https://cdn.example.com/live/test.m3u8"};</script>
    '''
    result = wb._extract_media_candidates(html, 'https://example.com/post/1')
    assert 'https://example.com/media/demo.mp4' in result
    assert 'https://cdn.example.com/live/test.m3u8' in result


def test_download_web_task_falls_back_to_page_media_candidates_when_ytdlp_rejects_page_url():
    module = load_module()
    wb = load_web_backend()
    original_runner = wb._download_url_with_ytdlp
    original_fetch = wb._fetch_webpage_html
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                raise module.DownloadError('ERROR: Unsupported URL: https://example.com/post/1')
            path = output_root / 'demo.mp4'
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_url_with_ytdlp = fake_runner
        wb._fetch_webpage_html = lambda url, *args, **kwargs: '<video src="/media/demo.mp4"></video>'
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = wb._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert seen == ['https://example.com/post/1', 'https://example.com/media/demo.mp4']
    finally:
        wb._download_url_with_ytdlp = original_runner
        wb._fetch_webpage_html = original_fetch


def test_download_web_task_uses_task_output_subdir():
    module = load_module()
    wb = load_web_backend()
    original_runner = wb._download_url_with_ytdlp
    original_extract = wb._extract_ytdlp_entry_candidates
    try:
        captured: list[pathlib.Path] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            captured.append(output_root)
            path = output_root / 'demo.mp4'
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_url_with_ytdlp = fake_runner
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: []
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo', output_subdir='课程 一')
            result = wb._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
            assert pathlib.Path(tmp, '课程 一').is_dir()
        assert result['success'] is True
        assert captured and captured[0].name == '课程 一'
        assert pathlib.Path(result['files'][0]).parent.name == '课程 一'
    finally:
        wb._download_url_with_ytdlp = original_runner
        wb._extract_ytdlp_entry_candidates = original_extract


def test_expand_web_all_candidates_preserves_task_output_subdir():
    module = load_module()
    wb = load_web_backend()
    original_extract = wb._extract_ytdlp_entry_candidates
    try:
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: [
            'https://cdn.example.com/a.mp4',
            'https://cdn.example.com/b.mp4',
        ]

        expanded = wb._expand_web_all_candidates(
            [module.DownloadTask('https://example.com/course', 'web', '课程', output_subdir='课程')],
            None,
            module.DownloadOptions(web_download_all_candidates=True),
        )

        assert [task.output_subdir for task in expanded] == ['课程', '课程']
        assert [task.source_url for task in expanded] == [
            'https://cdn.example.com/a.mp4',
            'https://cdn.example.com/b.mp4',
        ]
    finally:
        wb._extract_ytdlp_entry_candidates = original_extract


def test_fetch_webpage_html_uses_proxy_opener():
    wb = load_web_backend()
    captured: dict[str, object] = {}

    class FakeResponse:
        headers = types.SimpleNamespace(get_content_charset=lambda: 'utf-8')

        def read(self):
            return b'<video></video>'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeOpener:
        def open(self, request, timeout=20):
            captured['url'] = request.full_url
            captured['timeout'] = timeout
            return FakeResponse()

    original_build_opener = wb.build_opener
    original_proxy_handler = wb.ProxyHandler
    try:
        wb.ProxyHandler = lambda proxies: captured.setdefault('proxies', proxies)
        wb.build_opener = lambda handler: FakeOpener()

        assert wb._fetch_webpage_html('https://example.com/page', '127.0.0.1:7890') == '<video></video>'
        assert captured['proxies'] == {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
        assert captured['url'] == 'https://example.com/page'
        assert captured['timeout'] == 20
    finally:
        wb.build_opener = original_build_opener
        wb.ProxyHandler = original_proxy_handler


def test_download_web_task_can_download_all_page_media_candidates():
    module = load_module()
    wb = load_web_backend()
    original_runner = wb._download_url_with_ytdlp
    original_fetch = wb._fetch_webpage_html
    original_extract = wb._extract_ytdlp_entry_candidates
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                raise module.DownloadError('ERROR: Unsupported URL: https://example.com/post/1')
            file_name = pathlib.Path(source_url).name.split('?', 1)[0] or 'demo.mp4'
            path = output_root / file_name
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_url_with_ytdlp = fake_runner
        wb._fetch_webpage_html = lambda url, *args, **kwargs: '''
        <video src="/media/a.mp4"></video>
        <video src="/media/b.mp4"></video>
        '''
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: []
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            options = module.DownloadOptions(web_download_all_candidates=True)
            result = wb._download_web_task(task, pathlib.Path(tmp), options, None)
        assert result['success'] is True
        assert result['downloaded_count'] == 2
        assert seen == [
            'https://example.com/post/1',
            'https://example.com/media/a.mp4',
            'https://example.com/media/b.mp4',
        ]
    finally:
        wb._download_url_with_ytdlp = original_runner
        wb._fetch_webpage_html = original_fetch
        wb._extract_ytdlp_entry_candidates = original_extract


def test_download_web_task_uses_ytdlp_multi_entry_candidates_instead_of_collapsing_to_one():
    module = load_module()
    wb = load_web_backend()
    original_runner = wb._download_url_with_ytdlp
    original_extract = wb._extract_ytdlp_entry_candidates
    try:
        seen: list[str] = []

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            seen.append(source_url)
            if source_url == 'https://example.com/post/1':
                path = output_root / 'first-only.mp4'
            else:
                file_name = pathlib.Path(source_url).name.split('?', 1)[0] or 'demo.mp4'
                path = output_root / file_name
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_url_with_ytdlp = fake_runner
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: [
            'https://cdn.example.com/media/a.mp4',
            'https://cdn.example.com/media/b.mp4',
        ]
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            options = module.DownloadOptions(web_download_all_candidates=True)
            result = wb._download_web_task(task, pathlib.Path(tmp), options, None)
        assert result['success'] is True
        assert result['downloaded_count'] == 2
        assert seen == [
            'https://cdn.example.com/media/a.mp4',
            'https://cdn.example.com/media/b.mp4',
        ]
    finally:
        wb._download_url_with_ytdlp = original_runner
        wb._extract_ytdlp_entry_candidates = original_extract


def test_emit_scan_progress_uses_structured_marker():
    module = load_module()
    pr = load_progress()
    captured: list[str] = []
    pr._emit_scan_progress(captured.append, 25, 3)
    assert captured == ['__HYL_PROGRESS__|tg_scan|matched=3|scanned=25']


def test_make_web_progress_hook_emits_speed_and_eta():
    module = load_module()
    wb = load_web_backend()
    captured: list[str] = []
    hook = wb._make_web_progress_hook(captured.append)
    hook({
        'status': 'downloading',
        'filename': 'demo.mp4',
        '_percent_str': '12.3%',
        '_speed_str': '1.2 MiB/s',
        '_eta_str': '00:05',
    })
    assert any(item.startswith('__HYL_PROGRESS__|web_percent|percent=12.3') for item in captured)
    assert any(item.startswith('__HYL_PROGRESS__|web_status|') and 'speed=1.2 MiB/s' in item and 'eta=00:05' in item for item in captured)
    assert any('正在下载 "demo.mp4" "1.2 MiB/s" "12.3%"' in item for item in captured)


def test_make_web_progress_hook_can_compute_percent_from_bytes():
    module = load_module()
    wb = load_web_backend()
    captured: list[str] = []
    hook = wb._make_web_progress_hook(captured.append)
    hook({
        'status': 'downloading',
        'filename': 'demo.mp4',
        'downloaded_bytes': 25,
        'total_bytes': 100,
        'speed': 2048,
    })
    assert any(item.startswith('__HYL_PROGRESS__|web_percent|percent=25.0') for item in captured)
    assert '正在下载 "demo.mp4" "2.0 KiB/s" "25%"' in captured


def test_make_web_progress_hook_uses_internal_pause_signal_not_cancel():
    module = load_module()
    wb = load_web_backend()
    token = module.Token()
    token.pause.set()
    hook = wb._make_web_progress_hook(None, token)
    try:
        hook({'status': 'downloading', 'filename': 'demo.mp4'})
    except module.CancelledError as exc:
        raise AssertionError('pause must not surface as cancellation') from exc
    except wb._PausedDownload:
        pass
    else:
        raise AssertionError('paused hook should stop the current yt-dlp attempt')


def test_download_web_concurrent_reraises_cancelled_error():
    module = load_module()
    wb = load_web_backend()
    original_run = wb._run_web_task
    try:
        def fake_run(task, output_root, options, progress_cb, token):
            raise module.CancelledError('cancelled')

        wb._run_web_task = fake_run
        tasks = [(0, module.DownloadTask('https://example.com/a', 'web', 'a'))]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                wb._download_web_concurrent(tasks, pathlib.Path(tmp), module.DownloadOptions(), None, 1, 0, 1)
            except module.CancelledError:
                pass
            else:
                raise AssertionError('_download_web_concurrent should reraise CancelledError')
    finally:
        wb._run_web_task = original_run


def test_download_web_concurrent_passes_current_token_to_workers():
    module = load_module()
    wb = load_web_backend()
    pr = load_progress()
    original_run = wb._run_web_task
    token = module.Token()
    seen = []
    try:
        def fake_run(task, output_root, options, progress_cb, passed_token):
            seen.append(passed_token)
            return pr._make_result(task, True, [], '')

        wb._run_web_task = fake_run
        tasks = [(0, module.DownloadTask('https://example.com/a', 'web', 'a'))]
        with tempfile.TemporaryDirectory() as tmp:
            wb._download_web_concurrent(tasks, pathlib.Path(tmp), module.DownloadOptions(), None, 1, 0, 1, token=token)
        assert seen == [token]
    finally:
        wb._run_web_task = original_run


def test_make_telegram_progress_callback_emits_speed_and_eta():
    pr = load_progress()
    captured: list[str] = []
    original_monotonic = pr.monotonic
    times = iter([0.0, 1.0, 2.0])
    try:
        pr.monotonic = lambda: next(times)
        callback = pr._make_telegram_progress_callback(captured.append, 'demo.mp4')
        callback(50, 100)
        callback(100, 100)
    finally:
        pr.monotonic = original_monotonic
    assert any(item.startswith('__HYL_PROGRESS__|tg_media|') and 'speed=' in item for item in captured)
    assert any(item.startswith('__HYL_PROGRESS__|tg_media|') and 'eta=' in item for item in captured)
    assert any(item.startswith('正在下载 "demo.mp4" "') and '"50%"' in item for item in captured)


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


def test_run_download_assigns_web_tasks_to_named_subfolders():
    tab_module = load_tab_module()
    module = load_module()
    captured = {}
    tab_class = tab_module.build_video_downloader_tab_class({
        'QWidget': object,
        'QVBoxLayout': object,
        'QHBoxLayout': object,
        'QScrollArea': object,
        'QFrame': object,
        'QLabel': object,
        'QLineEdit': object,
        'QPlainTextEdit': object,
        'QPushButton': object,
        'QProgressBar': object,
        'QFileDialog': object,
        'QApplication': object,
        'QCheckBox': object,
        'QComboBox': object,
        'QObject': None,
        'QThread': None,
        'Signal': None,
        'load_setting': lambda *args, **kwargs: '',
        'save_setting': lambda *args, **kwargs: None,
        'make_card': lambda *args, **kwargs: object(),
        'make_transparent_row': lambda *args, **kwargs: object(),
        'build_global_scrollbar_style': lambda: '',
        'show_themed_warning': lambda *args, **kwargs: None,
        'show_themed_error': lambda *args, **kwargs: None,
        'show_themed_success': lambda *args, **kwargs: None,
        'style_combo_popup': lambda *args, **kwargs: None,
        'get_video_downloader_module': lambda: module,
        'ROOT': ROOT,
        'VIDEO_DOWNLOADER_DIR': ROOT,
    })

    class DummyField:
        def __init__(self, value=''):
            self._value = value

        def toPlainText(self):
            return self._value

        def text(self):
            return self._value

        def clear(self):
            self._value = ''

        def isChecked(self):
            return bool(self._value)

    class DummyTab:
        def __init__(self):
            self.module = module
            self.source_mode = 'web'
            self.task_edit = DummyField('\n'.join([
                '1.片头：https://cdn.example.com/a.mp4',
                '2.正片：https://cdn.example.com/b.mp4',
            ]))
            self.output_edit = DummyField('C:/tmp')
            self.api_id_edit = DummyField('')
            self.api_hash_edit = DummyField('')
            self.phone_edit = DummyField('')
            self.recent_count_edit = DummyField('500')
            self.all_messages_checkbox = DummyField('')
            self.date_from_edit = DummyField('')
            self.date_to_edit = DummyField('')
            self.include_video_checkbox = DummyField('')
            self.include_photo_checkbox = DummyField('')
            self.overwrite_checkbox = DummyField('')
            self.output_subdir_checkbox = DummyField('1')
            self.proxy_host_edit = DummyField('127.0.0.1')
            self.proxy_port_edit = DummyField('7890')
            self.concurrent_combo = None
            self.log = types.SimpleNamespace(clear=lambda: None)
            self.worker = None
            self.worker_thread = None
            self._downloaded_urls = set()
            self._current_options = None
            self.web_candidate_sources = {}

        def save_form_settings(self):
            pass

        def cleanup_worker(self):
            pass

        def _is_checked(self, widget):
            return bool(widget is not None and widget.isChecked())

        def _widget_text(self, widget):
            return widget.text() if widget is not None else ''

        def _concurrent_value(self):
            return '1'

        def build_config(self):
            return None

        def set_busy(self, value):
            pass

        def append_log(self, message):
            pass

        def reset_progress_ui(self, total_tasks):
            pass

        def _start_worker(self, tasks, options=None):
            captured['tasks'] = tasks
            captured['options'] = options

    tab_class.run_download(DummyTab())

    assert [task.output_subdir for task in captured['tasks']] == ['片头', '正片']
    assert captured['options'].output_subdir_by_title is True
    assert captured['options'].proxy_url == 'http://127.0.0.1:7890'
    assert captured['options'].web_use_browser_cookies is True


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
    wb = load_web_backend()
    original_extract = wb._extract_ytdlp_entry_candidates
    original_fetch = wb._fetch_webpage_html
    original_support = wb._supports_ytdlp_direct_media
    try:
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: [
            'https://cdn.example.com/a.mp4',
            'https://cdn.example.com/b.mp4',
        ]
        wb._fetch_webpage_html = lambda url, *args, **kwargs: ''
        wb._supports_ytdlp_direct_media = lambda url, *args, **kwargs: False
        result = wb.inspect_web_media_candidates('https://example.com/post/1')
    finally:
        wb._extract_ytdlp_entry_candidates = original_extract
        wb._fetch_webpage_html = original_fetch
        wb._supports_ytdlp_direct_media = original_support
    assert result['success'] is True
    assert result['candidate_count'] == 2
    assert result['source'] == 'yt-dlp'


def test_collect_web_media_candidates_falls_back_to_html_when_ytdlp_errors():
    wb = load_web_backend()
    original_douyin = wb._extract_douyin_share_candidates
    original_extract = wb._extract_ytdlp_entry_candidates
    original_fetch = wb._fetch_webpage_html
    try:
        wb._extract_douyin_share_candidates = lambda url, *args, **kwargs: []
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: (_ for _ in ()).throw(RuntimeError('yt-dlp failed'))
        wb._fetch_webpage_html = lambda url, *args, **kwargs: '<video src="https://cdn.example.com/a.mp4"></video>'
        candidates, source = wb._collect_web_media_candidates('https://example.com/page')
    finally:
        wb._extract_douyin_share_candidates = original_douyin
        wb._extract_ytdlp_entry_candidates = original_extract
        wb._fetch_webpage_html = original_fetch
    assert candidates == ['https://cdn.example.com/a.mp4']
    assert source == 'html'


def test_resolve_aria2c_path_prefers_bundled_binary():
    sh = load_shared()
    original_file = sh.__file__
    original_which = sh.shutil.which
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        bundled = root / 'bin' / 'aria2c.exe'
        bundled.parent.mkdir()
        bundled.write_bytes(b'fake')
        sh.__file__ = str(root / '_shared.py')
        sh.shutil.which = lambda name: 'C:/PATH/aria2c.exe'
        try:
            assert sh._resolve_aria2c_path() == str(bundled)
        finally:
            sh.__file__ = original_file
            sh.shutil.which = original_which


def test_download_url_with_ytdlp_uses_aria2_and_stability_options():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    # Defensive: reset _resolve_aria2c_path to the real implementation in case
    # a prior test left a monkeypatched lambda on the cached _shared module.
    _sh_path = ROOT / '_shared.py'
    _sh_spec = importlib.util.spec_from_file_location('_shared_fresh', _sh_path, submodule_search_locations=[])
    _sh_fresh = importlib.util.module_from_spec(_sh_spec)
    _sh_spec.loader.exec_module(_sh_fresh)
    sh._resolve_aria2c_path = _sh_fresh._resolve_aria2c_path
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Demo', 'id': 'abc'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://example.com/video',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
                referer_url='https://example.com/post/1',
            )
        download_opts = next(o for o in captured_opts if 'external_downloader' in o)
        assert result['success'] is True
        assert download_opts['external_downloader'] == 'C:/tools/aria2c.exe'
        assert download_opts['continuedl'] is True
        assert download_opts['fragment_retries'] == 20
        assert download_opts['retries'] == 20
        assert download_opts['throttledratelimit'] == 500 * 1024
        assert download_opts['http_headers']['Referer'] == 'https://example.com/post/1'
        assert '--summary-interval=1' in download_opts['external_downloader_args']
        assert '--header=Referer: https://example.com/post/1' in download_opts['external_downloader_args']
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_applies_proxy_to_ytdlp_and_aria2():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Demo', 'id': 'abc'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://example.com/video',
                pathlib.Path(tmp),
                module.DownloadOptions(proxy_url='127.0.0.1:7890'),
                None,
            )
        assert result['success'] is True
        assert captured_opts[0]['proxy'] == 'http://127.0.0.1:7890'
        download_opts = next(opts for opts in captured_opts if 'external_downloader_args' in opts)
        assert download_opts['proxy'] == 'http://127.0.0.1:7890'
        assert '--all-proxy=http://127.0.0.1:7890' in download_opts['external_downloader_args']
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_auto_fills_missing_cover_after_aria2_download():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    progress: list[str] = []
    fill_calls: list[tuple[str, str]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Demo', 'id': 'abc'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    def fake_embed_thumbnail(video_path, source_url, progress_cb=None, candidate_index=None, **kwargs):
        fill_calls.append((pathlib.Path(video_path).name, source_url))
        if progress_cb:
            progress_cb('mock fill')
        return {'success': True, 'files': [str(video_path)]}

    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    original_has_cover = wb._video_has_embedded_thumbnail
    original_embed = wb.embed_thumbnail
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        fake_ytdlp.YoutubeDL = FakeYoutubeDL
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        wb._video_has_embedded_thumbnail = lambda video_path, ffmpeg_path: False
        wb.embed_thumbnail = fake_embed_thumbnail
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://example.com/video',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                progress.append,
            )
        assert result['success'] is True
        assert fill_calls == [('Demo [abc].mp4', 'https://example.com/video')]
        assert any('封面缺失，自动补封面: Demo [abc].mp4' == line for line in progress)
        assert any('封面补全成功: Demo [abc].mp4' == line for line in progress)
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg
        wb._video_has_embedded_thumbnail = original_has_cover
        wb.embed_thumbnail = original_embed


def test_download_url_with_ytdlp_uses_custom_title_as_exact_stem():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Site Title', 'id': 'abc'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        fake_ytdlp.YoutubeDL = FakeYoutubeDL
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://example.com/video',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
                title_hint='自定义名字',
            )
        assert pathlib.Path(result['files'][0]).name == '自定义名字.mp4'
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_embed_thumbnail_prefers_page_thumbnail_for_selected_candidate():
    wb = load_web_backend()
    fake_ytdlp = types.ModuleType('yt_dlp')
    progress: list[str] = []
    ytdlp_calls: list[tuple[str, bool]] = []
    ffmpeg_calls: list[list[str]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            ytdlp_calls.append((url, download))
            return {
                'entries': [
                    {'url': 'https://cdn.example.com/a/index.m3u8', 'thumbnail': 'https://cdn.example.com/a.jpg'},
                    {'url': 'https://cdn.example.com/b/index.m3u8', 'thumbnail': 'https://cdn.example.com/b.jpg'},
                ],
            }

    class FakeResponse:
        def __init__(self, body: bytes):
            self._body = body
            self.headers = {'Content-Type': 'image/jpeg'}

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=20):
        assert request.full_url == 'https://cdn.example.com/b.jpg'
        return FakeResponse(b'jpg-data')

    def fake_run(args, capture_output=True, check=True, **kwargs):
        ffmpeg_calls.append(list(args))
        pathlib.Path(args[-1]).write_text('ok', encoding='utf-8')
        return types.SimpleNamespace(stderr=b'')

    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_collect = wb._collect_web_media_candidates
    original_urlopen = wb.urlopen
    original_run = wb.subprocess.run
    original_which = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        fake_ytdlp.YoutubeDL = FakeYoutubeDL
        wb._require_web_backend = lambda: None
        wb._collect_web_media_candidates = lambda url, *args, **kwargs: (
            ['https://cdn.example.com/a/index.m3u8', 'https://cdn.example.com/b/index.m3u8'],
            'yt-dlp',
        )
        wb.urlopen = fake_urlopen
        wb.subprocess.run = fake_run
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        with tempfile.TemporaryDirectory() as tmp:
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            result = wb.embed_thumbnail(
                video_path,
                'https://example.com/post',
                progress_cb=progress.append,
                candidate_index=2,
            )
            assert result['success'] is True
            assert video_path.exists()
            assert video_path.read_text(encoding='utf-8') == 'ok'
        assert ytdlp_calls == [('https://example.com/post', False)]
        assert '正在抓取封面: https://example.com/post' in progress
        assert not any('页面封面缺失' in line for line in progress)
        assert len(ffmpeg_calls) == 1
        assert any(str(arg).endswith('demo.jpg') for arg in ffmpeg_calls[0])
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        wb._collect_web_media_candidates = original_collect
        wb.urlopen = original_urlopen
        wb.subprocess.run = original_run
        wb.shutil.which = original_which


def test_embed_thumbnail_falls_back_to_video_frame_when_external_cover_missing():
    wb = load_web_backend()
    fake_ytdlp = types.ModuleType('yt_dlp')
    progress: list[str] = []
    ffmpeg_calls: list[list[str]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {}

    def fake_run(args, capture_output=True, check=True, **kwargs):
        ffmpeg_calls.append(list(args))
        out_path = pathlib.Path(args[-1])
        out_path.write_text('ok', encoding='utf-8')
        return types.SimpleNamespace(stderr=b'')

    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_collect = wb._collect_web_media_candidates
    original_extract = wb._extract_thumbnail_urls
    original_run = wb.subprocess.run
    original_which = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        fake_ytdlp.YoutubeDL = FakeYoutubeDL
        wb._require_web_backend = lambda: None
        wb._collect_web_media_candidates = lambda url, *args, **kwargs: (['https://cdn.example.com/a/index.m3u8'], 'yt-dlp')
        wb._extract_thumbnail_urls = lambda source_url, resolved_url, candidate_index, *args, **kwargs: []
        wb.subprocess.run = fake_run
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        with tempfile.TemporaryDirectory() as tmp:
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            result = wb.embed_thumbnail(
                video_path,
                'https://example.com/post',
                progress_cb=progress.append,
                candidate_index=1,
            )
            assert result['success'] is True
            assert video_path.exists()
            assert video_path.read_text(encoding='utf-8') == 'ok'
        assert any('外部封面缺失，改用视频首帧' in line for line in progress)
        assert len(ffmpeg_calls) == 2
        assert 'thumbnail' in ffmpeg_calls[0]
        assert any(str(arg).endswith('demo.jpg') for arg in ffmpeg_calls[0])
        assert any(str(arg).endswith('demo_cover_tmp.mp4') for arg in ffmpeg_calls[1])
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        wb._collect_web_media_candidates = original_collect
        wb._extract_thumbnail_urls = original_extract
        wb.subprocess.run = original_run
        wb.shutil.which = original_which


def test_embed_thumbnail_falls_back_to_frame_when_source_url_empty():
    """web_then_frame mode with empty source_url should extract video frame."""
    wb = load_web_backend()
    progress: list[str] = []
    ffmpeg_calls: list[list[str]] = []

    def fake_run(args, capture_output=True, check=True, **kwargs):
        ffmpeg_calls.append(list(args))
        out_path = pathlib.Path(args[-1])
        out_path.write_text('ok', encoding='utf-8')
        return types.SimpleNamespace(stderr=b'')

    original_run = wb.subprocess.run
    original_which = wb.shutil.which
    try:
        wb.subprocess.run = fake_run
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        with tempfile.TemporaryDirectory() as tmp:
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            result = wb.embed_thumbnail(
                video_path,
                '',
                progress_cb=progress.append,
            )
            assert result['success'] is True
            assert video_path.read_text(encoding='utf-8') == 'ok'
        assert any('直接抽取视频帧作为封面: demo.mp4' == line for line in progress)
        assert len(ffmpeg_calls) == 2
        assert 'thumbnail' in ffmpeg_calls[0]
    finally:
        wb.subprocess.run = original_run
        wb.shutil.which = original_which


def test_embed_thumbnail_frame_mode_skips_web_lookup():
    wb = load_web_backend()
    progress: list[str] = []
    ffmpeg_calls: list[list[str]] = []

    def fake_run(args, capture_output=True, check=True, **kwargs):
        ffmpeg_calls.append(list(args))
        pathlib.Path(args[-1]).write_text('ok', encoding='utf-8')
        return types.SimpleNamespace(stderr=b'')

    def fail_require():
        raise AssertionError('yt-dlp should not be required for frame mode')

    original_require = wb._require_web_backend
    original_run = wb.subprocess.run
    original_which = wb.shutil.which
    try:
        wb._require_web_backend = fail_require
        wb.subprocess.run = fake_run
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        with tempfile.TemporaryDirectory() as tmp:
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            result = wb.embed_thumbnail(
                video_path,
                '',
                progress_cb=progress.append,
                thumbnail_mode='frame',
            )
            assert result['success'] is True
            assert video_path.read_text(encoding='utf-8') == 'ok'
        assert any('直接抽取视频帧作为封面: demo.mp4' == line for line in progress)
        assert len(ffmpeg_calls) == 2
        assert 'thumbnail' in ffmpeg_calls[0]
        assert any(str(arg).endswith('demo_cover_tmp.mp4') for arg in ffmpeg_calls[1])
    finally:
        wb._require_web_backend = original_require
        wb.subprocess.run = original_run
        wb.shutil.which = original_which


def test_embed_thumbnail_frame_mode_returns_error_on_ffmpeg_failure():
    wb = load_web_backend()
    import subprocess as _sp

    def fake_run(args, capture_output=True, check=True, **kwargs):
        raise _sp.CalledProcessError(1, args, stderr=b'invalid codec')

    original_require = wb._require_web_backend
    original_run = wb.subprocess.run
    original_which = wb.shutil.which
    try:
        wb._require_web_backend = lambda: (_ for _ in ()).throw(AssertionError('should not be called'))
        wb.subprocess.run = fake_run
        wb.shutil.which = lambda name: 'C:/tools/ffmpeg.exe' if name == 'ffmpeg' else ''
        with tempfile.TemporaryDirectory() as tmp:
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            result = wb.embed_thumbnail(
                video_path,
                '',
                thumbnail_mode='frame',
            )
            assert result['success'] is False
            assert '视频帧提取失败' in result['error']
            assert 'invalid codec' in result['error']
    finally:
        wb._require_web_backend = original_require
        wb.subprocess.run = original_run
        wb.shutil.which = original_which


def test_cover_button_defaults_to_frame_mode_without_source_url():
    tab_module = load_tab_module()
    calls: list[dict[str, object]] = []

    class FakeFileDialog:
        @staticmethod
        def getOpenFileNames(*args, **kwargs):
            return (['C:/tmp/demo.mp4'], '')

    class FakeModule:
        def parse_task_lines(self, text):
            return []

        def build_proxy_url(self, host, port):
            return f'http://{host}:{port}' if port else ''

        def embed_thumbnail(self, fpath, source_url, progress_cb=None, candidate_index=None, thumbnail_mode='web_then_frame', proxy_url=''):
            calls.append({
                'fpath': fpath,
                'source_url': source_url,
                'thumbnail_mode': thumbnail_mode,
                'proxy_url': proxy_url,
            })
            return {'success': True}

    tab_class = tab_module.build_video_downloader_tab_class({
        'QWidget': object,
        'QVBoxLayout': object,
        'QHBoxLayout': object,
        'QScrollArea': object,
        'QFrame': object,
        'QLabel': object,
        'QLineEdit': object,
        'QPlainTextEdit': object,
        'QPushButton': object,
        'QProgressBar': object,
        'QFileDialog': FakeFileDialog,
        'QApplication': object,
        'QCheckBox': object,
        'QComboBox': object,
        'QObject': None,
        'QThread': None,
        'Signal': None,
        'load_setting': lambda *args, **kwargs: '',
        'save_setting': lambda *args, **kwargs: None,
        'make_card': lambda *args, **kwargs: object(),
        'make_transparent_row': lambda *args, **kwargs: object(),
        'build_global_scrollbar_style': lambda: '',
        'show_themed_warning': lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('no warning expected')),
        'show_themed_error': lambda *args, **kwargs: None,
        'show_themed_success': lambda *args, **kwargs: None,
        'style_combo_popup': lambda *args, **kwargs: None,
        'get_video_downloader_module': FakeModule,
        'ROOT': ROOT,
        'VIDEO_DOWNLOADER_DIR': ROOT,
    })

    class DummyText:
        def toPlainText(self):
            return ''

        def text(self):
            return ''

    class DummyTab:
        module = FakeModule()
        settings = object()
        task_edit = DummyText()
        output_edit = DummyText()
        proxy_host_edit = types.SimpleNamespace(text=lambda: '127.0.0.1')
        proxy_port_edit = types.SimpleNamespace(text=lambda: '7890')
        _last_cover_dir = ''
        log = types.SimpleNamespace(clear=lambda: None)
        thumbnail_worker = None
        thumbnail_worker_thread = None

        def _choose_thumbnail_mode(self, has_source_url):
            assert has_source_url is False
            return 'frame'

        def _widget_text(self, widget):
            return widget.text()

        def _mode_setting_key(self, name):
            return name

        def set_busy(self, value):
            pass

        def append_log(self, message):
            pass

        def reset_progress_ui(self, total):
            pass

        def handle_thumbnail_progress(self, message):
            pass

        def finalize_thumbnail(self, results):
            pass

        def handle_thumbnail_error(self, message):
            raise AssertionError(message)

        def cleanup_thumbnail_worker(self):
            pass

        def build_web_options(self):
            return types.SimpleNamespace(proxy_url='http://127.0.0.1:7890')

    tab_class.embed_thumbnail_clicked(DummyTab())
    assert calls == [{
        'fpath': 'C:/tmp/demo.mp4',
        'source_url': '',
        'thumbnail_mode': 'frame',
        'proxy_url': 'http://127.0.0.1:7890',
    }]


def test_download_url_with_ytdlp_keeps_completed_file_when_aria2_finish_trips_error():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Demo', 'id': 'abc'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            raise RuntimeError('yt-dlp post-download cleanup failed')

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp('https://example.com/video', pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert len(result['files']) == 1
        assert pathlib.Path(result['files'][0]).name == 'Demo [abc].mp4'
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_waits_for_pause_then_resumes():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    token = module.Token()
    download_calls = []
    clear_threads: list[threading.Thread] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Demo', 'id': 'abc'}
            download_calls.append(url)
            if len(download_calls) == 1:
                token.pause.set()
                clearer = threading.Thread(target=lambda: (time.sleep(0.05), token.pause.clear()))
                clear_threads.append(clearer)
                clearer.start()
                self.opts['progress_hooks'][0]({'status': 'downloading', 'filename': 'demo.mp4'})
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        wb._ffmpeg_path.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp('https://example.com/video', pathlib.Path(tmp), module.DownloadOptions(), None, token=token)
        assert result['success'] is True
        assert len(download_calls) == 2
    finally:
        for thread in clear_threads:
            thread.join(timeout=1)
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg
        wb._ffmpeg_path.cache_clear()


def test_concurrent_ytdlp_downloads_are_not_serialized_by_aria2_progress_capture():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    token = module.Token()
    barrier = threading.Barrier(2)
    entered: list[str] = []
    entry_lock = threading.Lock()

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': pathlib.PurePosixPath(url).name or 'Demo', 'id': 'abc'}
            with entry_lock:
                entered.append(url)
            try:
                barrier.wait(timeout=1)
            except threading.BrokenBarrierError as exc:
                raise AssertionError('concurrent downloads did not overlap') from exc
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: 'aria2c'
        wb.shutil.which = lambda name: ''
        wb._ffmpeg_path.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            tasks = [
                (0, module.DownloadTask('https://example.com/a', 'web', 'a')),
                (1, module.DownloadTask('https://example.com/b', 'web', 'b')),
            ]
            results = wb._download_web_entries(
                tasks,
                pathlib.Path(tmp),
                module.DownloadOptions(max_concurrent_downloads=2),
                lambda message: None,
                2,
                0,
                token=token,
            )
        assert len(entered) == 2
        assert all(item['success'] for item in results.values())
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg
        wb._ffmpeg_path.cache_clear()


def test_download_url_with_ytdlp_sets_legacy_server_connect_for_tls_edge_cases():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if download:
                pathlib.Path(str(captured_opts[-1]['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
                return {'ok': True}
            return {'title': 'Demo', 'id': 'abc'}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            wb._download_url_with_ytdlp('https://example.com/video', pathlib.Path(tmp), module.DownloadOptions(), None)
        # legacyserverconnect removed — no longer bypassing TLS
        assert 'legacyserverconnect' not in captured_opts[0]
        assert 'legacyserverconnect' not in captured_opts[1]
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_retries_douyin_with_browser_cookies():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if 'cookiesfrombrowser' not in self.opts:
                raise RuntimeError('ERROR: [Douyin] 7644497851275431174: Fresh cookies (not necessarily logged in) are needed')
            if not download:
                return {'title': 'Douyin Demo', 'id': 'dy123'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://v.douyin.com/mYxjnR57uFU/',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
            )
        assert result['success'] is True
        assert any('cookiesfrombrowser' not in opts for opts in captured_opts)
        assert any(opts.get('cookiesfrombrowser') == ('chrome',) for opts in captured_opts)
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg


def test_extract_ytdlp_entry_candidates_retries_douyin_with_browser_cookies():
    wb = load_web_backend()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(dict(opts))

        def extract_info(self, url, download=False):
            if 'cookiesfrombrowser' not in self.opts:
                raise RuntimeError('ERROR: [Douyin] 7644497851275431174: Fresh cookies (not necessarily logged in) are needed')
            return {
                'entries': [
                    {'url': 'https://cdn.example.com/video.mp4'},
                ],
            }

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        result = wb._extract_ytdlp_entry_candidates('https://v.douyin.com/mYxjnR57uFU/')
        assert result == ['https://cdn.example.com/video.mp4']
        assert any('cookiesfrombrowser' not in opts for opts in captured_opts)
        assert any(opts.get('cookiesfrombrowser') == ('chrome',) for opts in captured_opts)
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require


def test_extract_douyin_share_candidates_uses_mobile_share_page_play_url():
    wb = load_web_backend()
    original_fetch = wb._fetch_douyin_share_html
    try:
        wb._fetch_douyin_share_html = lambda url, *args, **kwargs: '''
        <script>
        window._ROUTER_DATA = {"loaderData":{"page":{"videoInfoRes":{"item_list":[{"video":{"play_addr":{"url_list":["https://aweme.snssdk.com/aweme/v1/playwm/?video_id=v0200fg10000d8bbapfog65tcjqvkp40&ratio=720p&line=0"]}}}]}}}};
        </script>
        '''
        result = wb._extract_douyin_share_candidates('https://v.douyin.com/jz83Ii3BD-4/')
    finally:
        wb._fetch_douyin_share_html = original_fetch
    assert result == ['https://aweme.snssdk.com/aweme/v1/play/?video_id=v0200fg10000d8bbapfog65tcjqvkp40&ratio=720p&line=0']


def test_download_url_with_ytdlp_falls_back_to_cookiefile_when_browser_cookie_copy_fails():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if self.opts.get('cookiefile'):
                if not download:
                    return {'title': 'Douyin Demo', 'id': 'dy456'}
                pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
                return {'ok': True}
            if 'cookiesfrombrowser' in self.opts:
                raise RuntimeError('ERROR: Could not copy Chrome cookie database. See https://github.com/yt-dlp/yt-dlp/issues/7271 for more info')
            raise RuntimeError('ERROR: [Douyin] 7644497851275431174: Fresh cookies (not necessarily logged in) are needed')

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    original_cookie_candidates = wb._iter_cookie_file_candidates
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        wb._iter_cookie_file_candidates = lambda: [pathlib.Path('C:/temp/douyin.cookies.txt')]
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://v.douyin.com/jz83Ii3BD-4/',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
            )
        assert result['success'] is True
        assert any(opts.get('cookiesfrombrowser') == ('chrome',) for opts in captured_opts)
        assert not any(opts.get('cookiesfrombrowser') == ('firefox',) for opts in captured_opts)
        assert any(str(opts.get('cookiefile', '')).lower().endswith('douyin.cookies.txt') for opts in captured_opts)
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg
        wb._iter_cookie_file_candidates = original_cookie_candidates


def test_download_web_task_prefers_douyin_share_candidates_before_ytdlp():
    module = load_module()
    wb = load_web_backend()
    original_extract_share = wb._extract_douyin_share_candidates
    original_extract_ytdlp = wb._extract_ytdlp_entry_candidates
    original_download_candidates = wb._download_web_candidates
    try:
        wb._extract_douyin_share_candidates = lambda url, *args, **kwargs: ['https://aweme.snssdk.com/aweme/v1/play/?video_id=abc&ratio=720p&line=0']
        wb._extract_ytdlp_entry_candidates = lambda url, *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not call yt-dlp'))

        def fake_download(candidates, task, output_root, options, progress_cb, ffmpeg_path='', *, download_all=False, **kwargs):
            assert candidates == ['https://aweme.snssdk.com/aweme/v1/play/?video_id=abc&ratio=720p&line=0']
            path = output_root / 'douyin.mp4'
            path.write_text('ok', encoding='utf-8')
            return [path], None

        wb._download_web_candidates = fake_download
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://v.douyin.com/jz83Ii3BD-4/', 'web', 'douyin')
            result = wb._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert result['downloaded_count'] == 1
    finally:
        wb._extract_douyin_share_candidates = original_extract_share
        wb._extract_ytdlp_entry_candidates = original_extract_ytdlp
        wb._download_web_candidates = original_download_candidates


def test_download_web_candidate_uses_direct_http_for_douyin_play_url():
    module = load_module()
    wb = load_web_backend()
    original_direct = wb._download_direct_media_file
    original_ytdlp = wb._download_url_with_ytdlp
    try:
        called: list[str] = []

        def fake_direct(media_url, task, output_root, options, progress_cb, *, referer_url='', **kwargs):
            called.append('direct')
            assert media_url == 'https://aweme.snssdk.com/aweme/v1/play/?video_id=abc&ratio=720p&line=0'
            assert referer_url == 'https://v.douyin.com/jz83Ii3BD-4/'
            return {'success': True, 'files': [output_root / 'douyin.mp4']}

        wb._download_direct_media_file = fake_direct
        wb._download_url_with_ytdlp = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not call yt-dlp'))
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://v.douyin.com/jz83Ii3BD-4/', 'web', 'douyin')
            result = wb._download_web_candidate(
                'https://aweme.snssdk.com/aweme/v1/play/?video_id=abc&ratio=720p&line=0',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
            )
        assert result['success'] is True
        assert called == ['direct']
    finally:
        wb._download_direct_media_file = original_direct
        wb._download_url_with_ytdlp = original_ytdlp


def test_download_web_task_surfaces_cookie_lock_guidance_without_html_fallback():
    module = load_module()
    wb = load_web_backend()
    original_runner = wb._download_url_with_ytdlp
    original_fetch = wb._fetch_webpage_html
    original_share = wb._extract_douyin_share_candidates
    try:
        wb._extract_douyin_share_candidates = lambda url, *args, **kwargs: []
        wb._download_url_with_ytdlp = lambda *args, **kwargs: (_ for _ in ()).throw(
            module.DownloadError(
                'ERROR: Could not copy Chrome cookie database. See https://github.com/yt-dlp/yt-dlp/issues/7271 for more info'
            )
        )
        wb._fetch_webpage_html = lambda url, *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not reach html fallback'))
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://v.douyin.com/jz83Ii3BD-4/', 'web', 'douyin')
            try:
                wb._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
            except module.DownloadError as exc:
                message = str(exc)
            else:
                raise AssertionError('expected cookie lock guidance error')
        assert 'Could not copy Chrome cookie database' in message
        assert 'LockProfileCookieDatabase' in message
        assert 'cookies.txt' in message
    finally:
        wb._extract_douyin_share_candidates = original_share
        wb._download_url_with_ytdlp = original_runner
        wb._fetch_webpage_html = original_fetch


def test_m3u8_candidate_tries_ytdlp_before_ffmpeg_fallback():
    module = load_module()
    wb = load_web_backend()
    calls: list[str] = []
    original_ytdlp = wb._download_url_with_ytdlp
    original_ffmpeg = wb._download_m3u8_with_ffmpeg
    try:
        def fake_ytdlp(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            calls.append('yt-dlp')
            assert referer_url == 'https://example.com/post/1'
            raise module.DownloadError('slow')

        def fake_ffmpeg(media_url, task, output_root, options, progress_cb, ffmpeg_path='', referer_url='', **kwargs):
            calls.append('ffmpeg')
            assert referer_url == 'https://example.com/post/1'
            return {'success': True, 'files': [output_root / 'ok.mp4']}

        wb._download_url_with_ytdlp = fake_ytdlp
        wb._download_m3u8_with_ffmpeg = fake_ffmpeg
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = wb._download_web_candidate('https://cdn.example.com/live.m3u8', task, pathlib.Path(tmp), module.DownloadOptions(), None, ffmpeg_path='ffmpeg')
        assert result['success'] is True
        assert calls == ['yt-dlp', 'ffmpeg']
    finally:
        wb._download_url_with_ytdlp = original_ytdlp
        wb._download_m3u8_with_ffmpeg = original_ffmpeg


def test_m3u8_candidate_keeps_explicit_browser_cookies_for_direct_media_url():
    module = load_module()
    wb = load_web_backend()
    captured: dict[str, object] = {}
    original_ytdlp = wb._download_url_with_ytdlp
    original_ffmpeg = wb._download_m3u8_with_ffmpeg
    try:
        def fake_ytdlp(source_url, output_root, options, progress_cb, title_hint='', referer_url='', **kwargs):
            captured['use_cookies'] = options.web_use_browser_cookies
            return {'success': True, 'files': [output_root / 'ok.mp4']}

        wb._download_url_with_ytdlp = fake_ytdlp
        wb._download_m3u8_with_ffmpeg = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not fallback'))
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = wb._download_web_candidate(
                'https://cdn.example.com/live.m3u8',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(web_use_browser_cookies=True),
                None,
                ffmpeg_path='ffmpeg',
            )
        assert result['success'] is True
        assert captured['use_cookies'] is True
    finally:
        wb._download_url_with_ytdlp = original_ytdlp
        wb._download_m3u8_with_ffmpeg = original_ffmpeg


def test_m3u8_source_task_downloads_directly_without_browser_cookies_probe():
    module = load_module()
    wb = load_web_backend()
    captured: dict[str, object] = {}
    original_candidate = wb._download_web_candidate
    original_extract = wb._extract_ytdlp_entry_candidates
    original_ffmpeg_path = wb._ffmpeg_path
    try:
        def fake_candidate(candidate_url, task, output_root, options, progress_cb, ffmpeg_path='', **kwargs):
            captured['candidate_url'] = candidate_url
            captured['use_cookies'] = options.web_use_browser_cookies
            captured['ffmpeg_path'] = ffmpeg_path
            return {'success': True, 'files': [output_root / 'ok.mp4']}

        wb._download_web_candidate = fake_candidate
        wb._extract_ytdlp_entry_candidates = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not probe yt-dlp'))
        wb._ffmpeg_path = lambda: 'ffmpeg'
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://cdn.example.com/live.m3u8', 'web', 'demo')
            result = wb._download_web_task(
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(web_use_browser_cookies=True),
                None,
            )
        assert result['success'] is True
        assert captured['candidate_url'] == 'https://cdn.example.com/live.m3u8'
        assert captured['use_cookies'] is True
        assert captured['ffmpeg_path'] == 'ffmpeg'
    finally:
        wb._download_web_candidate = original_candidate
        wb._extract_ytdlp_entry_candidates = original_extract
        wb._ffmpeg_path = original_ffmpeg_path


def test_bilibili_cdn_candidate_uses_direct_downloader_with_bilibili_referer():
    module = load_module()
    wb = load_web_backend()
    captured: dict[str, object] = {}
    original_direct = wb._download_direct_media_file
    original_ytdlp = wb._download_url_with_ytdlp
    try:
        def fake_direct(media_url, task, output_root, options, progress_cb, referer_url='', **kwargs):
            captured['media_url'] = media_url
            captured['referer_url'] = referer_url
            path = output_root / 'bili.mp4'
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_direct_media_file = fake_direct
        wb._download_url_with_ytdlp = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not use yt-dlp'))
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://www.bilibili.com/video/BV1xx', 'web', 'demo')
            result = wb._download_web_candidate(
                'https://upos-sz-estgcos.bilivideo.com/upgcxcode/demo.mp4?deadline=1',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
            )
        assert result['success'] is True
        assert captured['referer_url'] == 'https://www.bilibili.com/'
        assert captured['media_url'].startswith('https://upos-sz-estgcos.bilivideo.com/')
    finally:
        wb._download_direct_media_file = original_direct
        wb._download_url_with_ytdlp = original_ytdlp


def test_bilibili_cdn_task_uses_direct_downloader_before_ytdlp_probe():
    module = load_module()
    wb = load_web_backend()
    calls: list[str] = []
    original_direct = wb._download_direct_media_file
    original_ytdlp = wb._download_url_with_ytdlp
    original_extract = wb._extract_ytdlp_entry_candidates
    try:
        def fake_direct(media_url, task, output_root, options, progress_cb, referer_url='', **kwargs):
            calls.append(f'direct:{referer_url}')
            path = output_root / 'bili.mp4'
            path.write_text('ok', encoding='utf-8')
            return {'success': True, 'files': [path]}

        wb._download_direct_media_file = fake_direct
        wb._download_url_with_ytdlp = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not use yt-dlp'))
        wb._extract_ytdlp_entry_candidates = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not probe yt-dlp'))
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask(
                'https://upos-sz-estgcos.bilivideo.com/upgcxcode/demo.mp4?deadline=1',
                'web',
                'demo',
            )
            result = wb._download_web_task(task, pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert calls == ['direct:https://www.bilibili.com/']
    finally:
        wb._download_direct_media_file = original_direct
        wb._download_url_with_ytdlp = original_ytdlp
        wb._extract_ytdlp_entry_candidates = original_extract


def test_bilibili_page_scan_keeps_page_url_for_cookie_aware_ytdlp():
    wb = load_web_backend()
    original_support = wb._supports_ytdlp_direct_media
    original_fetch = wb._fetch_webpage_html
    try:
        wb._supports_ytdlp_direct_media = lambda url, options=None: True
        wb._fetch_webpage_html = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('should not scan html preview urls'))

        candidates, source = wb._collect_web_media_candidates('https://www.bilibili.com/video/BV1xx', None)
    finally:
        wb._supports_ytdlp_direct_media = original_support
        wb._fetch_webpage_html = original_fetch

    assert candidates == ['https://www.bilibili.com/video/BV1xx']
    assert source == 'bilibili-page'


def test_bilibili_page_scan_uses_html_fallback_before_page_url():
    wb = load_web_backend()
    original_extract = wb._extract_ytdlp_entry_candidates
    original_support = wb._supports_ytdlp_direct_media
    original_fetch = wb._fetch_webpage_html
    try:
        wb._extract_ytdlp_entry_candidates = lambda *args, **kwargs: []
        wb._supports_ytdlp_direct_media = lambda *args, **kwargs: False
        wb._fetch_webpage_html = lambda *args, **kwargs: '<video src="/media/demo.mp4"></video>'

        candidates, source = wb._collect_web_media_candidates('https://www.bilibili.com/video/BV1xx', None)
    finally:
        wb._extract_ytdlp_entry_candidates = original_extract
        wb._supports_ytdlp_direct_media = original_support
        wb._fetch_webpage_html = original_fetch

    assert candidates == ['https://www.bilibili.com/media/demo.mp4']
    assert source == 'html'


def test_bilibili_page_ytdlp_probe_uses_browser_cookies_by_default():
    module = load_module()
    wb = load_web_backend()
    sh = load_shared()
    fake_ytdlp = types.ModuleType('yt_dlp')
    captured_opts: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            captured_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            if not download:
                return {'title': 'Bili Demo', 'id': 'BV1xx'}
            pathlib.Path(str(self.opts['outtmpl']).replace('%(ext)s', 'mp4')).write_text('ok', encoding='utf-8')
            return {'ok': True}

    fake_ytdlp.YoutubeDL = FakeYoutubeDL
    original_module = sys.modules.get('yt_dlp')
    original_require = wb._require_web_backend
    original_resolve_aria2 = sh._resolve_aria2c_path
    original_ffmpeg = wb.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        wb._require_web_backend = lambda: None
        sh._resolve_aria2c_path = lambda: ''
        wb.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = wb._download_url_with_ytdlp(
                'https://www.bilibili.com/video/BV1xx',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
            )
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        wb._require_web_backend = original_require
        sh._resolve_aria2c_path = original_resolve_aria2
        wb.shutil.which = original_ffmpeg

    assert result['success'] is True
    assert captured_opts[0].get('cookiesfrombrowser') == ('chrome',)
    assert any(opts.get('cookiesfrombrowser') == ('chrome',) for opts in captured_opts)


def test_collect_web_media_candidates_uses_bilibili_ytdlp_entries_before_page_fallback():
    wb = load_web_backend()
    original_extract = wb._extract_ytdlp_entry_candidates
    original_support = wb._supports_ytdlp_direct_media
    captured: dict[str, object] = {}
    try:
        def fake_extract(url, options=None):
            captured['use_cookies'] = options.web_use_browser_cookies
            captured['disable_auto'] = getattr(options, '_disable_auto_browser_cookies', False)
            return ['https://cdn.example.com/a.mp4']

        wb._extract_ytdlp_entry_candidates = fake_extract
        wb._supports_ytdlp_direct_media = lambda *args, **kwargs: False
        candidates, source = wb._collect_web_media_candidates(
            'https://www.bilibili.com/video/BV1xx',
            wb.DownloadOptions(web_use_browser_cookies=True),
        )
    finally:
        wb._extract_ytdlp_entry_candidates = original_extract
        wb._supports_ytdlp_direct_media = original_support

    assert candidates == ['https://cdn.example.com/a.mp4']
    assert source == 'yt-dlp'
    assert captured['use_cookies'] is True
    assert captured['disable_auto'] is True


def test_emit_aria2_progress_reports_speed_without_overall_percent():
    module = load_module()
    wb = load_web_backend()
    captured: list[str] = []
    wb._emit_aria2_progress(
        captured.append,
        'demo.mp4',
        '[#abc 12MiB/100MiB(12%) CN:12 DL:4.5MiB ETA:19s]',
    )
    assert any(item.startswith('__HYL_PROGRESS__|web_aria2|') and 'speed=4.5MiB/s' in item and 'percent=12' in item and 'eta=00:19' in item for item in captured)
    assert not any(item.startswith('__HYL_PROGRESS__|web_status|') for item in captured)
    assert any('正在下载 "demo.mp4" "4.5MiB/s" "--"' in item for item in captured)


def test_capture_aria2_console_progress_serializes_process_stdout_redirect():
    wb = load_web_backend()
    entered_a = threading.Event()
    out_a: list[str] = []
    out_b: list[str] = []
    errors: list[BaseException] = []

    def worker_a():
        try:
            with wb._capture_aria2_console_progress(out_a.append, 'A.mp4'):
                entered_a.set()
                os.write(1, b'[#aaa 1MiB/10MiB(10%) CN:1 DL:1MiB ETA:9s]\n')
                time.sleep(0.2)
        except BaseException as exc:
            errors.append(exc)

    def worker_b():
        try:
            assert entered_a.wait(timeout=1)
            with wb._capture_aria2_console_progress(out_b.append, 'B.mp4'):
                os.write(1, b'[#bbb 2MiB/10MiB(20%) CN:1 DL:2MiB ETA:8s]\n')
        except BaseException as exc:
            errors.append(exc)

    first = threading.Thread(target=worker_a)
    second = threading.Thread(target=worker_b)
    first.start()
    second.start()
    first.join(timeout=2)
    second.join(timeout=2)

    assert errors == []
    assert any('name=A.mp4' in item and 'percent=10' in item for item in out_a)
    assert any('name=B.mp4' in item and 'percent=20' in item for item in out_b)
    assert not any('name=B.mp4' in item for item in out_a)
    assert not any('name=A.mp4' in item for item in out_b)


def test_ffmpeg_m3u8_command_enables_reconnect_options():
    module = load_module()
    wb = load_web_backend()
    captured: dict[str, object] = {}
    original_popen = wb.subprocess.Popen
    original_probe = wb._probe_stream_duration
    try:
        class FakeProcess:
            stdout = []
            returncode = 0

            def wait(self, timeout=None):
                return 0

        def fake_popen(command, **kwargs):
            captured['command'] = command
            return FakeProcess()

        wb.subprocess.Popen = fake_popen
        wb._probe_stream_duration = lambda url, ffmpeg_path='', **kwargs: None
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            wb._download_m3u8_with_ffmpeg(
                'https://cdn.example.com/live.m3u8',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
                ffmpeg_path='ffmpeg',
                referer_url='https://example.com/post/1',
            )
        command = captured['command']
        assert '-reconnect' in command
        assert '-reconnect_on_network_error' in command
        assert '-reconnect_on_http_error' in command
        assert '429,500,502,503,504' in command
        assert '-multiple_requests' in command
        assert '-headers' in command
        assert any('Referer: https://example.com/post/1\r\n' in item for item in command)
    finally:
        wb.subprocess.Popen = original_popen
        wb._probe_stream_duration = original_probe


def test_ffmpeg_m3u8_command_uses_proxy_for_probe_and_download():
    module = load_module()
    wb = load_web_backend()
    captured: dict[str, object] = {}
    original_popen = wb.subprocess.Popen
    original_run = wb.subprocess.run
    try:
        class FakeProcess:
            stdout = []
            returncode = 0

            def wait(self, timeout=None):
                return 0

        def fake_run(command, **kwargs):
            captured['probe_command'] = list(command)
            return types.SimpleNamespace(returncode=0, stdout='12.5\n')

        def fake_popen(command, **kwargs):
            captured['download_command'] = list(command)
            return FakeProcess()

        wb.subprocess.run = fake_run
        wb.subprocess.Popen = fake_popen
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            wb._download_m3u8_with_ffmpeg(
                'https://cdn.example.com/live.m3u8',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(proxy_url='127.0.0.1:7890'),
                None,
                ffmpeg_path='ffmpeg',
            )
        assert '-http_proxy' in captured['probe_command']
        assert 'http://127.0.0.1:7890' in captured['probe_command']
        assert '-http_proxy' in captured['download_command']
        assert 'http://127.0.0.1:7890' in captured['download_command']
    finally:
        wb.subprocess.Popen = original_popen
        wb.subprocess.run = original_run


def test_ffmpeg_m3u8_reconnect_overwrites_partial_output():
    module = load_module()
    wb = load_web_backend()
    commands: list[list[str]] = []
    original_popen = wb.subprocess.Popen
    original_probe = wb._probe_stream_duration
    token = module.Token()
    token.reconnect.set()
    try:
        class FakeProcess:
            def __init__(self, stdout):
                self.stdout = stdout
                self.stderr = None
                self.returncode = 0

            def terminate(self):
                self.returncode = -15

            def kill(self):
                self.returncode = -9

            def wait(self, timeout=None):
                return self.returncode

        def fake_popen(command, **kwargs):
            commands.append(list(command))
            stdout = ['out_time=00:00:01.000000\n'] if len(commands) == 1 else []
            return FakeProcess(stdout)

        wb.subprocess.Popen = fake_popen
        wb._probe_stream_duration = lambda url, ffmpeg_path='', **kwargs: None
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            wb._download_m3u8_with_ffmpeg(
                'https://cdn.example.com/live.m3u8',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(overwrite=False),
                None,
                ffmpeg_path='ffmpeg',
                token=token,
            )
        assert len(commands) == 2
        assert commands[0][1] == '-n'
        assert commands[1][1] == '-y'
    finally:
        wb.subprocess.Popen = original_popen
        wb._probe_stream_duration = original_probe


def test_ffmpeg_m3u8_allows_three_reconnects_before_success():
    module = load_module()
    wb = load_web_backend()
    commands: list[list[str]] = []
    original_popen = wb.subprocess.Popen
    original_probe = wb._probe_stream_duration
    token = module.Token()
    try:
        class FakeStdout:
            def __iter__(self):
                if len(commands) <= 3:
                    token.reconnect.set()
                    yield 'out_time=00:00:01.000000\n'

        class FakeProcess:
            def __init__(self):
                self.stdout = FakeStdout()
                self.stderr = None
                self.returncode = 0

            def terminate(self):
                self.returncode = -15

            def kill(self):
                self.returncode = -9

            def wait(self, timeout=None):
                return self.returncode

        def fake_popen(command, **kwargs):
            commands.append(list(command))
            return FakeProcess()

        wb.subprocess.Popen = fake_popen
        wb._probe_stream_duration = lambda url, ffmpeg_path='', **kwargs: None
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = wb._download_m3u8_with_ffmpeg(
                'https://cdn.example.com/live.m3u8',
                task,
                pathlib.Path(tmp),
                module.DownloadOptions(overwrite=False),
                None,
                ffmpeg_path='ffmpeg',
                token=token,
            )
        assert result['success'] is True
        assert len(commands) == 4
        assert [command[1] for command in commands] == ['-n', '-y', '-y', '-y']
    finally:
        wb.subprocess.Popen = original_popen
        wb._probe_stream_duration = original_probe


def test_hyltoolbox_spec_bundles_aria2c():
    spec_text = (ROOT.parent.parent / 'HylToolbox.spec').read_text(encoding='utf-8')
    assert "video-downloader/bin/aria2c.exe" in spec_text
    assert "video-downloader/bin/aria2c.SHA256.txt" in spec_text


def test_telegram_login_wires_password_callback_for_2fa():
    source = (ROOT / 'tab.py').read_text(encoding='utf-8')
    assert 'password_callback=self._request_telegram_password' in source
    assert 'QInputDialog.getText' in source
    assert 'QLineEdit.Password' in source


class _FakeSignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in list(self._slots):
            try:
                slot(*args)
            except TypeError:
                slot()


class _FakeQt:
    UserRole = 256
    WA_Hover = 1
    PointingHandCursor = 2
    AlignVCenter = 4
    Key_Return = 16777220


class _FakeSize:
    def __init__(self, width=0, height=0):
        self._width = width
        self._height = height

    def width(self):
        return self._width

    def height(self):
        return self._height

    def setWidth(self, width):
        self._width = width

    def setHeight(self, height):
        self._height = height


class _FakeMetrics:
    def horizontalAdvance(self, text):
        return len(str(text)) * 8


class _FakeWidget:
    def __init__(self, *args, **kwargs):
        self._style = ''
        self._width = 600
        self._height = 0
        self._text = str(args[0]) if args else ''
        self.textChanged = _FakeSignal()

    def setStyleSheet(self, style):
        self._style = style

    def styleSheet(self):
        return self._style

    def setProperty(self, *args):
        pass

    def setWordWrap(self, *args):
        pass

    def text(self):
        return self._text

    def setMinimumWidth(self, width):
        self._width = max(self._width, width)

    def setMaximumWidth(self, width):
        self._width = min(self._width, width)

    def setMinimumHeight(self, height):
        self._height = height

    def setMaximumHeight(self, height):
        self._height = height

    def setPlaceholderText(self, *args):
        pass

    def setContentsMargins(self, *args):
        pass

    def setFixedSize(self, width, height):
        self._width = width
        self._height = height

    def setFixedWidth(self, width):
        self._width = width

    def width(self):
        return self._width

    def fontMetrics(self):
        return _FakeMetrics()

    def setAttribute(self, *args):
        pass

    def setCursor(self, *args):
        pass

    def setAutoFillBackground(self, *args):
        pass

    def viewport(self):
        return self

    def sizeHint(self):
        return _FakeSize(self._width, self._height)

    def enterEvent(self, *args):
        pass

    def leaveEvent(self, *args):
        pass

    def resizeEvent(self, *args):
        pass


class _FakeLineEdit(_FakeWidget):
    def __init__(self, text=''):
        super().__init__()
        self._text = text
        self._read_only = False
        self.textChanged = _FakeSignal()
        self.editingFinished = _FakeSignal()

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text
        self.textChanged.emit(text)

    def setReadOnly(self, value):
        self._read_only = bool(value)

    def isReadOnly(self):
        return self._read_only

    def installEventFilter(self, *args):
        pass

    def setPlaceholderText(self, *args):
        pass

    def selectAll(self):
        pass

    def setFocus(self):
        pass


class _FakeButton(_FakeWidget):
    def __init__(self, text=''):
        super().__init__()
        self.text = text
        self._checked = False
        self.clicked = _FakeSignal()

    def setChecked(self, value):
        self._checked = bool(value)

    def isChecked(self):
        return self._checked

    def setToolTip(self, *args):
        pass

    def setAccessibleName(self, *args):
        pass

    def setVisible(self, *args):
        pass


class _FakeCombo(_FakeWidget):
    def __init__(self, *args):
        super().__init__()
        self.currentIndexChanged = _FakeSignal()
        self._index = 0

    def addItems(self, *args):
        pass

    def setCurrentIndex(self, index):
        self._index = index

    def currentIndex(self):
        return self._index


class _FakeLayout:
    def __init__(self, *args):
        self.children = []

    def setContentsMargins(self, *args):
        pass

    def setSpacing(self, *args):
        pass

    def addWidget(self, widget, *args):
        self.children.append(widget)

    def addLayout(self, layout, *args):
        self.children.append(layout)

    def addStretch(self, *args):
        pass


class _FakeListItem:
    def __init__(self):
        self._data = {}
        self._size = None

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)

    def setSizeHint(self, size):
        self._size = size


class _FakeListWidget(_FakeWidget):
    NoSelection = 0
    ScrollPerPixel = 1

    def __init__(self):
        super().__init__()
        self._items = []
        self._widgets = {}
        self._viewport = _FakeWidget()

    def viewport(self):
        return self._viewport

    def addItem(self, item):
        self._items.append(item)

    def setItemWidget(self, item, widget):
        self._widgets[item] = widget

    def itemWidget(self, item):
        return self._widgets.get(item)

    def item(self, index):
        return self._items[index]

    def count(self):
        return len(self._items)

    def row(self, item):
        try:
            return self._items.index(item)
        except ValueError:
            return -1

    def takeItem(self, index):
        item = self._items.pop(index)
        self._widgets.pop(item, None)
        return item

    def clear(self):
        self._items.clear()
        self._widgets.clear()

    def setSelectionMode(self, *args):
        pass

    def setHorizontalScrollMode(self, *args):
        pass

    def setVerticalScrollMode(self, *args):
        pass

    def setContentsMargins(self, *args):
        pass


def _make_web_task_list():
    tab = _make_web_task_tab()
    return tab.task_edit


def _make_web_task_tab():
    tab_panels = _ensure_package() or sys.modules[f'{_PKG_NAME}.tab_panels']
    deps = {
        'QLabel': _FakeWidget,
        'QPlainTextEdit': _FakeWidget,
        'QLineEdit': _FakeLineEdit,
        'QPushButton': _FakeButton,
        'QHBoxLayout': _FakeLayout,
        'QVBoxLayout': _FakeLayout,
        'QCheckBox': _FakeButton,
        'QComboBox': _FakeCombo,
        'QListWidget': _FakeListWidget,
        'QListWidgetItem': _FakeListItem,
        'QFrame': _FakeWidget,
        'Signal': _FakeSignal,
        'Qt': _FakeQt,
        'QSize': _FakeSize,
        'load_setting': lambda *args, **kwargs: '',
        'make_card': lambda *args: (_FakeWidget(), _FakeLayout()),
        'make_transparent_row': lambda: (_FakeWidget(), _FakeLayout()),
        'style_combo_popup': lambda *args, **kwargs: None,
    }
    tab = types.SimpleNamespace(
        settings={},
        source_mode='web',
        current_theme='dark',
        mode_meta={'task_placeholder': ''},
        task_edit=None,
        source_edit=None,
        summary_label=None,
        output_edit=None,
        overwrite_checkbox=None,
        concurrent_combo=None,
        scan_button=None,
        cover_button=None,
        run_button=None,
        pause_button=None,
        cancel_button=None,
        reconnect_button=None,
        module=types.SimpleNamespace(split_proxy_url=lambda value: ('127.0.0.1', '')),
        handle_web_source_text_changed=lambda: None,
        handle_task_text_changed=lambda: None,
        _mode_setting_key=lambda name: name,
        save_form_settings=lambda: None,
        choose_output_dir=lambda: None,
        scan_web_candidates=lambda: None,
        embed_thumbnail_clicked=lambda: None,
        run_download=lambda: None,
        toggle_pause=lambda: None,
        cancel_download=lambda: None,
        reconnect_download=lambda: None,
    )
    tab_panels.build_task_section(tab, _FakeLayout(), None, '', 110, deps)
    return tab


def test_build_source_mode_summary_for_web_hides_telegram_counts():
    tab_module = load_tab_module()
    summary = tab_module.build_source_mode_summary(['https://example.com/a', 'https://example.com/b'], 'web')
    assert '网页链接' in summary
    assert 'Telegram 消息' not in summary
    assert 'Telegram 群/频道' not in summary


def test_guess_source_kind_uses_host_instead_of_path_fragment():
    tab_module = load_tab_module()
    assert tab_module._guess_source_kind('https://example.com/path/t.me/demo/1') == 'web'
    assert tab_module._guess_source_kind('https://t.me/demo/1') == 'telegram_message'


def test_web_task_tab_uses_task_list_instead_of_candidate_options():
    tab = _make_web_task_tab()

    assert tab.scan_button is not None
    assert tab.task_edit is not None
    assert tab.output_subdir_checkbox is not None
    assert tab.proxy_host_edit is not None
    assert tab.proxy_port_edit is not None
    assert tab.proxy_host_edit.text() == '127.0.0.1'
    assert getattr(tab, 'web_candidate_mode_combo', None) is None
    assert getattr(tab, 'web_candidate_index_edit', None) is None


def test_format_web_task_summary_can_show_scan_results():
    tab_module = load_tab_module()
    summary = tab_module.format_web_task_summary(
        ['https://example.com/a'],
        {'https://example.com/a': {'success': True, 'candidate_count': 2}},
        ['https://cdn.example.com/a.mp4'],
    )
    assert '2 个候选' in summary
    assert '任务区: 1 个视频' in summary


def test_format_web_candidate_lines_uses_requested_queue_text():
    tab_module = load_tab_module()
    lines = tab_module.format_web_candidate_lines([
        {
            'source_url': 'https://example.com/course',
            'success': True,
            'candidates': [
                'https://cdn.example.com/a.mp4',
                'https://cdn.example.com/b.mp4',
            ],
        }
    ])
    assert lines == [
        '1.course_001：https://cdn.example.com/a.mp4',
        '2.course_002：https://cdn.example.com/b.mp4',
    ]


def test_append_web_queue_text_deduplicates_and_renumbers():
    tab_module = load_tab_module()
    merged = tab_module.append_web_queue_text(
        '9.旧名字：https://cdn.example.com/existing.mp4',
        '\n'.join([
            '1.course_001：https://cdn.example.com/existing.mp4',
            '2.course_002：https://cdn.example.com/new.mp4',
        ]),
    )
    assert merged == '\n'.join([
        '1.旧名字：https://cdn.example.com/existing.mp4',
        '2.course_002：https://cdn.example.com/new.mp4',
    ])


def test_web_queue_delete_button_uses_text_symbol_not_emoji():
    source = (ROOT / 'tab_task_list.py').read_text(encoding='utf-8')
    assert "QPushButton('\\u00d7')" in source
    assert "QPushButton('❌')" not in source
    assert "font-family:'Segoe UI','Arial',sans-serif" in source


def test_web_queue_delete_button_ignores_clicked_checked_arg():
    widget = _make_web_task_list()
    line = load_tab_module().format_web_queue_line(1, 'course_001', 'https://cdn.example.com/a.mp4')
    widget.setPlainText(line)

    entry_widget = widget.itemWidget(widget.item(0))
    entry_widget.del_btn.clicked.emit(True)

    assert widget.count() == 0


def test_web_queue_title_edit_has_polished_editing_surface():
    widget = _make_web_task_list()
    line = load_tab_module().format_web_queue_line(1, 'course_001', 'https://cdn.example.com/a.mp4')
    widget.setPlainText(line)

    title_edit = widget.itemWidget(widget.item(0)).title_edit
    style = title_edit.styleSheet()

    assert title_edit.width() >= 56
    assert 'border:1px solid transparent' in style
    assert 'border-radius:5px' in style
    assert 'selection-background-color' in style
    assert 'QLineEdit[readOnly="true"]:hover' in style


def test_web_queue_entry_shows_macos_style_metadata():
    widget = _make_web_task_list()
    line = load_tab_module().format_web_queue_line(1, 'course_001', 'https://cdn.example.com/a/b/c.mp4')
    widget.setPlainText(line)

    entry_widget = widget.itemWidget(widget.item(0))

    assert entry_widget.index_badge.text() == '01'
    assert entry_widget.host_label.text() == 'cdn.example.com'
    assert entry_widget.scheme_badge.text() == 'HTTPS'
    assert entry_widget.path_label.text() == 'b/c.mp4'
    assert entry_widget.url_label.text() == 'https://cdn.example.com/a/b/c.mp4'
    assert entry_widget.sizeHint().height() >= 82
    assert 'rgba(255, 255, 255, 0.035)' in entry_widget.index_badge.styleSheet()
    assert 'font-size:16px' in entry_widget.del_btn.styleSheet()
    assert 'rgba(255, 95, 86, 0.18)' in entry_widget.del_btn.styleSheet()


def test_web_queue_rename_rejects_blank_title():
    widget = _make_web_task_list()
    line = load_tab_module().format_web_queue_line(1, 'course_001', 'https://cdn.example.com/a.mp4')
    widget.setPlainText(line)
    entry_widget = widget.itemWidget(widget.item(0))

    widget._renameByWidget(entry_widget, '   ')

    assert widget.toPlainText() == line
    assert entry_widget.title_edit.text() == 'course_001'


def test_web_queue_rename_syncs_same_source_items():
    tab = _make_web_task_tab()
    widget = tab.task_edit
    tab.web_candidate_sources = {
        'https://cdn.example.com/a.mp4': 'https://example.com/course',
        'https://cdn.example.com/b.mp4': 'https://example.com/course',
    }
    widget.setPlainText('\n'.join([
        load_tab_module().format_web_queue_line(1, 'course_002', 'https://cdn.example.com/a.mp4'),
        load_tab_module().format_web_queue_line(2, 'course_003', 'https://cdn.example.com/b.mp4'),
    ]))
    entry_widget = widget.itemWidget(widget.item(0))

    widget._renameByWidget(entry_widget, '哈哈')

    tab_module = load_tab_module()
    titles = [tab_module.parse_web_queue_entry(widget.item(i).data(256))['title'] for i in range(widget.count())]
    assert titles == ['哈哈_001', '哈哈_002']


def test_web_queue_apply_theme_refreshes_existing_entry_widgets():
    widget = _make_web_task_list()
    line = load_tab_module().format_web_queue_line(1, 'course_001', 'https://cdn.example.com/a.mp4')
    widget.setPlainText(line)
    entry_widget = widget.itemWidget(widget.item(0))

    assert 'rgba(63, 70, 82, 0.58)' in entry_widget.styleSheet()
    widget.applyTheme('light')

    assert 'rgba(255, 255, 255, 0.76)' in widget.styleSheet()
    assert 'rgba(255, 255, 255, 0.72)' in entry_widget.styleSheet()
    assert 'rgba(255, 95, 86, 0.14)' in entry_widget.del_btn.styleSheet()
    assert 'rgba(255, 255, 255, 0.76)' in widget.viewport().styleSheet()


def test_web_queue_completed_url_matches_colon_separated_line():
    tab_task_list = (ROOT / 'tab_task_list.py').read_text(encoding='utf-8')
    assert 'parse_web_queue_entry(line)' in tab_task_list
    line = '1.course_001：https://cdn.example.com/a.mp4'
    assert [u for u in line.split() if u.startswith('http')] == []
    entry = load_tab_module().parse_web_queue_entry(line)
    assert entry['url'] == 'https://cdn.example.com/a.mp4'


def test_build_web_queue_tasks_applies_one_custom_name_to_same_source():
    tab_module = load_tab_module()
    tasks = tab_module.build_web_queue_tasks(
        [
            '1.课程：https://cdn.example.com/a.mp4',
            '2.course_002：https://cdn.example.com/b.mp4',
        ],
        {
            'https://cdn.example.com/a.mp4': 'https://example.com/course',
            'https://cdn.example.com/b.mp4': 'https://example.com/course',
        },
    )
    assert tasks == [
        {'title': '课程_001', 'url': 'https://cdn.example.com/a.mp4'},
        {'title': '课程_002', 'url': 'https://cdn.example.com/b.mp4'},
    ]



def test_build_web_queue_tasks_inherits_custom_name_after_leading_item_removed():
    tab_module = load_tab_module()
    tasks = tab_module.build_web_queue_tasks([
        tab_module.format_web_queue_line(1, 'custom', 'https://cdn.example.com/b.mp4'),
        tab_module.format_web_queue_line(2, 'course_003', 'https://cdn.example.com/c.mp4'),
    ], {
        'https://cdn.example.com/b.mp4': 'https://example.com/course',
        'https://cdn.example.com/c.mp4': 'https://example.com/course',
    })
    assert tasks == [
        {'title': 'custom_001', 'url': 'https://cdn.example.com/b.mp4'},
        {'title': 'custom_002', 'url': 'https://cdn.example.com/c.mp4'},
    ]


def test_build_web_queue_tasks_keeps_two_custom_names_for_same_source():
    tab_module = load_tab_module()
    tasks = tab_module.build_web_queue_tasks(
        [
            '1.片头：https://cdn.example.com/a.mp4',
            '2.正片：https://cdn.example.com/b.mp4',
        ],
        {
            'https://cdn.example.com/a.mp4': 'https://example.com/course',
            'https://cdn.example.com/b.mp4': 'https://example.com/course',
        },
    )
    assert tasks == [
        {'title': '片头', 'url': 'https://cdn.example.com/a.mp4'},
        {'title': '正片', 'url': 'https://cdn.example.com/b.mp4'},
    ]


def test_web_queue_output_subdir_title_drops_number_suffix():
    tab_module = load_tab_module()
    assert tab_module.web_queue_output_subdir_title('course_001') == 'course'
    assert tab_module.web_queue_output_subdir_title('course_002') == 'course'


def test_summarize_download_results_includes_counts():
    tab_module = load_tab_module()
    results = [
        {'success': True, 'downloaded_count': 2},
        {'success': False, 'downloaded_count': 0},
        {'success': True, 'downloaded_count': 3},
    ]
    assert tab_module.summarize_download_results(results) == [
        '任务总数: 3',
        '成功任务: 2',
        '失败任务: 1',
        '下载文件: 5',
    ]


# ---------------------------------------------------------------------------
# web_backend helper functions
# ---------------------------------------------------------------------------

def test_speed_to_concurrency():
    wb = load_web_backend()
    assert wb._speed_to_concurrency(0) == 3
    assert wb._speed_to_concurrency(-1) == 3
    assert wb._speed_to_concurrency(0.3 * 1024 * 1024) == 2
    assert wb._speed_to_concurrency(1 * 1024 * 1024) == 3
    assert wb._speed_to_concurrency(3 * 1024 * 1024) == 4
    assert wb._speed_to_concurrency(6 * 1024 * 1024) == 6
    assert wb._speed_to_concurrency(15 * 1024 * 1024) == 8


def test_parse_speed_bytes():
    wb = load_web_backend()
    assert wb._parse_speed_bytes('2.5 MiB/s') == 2.5 * 1024 * 1024
    assert wb._parse_speed_bytes('500 KiB/s') == 500 * 1024
    assert wb._parse_speed_bytes('') == 0.0
    assert wb._parse_speed_bytes('100') == 100


def test_normalize_aria2_speed():
    wb = load_web_backend()
    assert wb._normalize_aria2_speed('4.5MiB') == '4.5MiB/s'
    assert wb._normalize_aria2_speed('4.5MiB/s') == '4.5MiB/s'
    assert wb._normalize_aria2_speed('') == ''


def test_normalize_aria2_eta():
    wb = load_web_backend()
    assert wb._normalize_aria2_eta('1m30s') == '01:30'
    assert wb._normalize_aria2_eta('2h5m') == '2:05:00'
    assert wb._normalize_aria2_eta('45s') == '00:45'
    assert wb._normalize_aria2_eta('') == ''


def test_cookie_browser_name():
    wb = load_web_backend()
    assert wb._cookie_browser_name(('chrome',)) == 'chrome'
    assert wb._cookie_browser_name('Firefox') == 'firefox'
    assert wb._cookie_browser_name('') == ''
    assert wb._cookie_browser_name(None) == ''


def test_clean_ytdlp_error_detail_dedupes_repeated_error_prefixes():
    wb = load_web_backend()
    message = wb._clean_ytdlp_error_detail(RuntimeError(
        '\x1b[0;31mERROR:\x1b[0m \x1b[0;31mERROR:\x1b[0m Could not copy Chrome cookie database.\n'
        'ERROR: Could not copy Chrome cookie database.'
    ))
    assert message == 'ERROR: Could not copy Chrome cookie database.'


def test_run_ytdlp_with_cookie_retry_falls_back_without_browser_cookies_when_cookie_db_locked():
    wb = load_web_backend()
    calls: list[dict[str, object]] = []

    def runner(opts):
        calls.append(dict(opts))
        if opts.get('cookiesfrombrowser'):
            raise RuntimeError('ERROR: ERROR: Could not copy Chrome cookie database.')
        return {'ok': True}

    result = wb._run_ytdlp_with_cookie_retry(
        'https://www.bilibili.com/video/BV1xx',
        {'cookiesfrombrowser': ('chrome',)},
        None,
        runner,
    )

    assert result == {'ok': True}
    assert calls == [
        {'cookiesfrombrowser': ('chrome',)},
        {},
    ]


def test_normalize_douyin_play_url():
    wb = load_web_backend()
    assert wb._normalize_douyin_play_url('https://x.com/playwm/123') == 'https://x.com/play/123'
    assert wb._normalize_douyin_play_url('') == ''


def test_is_douyin_url():
    wb = load_web_backend()
    assert wb._is_douyin_url('https://www.douyin.com/video/123') is True
    assert wb._is_douyin_url('https://example.com') is False


def test_is_m3u8_url():
    wb = load_web_backend()
    assert wb._is_m3u8_url('https://cdn.example.com/live.m3u8') is True
    assert wb._is_m3u8_url('https://cdn.example.com/live.m3u8?token=abc') is True
    assert wb._is_m3u8_url('https://example.com/video.mp4') is False


def test_normalize_web_candidate_url():
    wb = load_web_backend()
    assert wb._normalize_web_candidate_url('//cdn.example.com/a.mp4', 'https://example.com') == 'https://cdn.example.com/a.mp4'
    assert wb._normalize_web_candidate_url('/media/a.mp4', 'https://example.com') == 'https://example.com/media/a.mp4'
    assert wb._normalize_web_candidate_url('https://other.com/a.mp4', 'https://example.com') == 'https://other.com/a.mp4'
    assert wb._normalize_web_candidate_url('javascript:void(0)', 'https://example.com') == ''
    assert wb._normalize_web_candidate_url('', 'https://example.com') == ''
