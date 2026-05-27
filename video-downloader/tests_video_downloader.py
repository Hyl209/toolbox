import importlib.util
import pathlib
import tempfile
import sys
import types


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
    module._INTER_TASK_DELAY_RANGE = (0, 0)
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
    module._INTER_TASK_DELAY_RANGE = (0, 0)
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


def test_download_batch_reraises_cancelled_error():
    module = load_module()
    original_download = module._download_web_task
    original_require = module._require_web_backend
    module._INTER_TASK_DELAY_RANGE = (0, 0)
    try:
        module._require_web_backend = lambda: None

        def fake_download(task, output_root, options, progress_cb):
            raise module.CancelledError('cancelled')

        module._download_web_task = fake_download
        tasks = [module.DownloadTask('https://example.com/a', 'web', 'a')]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                module.download_batch(tasks, tmp, None, module.DownloadOptions())
            except module.CancelledError:
                pass
            else:
                raise AssertionError('download_batch should reraise CancelledError')
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

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url=''):
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

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url=''):
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

        def fake_runner(source_url, output_root, options, progress_cb, title_hint='', referer_url=''):
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


def test_make_web_progress_hook_emits_speed_and_eta():
    module = load_module()
    captured: list[str] = []
    hook = module._make_web_progress_hook(captured.append)
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
    captured: list[str] = []
    hook = module._make_web_progress_hook(captured.append)
    hook({
        'status': 'downloading',
        'filename': 'demo.mp4',
        'downloaded_bytes': 25,
        'total_bytes': 100,
        'speed': 2048,
    })
    assert any(item.startswith('__HYL_PROGRESS__|web_percent|percent=25.0') for item in captured)
    assert '正在下载 "demo.mp4" "2.0 KiB/s" "25%"' in captured


def test_download_web_concurrent_reraises_cancelled_error():
    module = load_module()
    original_run = module._run_web_task
    try:
        def fake_run(task, output_root, options, progress_cb, token):
            raise module.CancelledError('cancelled')

        module._run_web_task = fake_run
        tasks = [(0, module.DownloadTask('https://example.com/a', 'web', 'a'))]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                module._download_web_concurrent(tasks, pathlib.Path(tmp), module.DownloadOptions(), None, 1, 0, 1)
            except module.CancelledError:
                pass
            else:
                raise AssertionError('_download_web_concurrent should reraise CancelledError')
    finally:
        module._run_web_task = original_run


def test_download_web_concurrent_passes_current_token_to_workers():
    module = load_module()
    original_run = module._run_web_task
    token = module.Token()
    seen = []
    try:
        module._set_current_token(token)

        def fake_run(task, output_root, options, progress_cb, passed_token):
            seen.append(passed_token)
            return module._make_result(task, True, [], '')

        module._run_web_task = fake_run
        tasks = [(0, module.DownloadTask('https://example.com/a', 'web', 'a'))]
        with tempfile.TemporaryDirectory() as tmp:
            module._download_web_concurrent(tasks, pathlib.Path(tmp), module.DownloadOptions(), None, 1, 0, 1)
        assert seen == [token]
    finally:
        module._set_current_token(None)
        module._run_web_task = original_run


def test_select_candidates_rejects_multiple_before_after_indices():
    module = load_module()
    for mode in ('before', 'after'):
        try:
            module._select_candidates(['a', 'b', 'c'], mode, [1, 2])
        except module.DownloadError as exc:
            assert 'before/after' in str(exc)
        else:
            raise AssertionError(f'{mode} should reject multiple indices')


def test_make_telegram_progress_callback_emits_speed_and_eta():
    module = load_module()
    captured: list[str] = []
    original_monotonic = module.monotonic
    times = iter([0.0, 1.0, 2.0])
    try:
        module.monotonic = lambda: next(times)
        callback = module._make_telegram_progress_callback(captured.append, 'demo.mp4')
        callback(50, 100)
        callback(100, 100)
    finally:
        module.monotonic = original_monotonic
    assert any(item.startswith('__HYL_PROGRESS__|tg_media|') and 'speed=' in item for item in captured)
    assert any(item.startswith('__HYL_PROGRESS__|tg_media|') and 'eta=' in item for item in captured)
    assert any(item.startswith('正在下载 "demo.mp4" "') and '"50%"' in item for item in captured)


def test_normalize_positive_indices_accepts_blank_and_rejects_non_positive_values():
    module = load_module()
    assert module.normalize_positive_indices('', '网页候选序号') is None
    assert module.normalize_positive_indices('2', '网页候选序号') == [2]
    assert module.normalize_positive_indices('3,4,6', '网页候选序号') == [3, 4, 6]
    try:
        module.normalize_positive_indices('0', '网页候选序号')
    except ValueError as exc:
        assert '网页候选序号 0 必须大于 0' == str(exc)
    else:
        raise AssertionError('expected invalid index error')
    try:
        module.normalize_positive_indices('3,3', '网页候选序号')
    except ValueError as exc:
        assert '重复' in str(exc)
    else:
        raise AssertionError('expected duplicate index error')


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


def test_run_download_ignores_stale_web_candidate_text_when_all_candidates_checked():
    tab_module = load_tab_module()
    module = load_module()
    captured = {}
    original_download_batch = module.download_batch
    original_expand = module._expand_web_all_candidates
    try:
        def fake_download_batch(tasks, output_dir, telegram_config, options, progress_cb=None, token=None):
            captured['options'] = options
            return []

        module.download_batch = fake_download_batch
        module._expand_web_all_candidates = lambda tasks, append_log: tasks
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
                self.task_edit = DummyField('https://example.com/post/1')
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
                self.web_candidate_index_edit = DummyField('before1')
                self.web_all_candidates_checkbox = DummyField(True)
                self.overwrite_checkbox = DummyField('')
                self.concurrent_combo = None
                self.log = types.SimpleNamespace(clear=lambda: None)
                self.worker = None
                self.worker_thread = None

            def save_form_settings(self):
                pass

            def _is_checked(self, widget):
                return widget.isChecked()

            def _widget_text(self, widget):
                if widget is self.web_candidate_index_edit:
                    raise AssertionError('stale web candidate text was read')
                return widget.text()

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

            def handle_worker_progress(self, *args):
                pass

            def finalize_download(self, *args):
                pass

            def handle_worker_error(self, *args):
                pass

            def handle_download_cancelled(self, *args):
                pass

            def _resolve_candidate_mode(self):
                return 'pick'

        tab = DummyTab()
        tab_class.run_download(tab)
        assert captured['options'].web_candidate_indices is None
        assert captured['options'].web_download_all_candidates is True
    finally:
        module.download_batch = original_download_batch
        module._expand_web_all_candidates = original_expand


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


def test_resolve_aria2c_path_prefers_bundled_binary():
    module = load_module()
    original_file = module.__file__
    original_which = module.shutil.which
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        bundled = root / 'bin' / 'aria2c.exe'
        bundled.parent.mkdir()
        bundled.write_bytes(b'fake')
        module.__file__ = str(root / 'converter.py')
        module.shutil.which = lambda name: 'C:/PATH/aria2c.exe'
        try:
            assert module._resolve_aria2c_path() == str(bundled)
        finally:
            module.__file__ = original_file
            module.shutil.which = original_which


def test_download_url_with_ytdlp_uses_aria2_and_stability_options():
    module = load_module()
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
    original_require = module._require_web_backend
    original_resolve_aria2 = module._resolve_aria2c_path
    original_ffmpeg = module.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        module._require_web_backend = lambda: None
        module._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        module.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = module._download_url_with_ytdlp(
                'https://example.com/video',
                pathlib.Path(tmp),
                module.DownloadOptions(),
                None,
                referer_url='https://example.com/post/1',
            )
        download_opts = captured_opts[-1]
        assert result['success'] is True
        assert download_opts['external_downloader'] == 'C:/tools/aria2c.exe'
        assert download_opts['continuedl'] is True
        assert download_opts['fragment_retries'] == 20
        assert download_opts['retries'] == 20
        assert download_opts['throttledratelimit'] == 100 * 1024
        assert download_opts['legacyserverconnect'] is True
        assert download_opts['http_headers']['Referer'] == 'https://example.com/post/1'
        assert '--summary-interval=1' in download_opts['external_downloader_args']
        assert '--header=Referer: https://example.com/post/1' in download_opts['external_downloader_args']
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        module._require_web_backend = original_require
        module._resolve_aria2c_path = original_resolve_aria2
        module.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_keeps_completed_file_when_aria2_finish_trips_error():
    module = load_module()
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
    original_require = module._require_web_backend
    original_resolve_aria2 = module._resolve_aria2c_path
    original_ffmpeg = module.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        module._require_web_backend = lambda: None
        module._resolve_aria2c_path = lambda: 'C:/tools/aria2c.exe'
        module.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            result = module._download_url_with_ytdlp('https://example.com/video', pathlib.Path(tmp), module.DownloadOptions(), None)
        assert result['success'] is True
        assert len(result['files']) == 1
        assert pathlib.Path(result['files'][0]).name == 'Demo [abc].mp4'
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        module._require_web_backend = original_require
        module._resolve_aria2c_path = original_resolve_aria2
        module.shutil.which = original_ffmpeg


def test_download_url_with_ytdlp_sets_legacy_server_connect_for_tls_edge_cases():
    module = load_module()
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
    original_require = module._require_web_backend
    original_resolve_aria2 = module._resolve_aria2c_path
    original_ffmpeg = module.shutil.which
    try:
        sys.modules['yt_dlp'] = fake_ytdlp
        module._require_web_backend = lambda: None
        module._resolve_aria2c_path = lambda: ''
        module.shutil.which = lambda name: ''
        with tempfile.TemporaryDirectory() as tmp:
            module._download_url_with_ytdlp('https://example.com/video', pathlib.Path(tmp), module.DownloadOptions(), None)
        assert captured_opts[0]['legacyserverconnect'] is True
        assert captured_opts[1]['legacyserverconnect'] is True
    finally:
        if original_module is None:
            sys.modules.pop('yt_dlp', None)
        else:
            sys.modules['yt_dlp'] = original_module
        module._require_web_backend = original_require
        module._resolve_aria2c_path = original_resolve_aria2
        module.shutil.which = original_ffmpeg


def test_m3u8_candidate_tries_ytdlp_before_ffmpeg_fallback():
    module = load_module()
    calls: list[str] = []
    original_ytdlp = module._download_url_with_ytdlp
    original_ffmpeg = module._download_m3u8_with_ffmpeg
    try:
        def fake_ytdlp(source_url, output_root, options, progress_cb, title_hint='', referer_url=''):
            calls.append('yt-dlp')
            assert referer_url == 'https://example.com/post/1'
            raise module.DownloadError('slow')

        def fake_ffmpeg(media_url, task, output_root, options, progress_cb, ffmpeg_path='', referer_url=''):
            calls.append('ffmpeg')
            assert referer_url == 'https://example.com/post/1'
            return {'success': True, 'files': [output_root / 'ok.mp4']}

        module._download_url_with_ytdlp = fake_ytdlp
        module._download_m3u8_with_ffmpeg = fake_ffmpeg
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            result = module._download_web_candidate('https://cdn.example.com/live.m3u8', task, pathlib.Path(tmp), module.DownloadOptions(), None, ffmpeg_path='ffmpeg')
        assert result['success'] is True
        assert calls == ['yt-dlp', 'ffmpeg']
    finally:
        module._download_url_with_ytdlp = original_ytdlp
        module._download_m3u8_with_ffmpeg = original_ffmpeg


def test_emit_aria2_progress_reports_speed_without_overall_percent():
    module = load_module()
    captured: list[str] = []
    module._emit_aria2_progress(
        captured.append,
        'demo.mp4',
        '[#abc 12MiB/100MiB(12%) CN:12 DL:4.5MiB ETA:19s]',
    )
    assert any(item.startswith('__HYL_PROGRESS__|web_aria2|') and 'speed=4.5MiB/s' in item and 'percent=12' in item and 'eta=00:19' in item for item in captured)
    assert not any(item.startswith('__HYL_PROGRESS__|web_status|') for item in captured)
    assert any('正在下载 "demo.mp4" "4.5MiB/s" "--"' in item for item in captured)


def test_ffmpeg_m3u8_command_enables_reconnect_options():
    module = load_module()
    captured: dict[str, object] = {}
    original_popen = module.subprocess.Popen
    original_probe = module._probe_stream_duration
    try:
        class FakeProcess:
            stdout = []
            returncode = 0

            def wait(self, timeout=None):
                return 0

        def fake_popen(command, **kwargs):
            captured['command'] = command
            return FakeProcess()

        module.subprocess.Popen = fake_popen
        module._probe_stream_duration = lambda url, ffmpeg_path='': None
        with tempfile.TemporaryDirectory() as tmp:
            task = module.DownloadTask('https://example.com/post/1', 'web', 'demo')
            module._download_m3u8_with_ffmpeg(
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
        module.subprocess.Popen = original_popen
        module._probe_stream_duration = original_probe


def test_hyltoolbox_spec_bundles_aria2c():
    spec_text = (ROOT.parent / 'HylToolbox.spec').read_text(encoding='utf-8')
    assert "video-downloader/bin/aria2c.exe" in spec_text
    assert "video-downloader/bin/aria2c.SHA256.txt" in spec_text


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


def test_format_web_task_summary_can_show_scan_results():
    tab_module = load_tab_module()
    summary = tab_module.format_web_task_summary(
        ['https://example.com/a'],
        {'https://example.com/a': {'success': True, 'candidate_count': 2}},
    )
    assert '2 个候选' in summary


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
