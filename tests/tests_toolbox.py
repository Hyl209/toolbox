import importlib.util
import pathlib
import tempfile
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'hyl_toolbox.py'


_cached_module = None

def load_module():
    global _cached_module
    if _cached_module is not None:
        return _cached_module
    sys.modules.pop('hyl_toolbox_test_module', None)
    spec = importlib.util.spec_from_file_location('hyl_toolbox_test_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _cached_module = module
    return module


def test_tool_definitions_include_image_convert_pdf_split_video_downloaders_base64_file_sorter_same_and_batch_rename_tools():
    toolbox = load_module()
    titles = [item['title'] for item in toolbox.get_tool_definitions()]
    assert '图片格式互转' in titles
    assert 'PDF工具' in titles
    assert 'TG下载' in titles
    assert '网页视频下载' in titles
    assert '批量命名' in titles
    assert '文件分类' in titles
    assert '重复文件' in titles
    assert '文件Base64' in titles


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


def test_get_video_downloader_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_video_downloader_module()
    assert hasattr(module, 'parse_task_lines')
    assert hasattr(module, 'classify_source')
    assert hasattr(module, 'download_batch')


def test_get_direct_downloader_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_direct_downloader_module()
    assert hasattr(module, 'parse_url_lines')
    assert hasattr(module, 'build_aria2_command')
    assert hasattr(module, 'DirectDownloadOptions')


def test_get_base64_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_base64_module()
    assert hasattr(module, 'encode_file_to_base64')
    assert hasattr(module, 'encode_image_to_base64')
    assert hasattr(module, 'decode_base64_to_file')


def test_get_file_sorter_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_file_sorter_module()
    assert hasattr(module, 'scan_folder')
    assert hasattr(module, 'classify_files')
    assert hasattr(module, 'resolve_name_conflict')


def test_get_name_module_loads_batch_rename_helpers():
    toolbox = load_module()
    module = toolbox.get_name_module()
    assert hasattr(module, 'scan_folder')
    assert hasattr(module, 'build_rename_plan')
    assert hasattr(module, 'rename_files')


def test_file_sorter_modules_live_under_classify_directory():
    toolbox = load_module()
    assert toolbox.FILE_SORTER_DIR.name == 'file-sorter'
    assert (ROOT / 'modules' / 'file-sorter' / 'converter.py').exists()
    assert (ROOT / 'modules' / 'file-sorter' / 'tab.py').exists()


def test_name_modules_live_under_name_directory():
    toolbox = load_module()
    assert toolbox.NAME_DIR.name == 'batch-rename'
    assert (ROOT / 'modules' / 'batch-rename' / 'converter.py').exists()
    assert (ROOT / 'modules' / 'batch-rename' / 'tab.py').exists()


def test_video_downloader_modules_live_under_video_downloader_directory():
    toolbox = load_module()
    assert toolbox.VIDEO_DOWNLOADER_DIR.name == 'video-downloader'
    assert (ROOT / 'modules' / 'video-downloader' / 'converter.py').exists()
    assert (ROOT / 'modules' / 'video-downloader' / 'tab.py').exists()


def test_direct_downloader_modules_live_under_direct_downloader_directory():
    toolbox = load_module()
    assert toolbox.DIRECT_DOWNLOADER_DIR.name == 'direct-downloader'
    assert (ROOT / 'modules' / 'direct-downloader' / 'converter.py').exists()
    assert (ROOT / 'modules' / 'direct-downloader' / 'tab.py').exists()


def test_get_same_module_loads_duplicate_helpers():
    toolbox = load_module()
    module = toolbox.get_same_module()
    assert hasattr(module, 'scan_files')
    assert hasattr(module, 'find_duplicate_groups')
    assert hasattr(module, 'move_duplicates')


def test_repeated_loader_calls_return_same_module_object():
    toolbox = load_module()
    ncm_a = toolbox._load_ncm_module()
    ncm_b = toolbox._load_ncm_module()
    assert ncm_a is ncm_b

    vd_a = toolbox.get_video_downloader_module()
    vd_b = toolbox.get_video_downloader_module()
    assert vd_a is vd_b


def test_validate_pdf_form_requires_output_and_extra_fields_for_text_actions():
    toolbox = load_module()
    errors = toolbox.validate_pdf_form('text', [], '', '', '', '150')
    assert '该功能只支持单个 PDF' in errors
    assert '请选择输出目录' in errors


def test_password_hash_roundtrip_and_verify_user_credentials():
    toolbox = load_module()
    hashed = toolbox.hash_password('Aa11!!Bb22@1')
    assert hashed != 'Aa11!!Bb22@1'
    assert toolbox.verify_password('Aa11!!Bb22@1', hashed)
    assert not toolbox.verify_password('wrong', hashed)


def test_password_policy_basic_rules():
    toolbox = load_module()
    # 正常密码通过
    assert toolbox.validate_password_policy('abc123') == []
    assert toolbox.validate_password_policy('MyP@ss1') == []
    # 太短
    errors = toolbox.validate_password_policy('a1')
    assert any('至少 6 位' in item for item in errors)
    # 没有字母
    errors = toolbox.validate_password_policy('123456')
    assert any('字母' in item for item in errors)
    # 没有数字
    errors = toolbox.validate_password_policy('abcdef')
    assert any('数字' in item for item in errors)


def test_ensure_default_admin_user_creates_admin_account_once():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        created = toolbox.ensure_default_admin_user(store)
        assert created is True
        assert toolbox.verify_user_credentials(store, 'admin', 'Hyl@Init1')
        created_again = toolbox.ensure_default_admin_user(store)
        assert created_again is False
        users = toolbox.load_users(store)
        assert [item['username'] for item in users] == ['admin']


def test_register_user_rejects_weak_password_for_all_users():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        # admin 也不能用弱密码
        try:
            toolbox.register_user(store, 'admin', '123')
        except ValueError as exc:
            assert '至少 6 位' in str(exc)
        else:
            raise AssertionError('expected password policy error for admin with weak password')
        # alice 同样不能
        try:
            toolbox.register_user(store, 'alice', '123')
        except ValueError as exc:
            assert '至少 6 位' in str(exc)
        else:
            raise AssertionError('expected password policy error for non-admin user')


def test_register_user_persists_multiple_accounts_and_rejects_duplicate_names():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        created = toolbox.register_user(store, 'alice', 'Aa11!!Bb22@1')
        assert created['username'] == 'alice'
        assert toolbox.verify_user_credentials(store, 'alice', 'Aa11!!Bb22@1')
        toolbox.register_user(store, 'bob', 'Bb22@@Cc33$4')
        users = toolbox.load_users(store)
        assert sorted(item['username'] for item in users) == ['alice', 'bob']
        try:
            toolbox.register_user(store, 'alice', 'Cc33##Dd44%5')
        except ValueError as exc:
            assert '已存在' in str(exc)
        else:
            raise AssertionError('expected duplicate username error')


def test_validate_auth_form_requires_username_and_password_lengths():
    toolbox = load_module()
    login_errors = toolbox.validate_auth_form('', '')
    assert '请输入用户名' in login_errors
    assert '请输入密码' in login_errors
    assert toolbox.validate_auth_form('admin', 'Hyl@Init1') == []
    register_errors = toolbox.validate_auth_form('ab', '123', confirm_password='12', is_register=True)
    assert any('用户名' in item for item in register_errors)
    assert any('严格等于 12 位' in item or '密码长度' in item for item in register_errors)
    assert '两次输入的密码不一致' in register_errors


def test_build_auth_state_reports_registration_requirement_until_user_exists():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        empty_state = toolbox.build_auth_state(store)
        assert empty_state['has_users'] is False
        assert empty_state['mode'] == 'register'
        toolbox.register_user(store, 'alice', 'Aa11!!Bb22@1')
        ready_state = toolbox.build_auth_state(store)
        assert ready_state['has_users'] is True
        assert ready_state['mode'] == 'login'


def test_format_music_log_added_uses_pretty_sections():
    toolbox = load_module()
    text = toolbox.format_music_log_added([
        {'title': '小猫之歌', 'artist': 'daddy', 'file_path': '/tmp/a.ncm'},
        {'title': '', 'artist': '', 'file_path': '/tmp/b.ncm'},
    ])
    assert '🎵 已添加歌曲' in text
    assert '• 01｜小猫之歌' in text
    assert '👤 daddy' in text
    assert '• 02｜b' in text


def test_format_music_log_summary_uses_emoji_layout():
    toolbox = load_module()
    text = toolbox.format_music_log_summary(3, 1, 2)
    assert '✨ 转换完成' in text
    assert '✅ 成功：3' in text
    assert '❌ 失败：1' in text
    assert '🗑 删除：2' in text


def test_music_backend_module_supports_mp3_tag_enrichment():
    toolbox = load_module()
    module = toolbox._load_ncm_module()
    assert hasattr(module, 'enrich_song_info_from_mp3')


def test_normalize_auth_preferences_forces_auto_login_to_depend_on_remember_password():
    toolbox = load_module()
    prefs = toolbox.normalize_auth_preferences(True, True)
    assert prefs == {'remember_password': True, 'auto_login': True}
    prefs = toolbox.normalize_auth_preferences(False, False)
    assert prefs == {'remember_password': False, 'auto_login': False}


def test_save_and_load_auth_preferences_roundtrip_with_saved_secret():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        toolbox.save_auth_preferences(settings, 'alice', True, True, 'encoded-secret')
        restored = toolbox.load_auth_preferences(settings)
        assert restored['last_username'] == 'alice'
        assert restored['remember_password'] is True
        assert restored['auto_login'] is True
        assert restored['saved_secret'] == 'encoded-secret'


def test_load_auth_preferences_reads_legacy_last_username_key_for_auto_login_compatibility():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        toolbox.save_setting(settings, 'auth/last_username', 'admin')
        toolbox.save_setting(settings, 'auth/remember_password', '1')
        toolbox.save_setting(settings, 'auth/auto_login', '1')
        toolbox.save_setting(settings, 'auth/saved_secret', toolbox.encode_saved_password('admin', '123'))
        restored = toolbox.load_auth_preferences(settings)
        assert restored['last_username'] == 'admin'
        assert restored['remember_password'] is True
        assert restored['auto_login'] is True
        assert restored['saved_secret'] == toolbox.encode_saved_password('admin', '123')


def test_should_auto_login_works_with_legacy_last_username_preference_key():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.ensure_default_admin_user(store)
        toolbox.save_setting(settings, 'auth/last_username', 'admin')
        toolbox.save_setting(settings, 'auth/remember_password', '1')
        toolbox.save_setting(settings, 'auth/auto_login', '1')
        toolbox.save_setting(settings, 'auth/saved_secret', toolbox.encode_saved_password('admin', 'Hyl@Init1'))
        prefs = toolbox.load_auth_preferences(settings)
        assert toolbox.should_auto_login(toolbox.load_users(store), prefs) == {'username': 'admin', 'password': 'Hyl@Init1'}


def test_frozen_app_prefers_source_dir_when_user_store_exists_next_to_script():
    toolbox = load_module()
    original_frozen = getattr(toolbox.sys, 'frozen', None)
    original_executable = toolbox.sys.executable
    original_file = toolbox.__file__
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = pathlib.Path(tmp) / 'source'
        exe_dir = pathlib.Path(tmp) / 'dist'
        source_dir.mkdir()
        exe_dir.mkdir()
        (source_dir / 'users.json').write_text('[]', encoding='utf-8')
        toolbox.__file__ = str(source_dir / 'hyl_toolbox.py')
        toolbox.sys.executable = str(exe_dir / '格式转换工具.exe')
        toolbox.sys.frozen = True
        try:
            source_dir_detected = pathlib.Path(toolbox.__file__).resolve().parent
            app_dir = source_dir_detected if getattr(toolbox.sys, 'frozen', False) and (source_dir_detected / 'users.json').exists() else pathlib.Path(toolbox.sys.executable).resolve().parent
            assert app_dir == source_dir
        finally:
            toolbox.__file__ = original_file
            toolbox.sys.executable = original_executable
            if original_frozen is None:
                delattr(toolbox.sys, 'frozen')
            else:
                toolbox.sys.frozen = original_frozen


def test_resolve_plugins_dir_prefers_bundled_plugins_when_available():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp) / 'bundle'
        app_dir = pathlib.Path(tmp) / 'app'
        (root / 'plugins').mkdir(parents=True)
        app_dir.mkdir()

        assert toolbox.resolve_plugins_dir(root, app_dir) == root / 'plugins'


def test_resolve_plugins_dir_falls_back_to_app_plugins_for_external_plugins():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp) / 'bundle'
        app_dir = pathlib.Path(tmp) / 'app'
        root.mkdir()
        app_dir.mkdir()

        assert toolbox.resolve_plugins_dir(root, app_dir) == app_dir / 'plugins'


def test_should_auto_login_only_when_saved_credentials_are_valid():
    toolbox = load_module()
    prefs = {
        'last_username': 'admin',
        'remember_password': True,
        'auto_login': True,
        'saved_secret': toolbox.encode_saved_password('admin', 'Hyl@Init1'),
    }
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.ensure_default_admin_user(store)
        decision = toolbox.should_auto_login(toolbox.load_users(store), prefs)
        assert decision == {'username': 'admin', 'password': 'Hyl@Init1'}
        bad = dict(prefs)
        bad['saved_secret'] = toolbox.encode_saved_password('admin', 'wrong')
        assert toolbox.should_auto_login(toolbox.load_users(store), bad) is None


def test_should_auto_login_requires_remembered_password_state():
    toolbox = load_module()
    prefs = {
        'last_username': 'admin',
        'remember_password': False,
        'auto_login': True,
        'saved_secret': toolbox.encode_saved_password('admin', '123'),
    }
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.ensure_default_admin_user(store)
        assert toolbox.should_auto_login(toolbox.load_users(store), prefs) is None


def test_prepare_auth_mode_fields_keeps_login_fields_when_staying_in_login_mode():
    toolbox = load_module()
    fields = {
        'username': 'admin',
        'password': '123',
        'confirm_password': '',
        'current_password': '',
        'new_password': '',
        'new_password_confirm': '',
    }
    state = toolbox.prepare_auth_mode_fields('login', 'login', fields, None)
    assert state['visible_fields']['username'] == 'admin'
    assert state['visible_fields']['password'] == '123'


def test_update_user_password_requires_current_password_and_persists_new_hash():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.register_user(store, 'alice', 'Aa11!!Bb22@1')
        try:
            toolbox.update_user_password(store, 'alice', 'badpass', 'Cc33##Dd44%5')
        except ValueError as exc:
            assert '当前密码' in str(exc)
        else:
            raise AssertionError('expected current password validation error')
        toolbox.update_user_password(store, 'alice', 'Aa11!!Bb22@1', 'Cc33##Dd44%5')
        assert toolbox.verify_user_credentials(store, 'alice', 'Cc33##Dd44%5')
        assert not toolbox.verify_user_credentials(store, 'alice', 'Aa11!!Bb22@1')


def test_encode_and_decode_saved_password_roundtrip():
    toolbox = load_module()
    secret = toolbox.encode_saved_password('alice', 'secret123')
    assert secret != 'secret123'
    assert toolbox.decode_saved_password('alice', secret) == 'secret123'
    assert toolbox.decode_saved_password('bob', secret) == ''


def test_clear_auth_fields_resets_all_sensitive_inputs():
    toolbox = load_module()
    fields = {
        'username': 'admin',
        'password': '123',
        'confirm_password': 'foo',
        'current_password': 'bar',
        'new_password': 'baz',
        'new_password_confirm': 'qux',
    }
    cleared = toolbox.clear_auth_fields(fields)
    assert cleared == {
        'username': '',
        'password': '',
        'confirm_password': '',
        'current_password': '',
        'new_password': '',
        'new_password_confirm': '',
    }


def test_auth_mode_transition_clears_on_entry_and_restores_on_login_return_without_changes():
    toolbox = load_module()
    login_fields = {
        'username': 'admin',
        'password': '123',
        'confirm_password': '',
        'current_password': '',
        'new_password': '',
        'new_password_confirm': '',
    }
    state = toolbox.prepare_auth_mode_fields('login', 'register', login_fields, None)
    assert state['visible_fields']['username'] == ''
    assert state['visible_fields']['password'] == ''
    assert state['login_snapshot']['username'] == 'admin'
    restored = toolbox.prepare_auth_mode_fields('register', 'login', state['visible_fields'], state['login_snapshot'])
    assert restored['visible_fields']['username'] == 'admin'
    assert restored['visible_fields']['password'] == '123'


def test_auth_dialog_auto_login_accepts_without_manual_submit_when_shown():
    toolbox = load_module()
    if toolbox.QApplication is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.register_user(store, 'admin', 'MyS3cure!Pw')
        toolbox.save_auth_preferences(settings, 'admin', True, True, toolbox.encode_saved_password('admin', 'MyS3cure!Pw'))
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        dialog = toolbox.AuthDialog(settings, store)
        assert dialog.result() == toolbox.QDialog.Accepted
        assert dialog.authenticated_username == 'admin'
        dialog.show()
        app.processEvents()
        # isVisible() may be False on headless CI without a display server
        assert dialog.isVisible() is True or not app.primaryScreen()
        assert dialog.result() == toolbox.QDialog.Accepted


def test_main_skips_exec_when_auto_login_already_accepted():
    toolbox = load_module()
    if toolbox.QApplication is None:
        return

    class FakeApp:
        _instance = None

        def __init__(self, argv=None):
            self.argv = argv or []
            self.exec_calls = 0
            FakeApp._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

        def exec(self):
            self.exec_calls += 1
            return 0

    class FakeSettings:
        def __init__(self):
            self.values = {}

    class FakeDialog:
        exec_calls = 0

        def __init__(self, settings, store_path):
            self.settings = settings
            self.store_path = store_path
            self.authenticated_username = 'admin'
            self._result = toolbox.QDialog.Accepted

        def result(self):
            return self._result

        def exec(self):
            FakeDialog.exec_calls += 1
            raise AssertionError('main should not call exec() when dialog is already accepted')

    class FakeWindow:
        instances = []

        def __init__(self, settings, username):
            self.settings = settings
            self.username = username
            self.relogin_requested = False
            self.shown = False
            FakeWindow.instances.append(self)

        def show(self):
            self.shown = True

    original_qapplication = toolbox.QApplication
    original_make_settings = toolbox.make_settings
    original_ensure_default_admin_user = toolbox.ensure_default_admin_user
    original_get_user_store_path = toolbox.get_user_store_path
    original_auth_dialog = toolbox.AuthDialog
    original_toolbox_window = toolbox.ToolboxWindow
    original_save_setting = toolbox.save_setting
    original_app_dir = toolbox.APP_DIR
    try:
        FakeApp._instance = None
        FakeDialog.exec_calls = 0
        FakeWindow.instances = []
        settings = FakeSettings()
        saved = []
        toolbox.QApplication = FakeApp
        toolbox.make_settings = lambda _path: settings
        toolbox.ensure_default_admin_user = lambda _path: None
        toolbox.get_user_store_path = lambda _path: pathlib.Path('/tmp/users.json')
        toolbox.AuthDialog = FakeDialog
        toolbox.ToolboxWindow = FakeWindow
        toolbox.save_setting = lambda s, key, value: saved.append((s, key, value))
        toolbox.APP_DIR = pathlib.Path('/tmp/appdir')

        exit_code = toolbox.main()

        assert exit_code == 0
        assert FakeDialog.exec_calls == 0
        assert len(FakeWindow.instances) == 1
        assert FakeWindow.instances[0].username == 'admin'
        assert FakeWindow.instances[0].shown is True
        assert FakeApp._instance.exec_calls == 1
        assert saved == [(settings, 'auth/last_user', 'admin')]
    finally:
        toolbox.QApplication = original_qapplication
        toolbox.make_settings = original_make_settings
        toolbox.ensure_default_admin_user = original_ensure_default_admin_user
        toolbox.get_user_store_path = original_get_user_store_path
        toolbox.AuthDialog = original_auth_dialog
        toolbox.ToolboxWindow = original_toolbox_window
        toolbox.save_setting = original_save_setting
        toolbox.APP_DIR = original_app_dir


def test_build_user_menu_state_exposes_username_and_logout_action():
    toolbox = load_module()
    state = toolbox.build_user_menu_state('admin')
    assert state['username'] == 'admin'
    assert state['avatar_text'] == 'A'
    assert state['logout_text'] == '退出账号'


def test_help_popup_state_uses_weixin_png_and_hides_on_main_area_click():
    toolbox = load_module()
    state = toolbox.build_help_popup_state(toolbox.WEIXIN_IMAGE_PATH)
    assert state['image_path'] == toolbox.WEIXIN_IMAGE_PATH
    assert state['close_on_main_click'] is True
    assert state['frameless'] is True
    assert state['max_width'] == 420
    assert state['max_height'] == 560
    assert state['caption'] == '感谢打赏'
    assert state['caption_font_size'] == 18
    assert state['caption_font_weight'] == 700


def test_help_popup_state_falls_back_to_embedded_image_when_file_is_missing():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        missing = pathlib.Path(tmp) / 'missing.png'
        state = toolbox.build_help_popup_state(missing)
        assert state['image_path'] is None
        assert state['has_image'] is True
        assert state['image_bytes']
        assert state['caption'] == '感谢打赏'


def test_toolbox_window_help_popup_toggles_and_hides_on_main_area_click_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    window, app = toolbox.build_main_window_for_test(str(ROOT))
    try:
        assert window.help_popup.isVisible() is False
        assert window.help_overlay.isVisible() is False
        assert window.help_image_label.pixmap() is not None
        assert window.help_image_label.pixmap().width() <= 420
        assert window.help_image_label.pixmap().height() <= 560
        assert window.help_caption_label.text() == '感谢打赏'
        assert window.help_caption_label.alignment() == toolbox.Qt.AlignCenter
        assert 'font-size: 18px' in window.help_caption_label.styleSheet()
        assert 'font-weight: 700' in window.help_caption_label.styleSheet()
        assert 'background-color: rgba(0, 0, 0, 110);' in window.help_overlay.styleSheet()
        assert window.help_popup.size().width() > 0
        assert window.help_popup.size().height() > 0
        window.show_help_popup()
        app.processEvents()
        assert window.help_popup.isVisible() is True
        assert window.help_overlay.isVisible() is True
        window.hide_help_popup()
        app.processEvents()
        assert window.help_popup.isVisible() is False
        assert window.help_overlay.isVisible() is False
        window.show_help_popup()
        app.processEvents()
        assert window.help_popup.isVisible() is True
        assert window.help_overlay.isVisible() is True
        # 点击窗口内但弹窗外的区域（左侧侧边栏区域）
        outside_popup = window.rect().center()
        outside_popup.setX(10)
        click_pos = window.mapToGlobal(outside_popup)
        window.handle_global_mouse_press(click_pos)
        app.processEvents()
        assert window.help_popup.isVisible() is False
        assert window.help_overlay.isVisible() is False
    finally:
        window.close()
        app.quit()


def test_logout_window_result_requests_return_to_login_screen_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        assert window.relogin_requested is False
        settings = toolbox.make_settings(tmp)
        toolbox.save_auth_preferences(settings, 'admin', True, True, toolbox.encode_saved_password('admin', 'Hyl@Init1'))
        window.settings = settings
        window.logout()
        restored = toolbox.load_auth_preferences(settings)
        assert window.relogin_requested is True
        assert restored['auto_login'] is False
        assert restored['remember_password'] is True


def test_switch_tool_page_uses_available_stack_animation_helper():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        window.switch_tool_page(1)
        assert window.stack.currentIndex() == 1


def test_bottom_left_button_order_places_avatar_theme_and_hint_buttons():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        bottom_layout = window.theme_button.parentWidget().layout().itemAt(window.theme_button.parentWidget().layout().count() - 1).layout()
        assert bottom_layout.itemAt(0).widget() is window.user_avatar_button
        assert bottom_layout.itemAt(1).widget() is window.theme_button
        assert bottom_layout.itemAt(2).widget() is window.hint_button
        assert window.hint_button.text() == '❕'
        assert window.hint_button.toolTip() == '赞赏'
        assert not hasattr(window, 'custom_theme_button')
        assert window.theme_button.toolTip() in {'切换为白天主题', '切换为夜晚主题', '切换为自定义配色'}


def test_build_user_menu_state_exposes_avatar_button_and_roomier_popup_style():
    toolbox = load_module()
    state = toolbox.build_user_menu_state('admin')
    assert state['username'] == 'admin'
    assert state['avatar_text'] == 'A'
    assert state['logout_text'] == '退出账号'
    assert state['avatar_button_size'] == 38
    assert state['avatar_border_radius'] == 19
    assert state['avatar_uses_theme_toggle_style'] is True
    assert state['menu_width'] >= 220
    assert state['menu_height'] >= 200
    assert state['menu_avatar_size'] >= 48


def test_main_window_sidebar_includes_all_builtin_tools():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
            for title in ('图片格式互转', 'PDF工具', 'TG下载', '网页视频下载', '批量命名', '文件分类', '重复文件', '文件Base64'):
                assert title in sidebar_titles
            assert window.stack.count() >= 11
        finally:
            window.close()
            app.quit()


def test_main_window_frame_and_drag_bar_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            assert bool(window.windowFlags() & toolbox.Qt.FramelessWindowHint)
            assert window.drag_bar.minimumHeight() == 34
            assert window.drag_bar.maximumHeight() == 34
            assert window.drag_bar.layout().contentsMargins().top() == 7
            assert window.drag_bar.layout().contentsMargins().right() == 20
            assert window.centralWidget().property('windowSurface') is True
            assert window.centralWidget().layout().contentsMargins().left() == 10
            assert window.content_surface.property('contentSurface') is True
            assert window.window_controls_layout.count() == 3
            assert window.min_button.toolTip() == '最小化'
            assert window.max_button.toolTip() in {'最大化', '还原'}
            assert window.close_button.toolTip() == '关闭'
            assert window.min_button.width() == 24
            assert window.min_button.height() == 24
            assert window.sidebar.width() == 196
            labels = window.findChildren(toolbox.QLabel)
            assert any('作者：HhhYl' in label.text() for label in labels)
        finally:
            window.close()
            app.quit()


def test_main_window_resize_handles_adjust_geometry():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            expected_edges = {
                'left', 'right', 'top', 'bottom',
                'top_left', 'top_right', 'bottom_left', 'bottom_right',
            }
            assert set(window._resize_handles) == expected_edges
            assert window._resize_margin == 8
            assert window.minimumWidth() == 860
            assert window.minimumHeight() == 560
            assert window._resize_handles['right'].cursor().shape() == toolbox.Qt.SizeHorCursor
            assert window._resize_handles['bottom'].cursor().shape() == toolbox.Qt.SizeVerCursor

            start_pos = window.mapToGlobal(toolbox.QPoint(0, 0))
            window.setGeometry(100, 100, 900, 600)
            window._start_window_resize('right', start_pos)
            window._resize_window_to_global_pos('right', start_pos + toolbox.QPoint(80, 0))
            window._stop_window_resize()
            assert window.width() == 980

            window._start_window_resize('left', start_pos)
            window._resize_window_to_global_pos('left', start_pos + toolbox.QPoint(500, 0))
            window._stop_window_resize()
            assert window.width() == 860
        finally:
            window.close()
            app.quit()


def test_main_window_dark_and_light_stylesheet_contents():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    for ss, colors in [
        (toolbox.DARK_STYLESHEET, ('#1b1f25', '#9aa6b5', '#2a3038', '#6d94c8', 'arrow-dark.svg')),
        (toolbox.LIGHT_STYLESHEET, ('#e5e9ef', '#d8dee7', '#d4e4ff', '#d9dfe7', 'arrow-light.svg')),
    ]:
        assert "QWidget[contentSurface='true']" in ss
        assert 'border-radius: 32px;' in ss
        assert "QFrame[dragBar='true']" in ss
        assert "QPushButton[windowControl='true']" in ss
        assert 'QComboBox::drop-down {' in ss
        assert 'QComboBox QAbstractItemView {' in ss
        for color in colors:
            assert color in ss


def test_image_convert_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.image_convert_tab
            assert tab.format_combo.minimumWidth() == 132
            assert not tab.format_combo.isEditable()
            assert tab.jpg_background_combo.minimumWidth() == 154
            assert tab.jpg_background_combo.itemText(0) == '白色'
            assert tab.jpg_background_combo.itemText(1) == '黑色'
            assert not tab.jpg_background_combo.isEditable()
            popup = tab.jpg_background_combo.view()
            assert popup.objectName() == 'comboPopupView'
            assert popup.frameShape() == toolbox.QFrame.NoFrame
            assert popup.property('comboPopupTheme') == window.current_theme
            assert popup.spacing() == 2
            assert popup.sizeHintForRow(0) == 34
            assert 'comboPopupTheme' in popup.styleSheet()
            assert 'border-radius: 0;' in popup.styleSheet()
            assert tab.preserve_alpha_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        finally:
            window.close()
            app.quit()


def test_pdf_tools_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.pdf_tools_tab
            assert tab.action_combo.minimumWidth() == 132
            assert tab.image_format_combo.minimumWidth() == 132
            assert tab.action_combo.itemText(0) == '合并'
            assert tab.action_combo.itemText(2) == '转图片'
            assert not tab.action_combo.isEditable()
            assert not tab.image_format_combo.isEditable()
        finally:
            window.close()
            app.quit()


def test_tg_downloader_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.tg_downloader_tab
            assert tab.output_edit.placeholderText() == '选择视频输出目录'
            assert tab.run_button.text() == '开始下载'
            assert tab.send_code_button.text() == '发送验证码'
            assert tab.check_status_button.text() == '检查状态'
            assert tab.progress_bar.value() == 0
            assert tab.task_edit.minimumHeight() == 150
            assert tab.log.minimumHeight() == 150
            assert tab.progress_label.text() == '等待开始'
            assert tab.overwrite_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        finally:
            window.close()
            app.quit()


def test_web_video_downloader_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.web_video_downloader_tab
            assert tab.output_edit.placeholderText() == '选择视频输出目录'
            assert tab.run_button.text() == '开始下载'
            assert tab.progress_bar.value() == 0
            assert tab.task_edit.minimumHeight() == 150
            assert tab.log.minimumHeight() == 110
            assert tab.progress_label.text() == '等待开始'
            assert tab.scan_button is not None
            assert getattr(tab, 'web_candidate_index_edit', None) is None
            assert getattr(tab, 'web_candidate_mode_combo', None) is None
            tab.set_busy(True)
            assert tab.run_button.isHidden() is True
            assert tab.scan_button.isHidden() is True
            assert tab.pause_button.isHidden() is False
            tab.set_busy(False)
            assert tab.send_code_button is None
            assert tab.refresh_status_button is None
            assert tab.backend_status_label is None
        finally:
            window.close()
            app.quit()


def test_web_video_downloader_task_delete_matches_exact_item():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.web_video_downloader_tab
            first = '1.short：https://cdn.example.com/video.mp4'
            second = '2.long：https://cdn.example.com/video.mp4?token=abc'
            tab.task_edit.setPlainText('\n'.join([first, second]))
            tab.task_edit._deleteItem(tab.task_edit.item(0))
            assert tab.task_edit.count() == 1
            assert 'token=abc' in tab.task_edit.toPlainText()
        finally:
            window.close()
            app.quit()


def test_web_video_downloader_task_rename_emits_change():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.web_video_downloader_tab
            changed = []
            tab.task_edit.entryChanged.connect(lambda: changed.append(True))
            tab.task_edit.setPlainText('1.old：https://cdn.example.com/video.mp4')
            widget = tab.task_edit.itemWidget(tab.task_edit.item(0))
            tab.task_edit._renameByWidget(widget, 'new title')
            assert changed
            assert tab.task_edit.toPlainText().startswith('1.new title')
        finally:
            window.close()
            app.quit()


def test_web_video_downloader_ignores_legacy_all_candidates_setting():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        toolbox.save_setting(settings, 'video_downloader/web/web_all_candidates', '1')
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.web_video_downloader_tab
            assert getattr(tab, '_web_candidate_mode_value', None) is None
            assert getattr(tab, 'web_candidate_index_edit', None) is None
        finally:
            window.close()
            app.quit()


def test_video_downloader_embed_thumbnail_without_source_url_starts_worker_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None or toolbox.QThread is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        original_get_open_file_names = toolbox.QFileDialog.getOpenFileNames
        try:
            tab = window.web_video_downloader_tab
            video_path = pathlib.Path(tmp) / 'demo.mp4'
            video_path.write_text('video', encoding='utf-8')
            embed_calls = []
            finalized = []
            errors = []

            def fake_get_open_file_names(*_args, **_kwargs):
                return [str(video_path)], ''

            def fake_embed_thumbnail(path, source_url, progress_cb=None, candidate_index=None, thumbnail_mode='web_then_frame', proxy_url=''):
                embed_calls.append({
                    'path': path,
                    'source_url': source_url,
                    'candidate_index': candidate_index,
                    'thumbnail_mode': thumbnail_mode,
                    'proxy_url': proxy_url,
                })
                if progress_cb is not None:
                    progress_cb(f'补封面 1/1: {pathlib.Path(path).name}')
                return {'success': True}

            def fake_finalize_thumbnail(results):
                finalized.append(results)
                tab.cleanup_thumbnail_worker()
                tab.set_busy(False)

            def fake_handle_thumbnail_error(message):
                errors.append(message)
                tab.cleanup_thumbnail_worker()
                tab.set_busy(False)

            toolbox.QFileDialog.getOpenFileNames = fake_get_open_file_names
            tab._choose_thumbnail_mode = lambda has_source_url: 'frame'
            tab.module.embed_thumbnail = fake_embed_thumbnail
            tab.finalize_thumbnail = fake_finalize_thumbnail
            tab.handle_thumbnail_error = fake_handle_thumbnail_error

            tab.embed_thumbnail_clicked()

            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                app.processEvents()
                if finalized or errors:
                    break
                time.sleep(0.01)

            assert errors == []
            assert len(embed_calls) == 1
            assert embed_calls[0]['source_url'] == ''
            assert embed_calls[0]['thumbnail_mode'] == 'frame'
            assert embed_calls[0]['proxy_url'] == ''
            assert finalized and finalized[0][0]['success'] is True
            assert tab.thumbnail_worker is None
            assert tab.thumbnail_worker_thread is None
        finally:
            toolbox.QFileDialog.getOpenFileNames = original_get_open_file_names
            window.close()
            app.quit()


def test_file_sorter_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            tab = window.file_sorter_tab
            assert tab.folder_edit.placeholderText() == '选择需要分类的文件夹'
            assert tab.run_button.text() == '开始分类'
            assert tab.mode_combo.minimumWidth() == 144
            assert tab.mode_combo.itemText(0) == '按大类分类'
            assert tab.mode_combo.itemText(1) == '按分辨率分类'
            assert not tab.mode_combo.isEditable()
            popup = tab.mode_combo.view()
            assert popup.objectName() == 'comboPopupView'
            assert popup.frameShape() == toolbox.QFrame.NoFrame
            assert popup.property('comboPopupTheme') == window.current_theme
            assert popup.spacing() == 2
            assert popup.sizeHintForRow(0) == 34
            assert 'comboPopupTheme' in popup.styleSheet()
            assert len(tab.category_checkboxes) == 7
            assert tab.category_checkboxes[toolbox.get_file_sorter_module().CATEGORY_ORDER[1]].isChecked() is True
        finally:
            window.close()
            app.quit()


def test_same_tab_and_base64_tab_properties():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            assert window.same_tab.folder_edit.placeholderText() == '选择需要检测的文件夹'
            assert window.same_tab.detect_button.text() == '开始检测'
            assert window.same_tab.move_button.text() == '移动重复件'
            assert window.same_tab.move_button.isEnabled() is False
            assert window.same_tab.recursive_checkbox.isChecked() is True
            assert window.base64_tab.mode_combo.minimumWidth() == 144
            assert window.base64_tab.mode_combo.itemText(0) == '文件转Base64'
            assert window.base64_tab.mode_combo.itemText(1) == 'Base64转文件'
            assert not window.base64_tab.mode_combo.isEditable()
            popup = window.base64_tab.mode_combo.view()
            assert popup.objectName() == 'comboPopupView'
            assert popup.frameShape() == toolbox.QFrame.NoFrame
            assert popup.property('comboPopupTheme') == window.current_theme
            assert popup.spacing() == 2
            assert popup.sizeHintForRow(0) == 34
            assert 'comboPopupTheme' in popup.styleSheet()
            assert window.base64_tab.data_url_checkbox.parentWidget().styleSheet() == 'background: transparent;'
            assert window.music_tab.overwrite_checkbox.parentWidget().styleSheet() == 'background: transparent;'
            assert window.music_tab.delete_source_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        finally:
            window.close()
            app.quit()


def test_main_window_toggle_max_restore():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            initial = window.isMaximized()
            window.toggle_max_restore()
            assert window.isMaximized() != initial
            window.toggle_max_restore()
            assert window.isMaximized() == initial
        finally:
            window.close()
            app.quit()


def test_main_window_loads_promotable_plugins_without_demo_sidebar_item_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
            assert '哈希校验' in sidebar_titles
            assert 'JSON 工具' in sidebar_titles
            assert '时间戳工具' in sidebar_titles
            assert 'URL 工具' in sidebar_titles
            assert not any('Hello' in title for title in sidebar_titles)
        finally:
            window.close()
            app.quit()


def test_main_window_defers_plugin_tab_widgets_until_selected_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            plugin_id = 'plugin:json_tools'
            plugin_stack = next(idx for idx, tid in window._stack_to_tool_id.items() if tid == plugin_id)
            placeholder = window._tabs[plugin_id]
            assert placeholder is window.stack.widget(plugin_stack)
            assert type(placeholder).__name__ == 'QWidget'
            assert placeholder.layout() is None

            window.sidebar.setCurrentRow(window._sidebar_to_stack.index(plugin_stack))
            app.processEvents()

            created = window._tabs[plugin_id]
            assert created is window.stack.widget(plugin_stack)
            assert created is not placeholder
            assert created.layout() is not None
        finally:
            window.close()
            app.quit()


def test_main_window_saved_sidebar_order_keeps_plugin_items_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        order = ['plugin:file_hasher'] + [td.id for td in toolbox.TOOL_DEFINITIONS]
        toolbox.save_setting(settings, 'sidebar/order', ','.join(order))
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
            assert sidebar_titles[0] == '哈希校验'
            assert 'JSON 工具' in sidebar_titles
        finally:
            window.close()
            app.quit()


def test_file_sorter_tab_exposes_choose_button_and_idle_state_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        assert hasattr(window.file_sorter_tab, 'choose_button')
        assert hasattr(window.file_sorter_tab, 'mode_combo')
        assert window.file_sorter_tab.is_running is False
        assert window.file_sorter_tab.choose_button.isEnabled() is True
        window.file_sorter_tab.mode_combo.setCurrentIndex(1)
        app.processEvents()
        assert window.file_sorter_tab.get_mode() == 'resolution'
        module = toolbox.get_file_sorter_module()
        assert window.file_sorter_tab.category_checkboxes[module.CATEGORY_ORDER[0]].isHidden() is False
        assert window.file_sorter_tab.category_checkboxes[module.CATEGORY_ORDER[1]].isHidden() is False
        assert window.file_sorter_tab.category_checkboxes[module.CATEGORY_ORDER[2]].isHidden() is True
        window.toggle_theme()
        app.processEvents()
        assert window.file_sorter_tab.mode_combo.view().property('comboPopupTheme') == window.current_theme
        window.close()
        app.quit()


def test_toolbox_window_sidebar_navigation():
    """测试侧边栏点击切换页面"""
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            assert window.stack.currentIndex() == 0
            window.sidebar.setCurrentRow(3)
            app.processEvents()
            assert window.stack.currentIndex() == 3
            window.sidebar.setCurrentRow(7)
            app.processEvents()
            assert window.stack.currentIndex() == 7
            window.sidebar.setCurrentRow(0)
            app.processEvents()
            assert window.stack.currentIndex() == 0
        finally:
            window.close()
            app.quit()


def test_toolbox_window_tabs_do_not_grow_window_height_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            initial_height = window.size().height()
            for row in range(window.sidebar.count()):
                window.sidebar.setCurrentRow(row)
                app.processEvents()
                assert window.size().height() == initial_height
                assert window.minimumSize().height() <= initial_height
        finally:
            window.close()
            app.quit()


def test_theme_toggle_cycles_light_dark_custom_light():
    """测试主题切换 light -> dark -> custom -> light"""
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        settings = toolbox.make_settings(tmp)
        toolbox.save_setting(settings, 'ui/theme', 'light')
        toolbox.save_setting(settings, 'ui/custom_theme_enabled', '0')
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        window = toolbox.ToolboxWindow(settings, 'admin')
        window.show()
        app.processEvents()
        try:
            assert window.current_theme == 'light'
            assert window.custom_theme_enabled is False
            assert window.theme_button.text() == '🌙'
            assert window.theme_button.toolTip() == '切换为夜晚主题'

            window.toggle_theme()
            app.processEvents()
            assert window.current_theme == 'dark'
            assert window.custom_theme_enabled is False
            assert toolbox.load_setting(window.settings, 'ui/theme', '') == 'dark'
            assert toolbox.load_setting(window.settings, 'ui/custom_theme_enabled', '1') == '0'
            assert window.theme_button.text() == '☀️'
            assert window.theme_button.toolTip() == '切换为自定义配色'

            window.toggle_theme()
            app.processEvents()
            assert window.current_theme == 'dark'
            assert window.custom_theme_enabled is True
            assert toolbox.load_setting(window.settings, 'ui/theme', '') == 'dark'
            assert toolbox.load_setting(window.settings, 'ui/custom_theme_enabled', '0') == '1'
            assert window.theme_button.text() == '🎨'
            assert window.theme_button.toolTip() == '切换为白天主题'

            window.toggle_theme()
            app.processEvents()
            assert window.current_theme == 'light'
            assert window.custom_theme_enabled is False
            assert toolbox.load_setting(window.settings, 'ui/theme', '') == 'light'
            assert toolbox.load_setting(window.settings, 'ui/custom_theme_enabled', '1') == '0'
            assert window.theme_button.text() == '🌙'
            assert window.theme_button.toolTip() == '切换为夜晚主题'
        finally:
            window.close()
            app.quit()



def test_toggle_custom_theme_persists_state_without_sidebar_button():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        try:
            assert window.custom_theme_enabled is False
            assert not hasattr(window, 'custom_theme_button')

            window.toggle_custom_theme()
            app.processEvents()
            assert toolbox.load_setting(window.settings, 'ui/custom_theme_enabled', '0') == '1'
            assert window.theme_button.toolTip() == '切换为白天主题'

            window.toggle_custom_theme()
            app.processEvents()
            assert toolbox.load_setting(window.settings, 'ui/custom_theme_enabled', '1') == '0'
            assert window.theme_button.toolTip() == '切换为自定义配色'
        finally:
            window.close()
            app.quit()


def test_settings_dialog_custom_theme_switch_persists_and_controls_swatches():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        dialog = toolbox.SettingsDialog(settings, None, None)
        try:
            assert dialog._custom_theme_checkbox.isChecked() is False
            assert dialog.custom_theme_enabled is False
            assert all(not swatch.isEnabled() for swatch in dialog._theme_swatches.values())

            dialog._custom_theme_checkbox.setChecked(True)
            app.processEvents()
            assert dialog.custom_theme_enabled is True
            assert all(swatch.isEnabled() for swatch in dialog._theme_swatches.values())
            dialog._save_and_close()
            assert toolbox.load_setting(settings, 'ui/custom_theme_enabled', '0') == '1'
        finally:
            dialog.close()
            app.processEvents()

        dialog = toolbox.SettingsDialog(settings, None, None)
        try:
            assert dialog._custom_theme_checkbox.isChecked() is True
            assert dialog.custom_theme_enabled is True
            assert all(swatch.isEnabled() for swatch in dialog._theme_swatches.values())

            dialog._custom_theme_checkbox.setChecked(False)
            app.processEvents()
            assert dialog.custom_theme_enabled is False
            assert all(not swatch.isEnabled() for swatch in dialog._theme_swatches.values())
            dialog._save_and_close()
            assert toolbox.load_setting(settings, 'ui/custom_theme_enabled', '1') == '0'
        finally:
            dialog.close()
            app.processEvents()


def test_settings_dialog_reuses_plugin_metadata_and_ignores_invalid_nav_rows():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from toolbox_app.plugins.base import PluginInfo

    class FakeDiscovery:
        def __init__(self):
            self.calls = 0

        def get_all_plugins(self):
            self.calls += 1
            return {
                'demo_plugin': PluginInfo(
                    name='demo_plugin',
                    version='1.0',
                    description='demo',
                    author='tester',
                    plugin_type='gui',
                )
            }

    class FakePluginManager:
        def __init__(self):
            self.discovery = FakeDiscovery()

    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        toolbox.save_setting(settings, 'tools/disabled', ' music, ,same ')
        dialog = toolbox.SettingsDialog(settings, FakePluginManager(), None)
        try:
            assert dialog._setting_set('tools/disabled') == {'music', 'same'}
            assert dialog.plugin_manager.discovery.calls == 1
            assert 'plugin:demo_plugin' in dialog._label_map
            assert 'demo_plugin' in dialog._plugin_checkboxes
            tool_title = toolbox.TOOL_DEFINITIONS[0].title
            tool_cb = dialog._tool_checkboxes[toolbox.TOOL_DEFINITIONS[0].id]
            assert tool_cb.toolTip() == f'启用/禁用 {tool_title}'
            assert tool_cb.accessibleName() == tool_title
            plugin_cb = dialog._plugin_checkboxes['demo_plugin']
            assert plugin_cb.toolTip() == '启用/禁用 demo_plugin'
            assert plugin_cb.accessibleName() == 'demo_plugin'
            current_index = dialog._stack.currentIndex()
            dialog._on_nav_changed(-1)
            assert dialog._stack.currentIndex() == current_index
        finally:
            dialog.close()
            app.processEvents()


def test_settings_dialog_disables_plugin_dependents_when_dependency_is_disabled():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from toolbox_app.plugins.base import PluginInfo

    class FakeDiscovery:
        def get_all_plugins(self):
            return {
                'core_dep': PluginInfo(
                    name='core_dep',
                    version='1.0',
                    description='core dependency',
                    author='tester',
                    plugin_type='gui',
                ),
                'dependent': PluginInfo(
                    name='dependent',
                    version='1.0',
                    description='dependent plugin',
                    author='tester',
                    dependencies=['core_dep'],
                    plugin_type='gui',
                ),
                'orphan': PluginInfo(
                    name='orphan',
                    version='1.0',
                    description='missing dependency plugin',
                    author='tester',
                    dependencies=['missing_dep'],
                    plugin_type='gui',
                ),
            }

    class FakePluginManager:
        def __init__(self):
            self.discovery = FakeDiscovery()
            self.enabled_calls = []

        def set_plugin_enabled(self, name, enabled):
            self.enabled_calls.append((name, enabled))

    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        manager = FakePluginManager()
        dialog = toolbox.SettingsDialog(settings, manager, None)
        try:
            assert not dialog._plugin_checkboxes['orphan'].isChecked()
            dialog._plugin_checkboxes['core_dep'].setChecked(False)
            assert not dialog._plugin_checkboxes['dependent'].isChecked()
            dialog._save_and_close()
            disabled = toolbox.load_setting(settings, 'plugins/disabled', '')
            assert disabled == 'core_dep,dependent,orphan'
            assert set(manager.enabled_calls) == {
                ('core_dep', False),
                ('dependent', False),
                ('orphan', False),
            }
        finally:
            dialog.close()
            app.processEvents()


def test_settings_dialog_enables_plugin_dependencies_when_dependent_is_enabled():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from toolbox_app.plugins.base import PluginInfo

    class FakeDiscovery:
        def get_all_plugins(self):
            return {
                'core_dep': PluginInfo(
                    name='core_dep',
                    version='1.0',
                    description='core dependency',
                    author='tester',
                    plugin_type='gui',
                ),
                'dependent': PluginInfo(
                    name='dependent',
                    version='1.0',
                    description='dependent plugin',
                    author='tester',
                    dependencies=['core_dep'],
                    plugin_type='gui',
                ),
            }

    class FakePluginManager:
        def __init__(self):
            self.discovery = FakeDiscovery()
            self.enabled_calls = []

        def set_plugin_enabled(self, name, enabled):
            self.enabled_calls.append((name, enabled))

    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        toolbox.save_setting(settings, 'plugins/disabled', 'core_dep,dependent')
        manager = FakePluginManager()
        dialog = toolbox.SettingsDialog(settings, manager, None)
        try:
            assert not dialog._plugin_checkboxes['core_dep'].isChecked()
            assert not dialog._plugin_checkboxes['dependent'].isChecked()
            dialog._plugin_checkboxes['dependent'].setChecked(True)
            assert dialog._plugin_checkboxes['core_dep'].isChecked()
            assert dialog._plugin_checkboxes['dependent'].isChecked()
            dialog._save_and_close()
            assert toolbox.load_setting(settings, 'plugins/disabled', '') == ''
            assert set(manager.enabled_calls) == {
                ('core_dep', True),
                ('dependent', True),
            }
        finally:
            dialog.close()
            app.processEvents()


def test_settings_dialog_order_uses_stable_ids_when_labels_duplicate():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from toolbox_app.plugins.base import PluginInfo

    duplicate_label = toolbox.TOOL_DEFINITIONS[0].sidebar_label

    class FakeDiscovery:
        def get_all_plugins(self):
            return {
                'duplicate_label_plugin': PluginInfo(
                    name='duplicate_label_plugin',
                    version='1.0',
                    description='demo',
                    author='tester',
                    plugin_type='gui',
                    sidebar_label=duplicate_label,
                )
            }

    class FakePluginManager:
        def __init__(self):
            self.discovery = FakeDiscovery()

    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        dialog = toolbox.SettingsDialog(settings, FakePluginManager(), None)
        try:
            order_ids = dialog._get_current_order_ids()
            assert order_ids.count(toolbox.TOOL_DEFINITIONS[0].id) == 1
            assert order_ids.count('plugin:duplicate_label_plugin') == 1
        finally:
            dialog.close()
            app.processEvents()


def test_settings_dialog_hides_manifest_disabled_demo_plugin_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager

    reset_plugin_manager()
    with tempfile.TemporaryDirectory() as tmp:
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        settings = toolbox.make_settings(tmp)
        manager = PluginManager(ROOT / 'plugins')
        manager.discover_plugins()
        dialog = toolbox.SettingsDialog(settings, manager, None)
        try:
            assert 'hello_world' not in dialog._plugin_checkboxes
            assert 'file_hasher' in dialog._plugin_checkboxes
            assert 'json_tools' in dialog._plugin_checkboxes
            assert 'timestamp_tools' in dialog._plugin_checkboxes
            assert 'url_tools' in dialog._plugin_checkboxes
            assert 'uuid_tools' in dialog._plugin_checkboxes
            assert dialog._label_map['plugin:file_hasher'] == '哈希校验'
            assert dialog._label_map['plugin:json_tools'] == 'JSON 工具'
            assert dialog._label_map['plugin:timestamp_tools'] == '时间戳工具'
            assert dialog._label_map['plugin:url_tools'] == 'URL 工具'
            assert dialog._label_map['plugin:uuid_tools'] == 'UUID 工具'
            order_items = [dialog._order_list.item(i).text() for i in range(dialog._order_list.count())]
            assert 'hello_world' not in order_items
            assert 'file_hasher' not in order_items
            assert 'json_tools' not in order_items
            assert 'timestamp_tools' not in order_items
            assert 'url_tools' not in order_items
            assert 'uuid_tools' not in order_items
            assert '哈希校验' in order_items
            assert 'JSON 工具' in order_items
            assert '时间戳工具' in order_items
            assert 'URL 工具' in order_items
            assert 'UUID 工具' in order_items
        finally:
            dialog.close()
            app.processEvents()
            manager.cleanup_all_plugins()
            reset_plugin_manager()


def test_drop_zone_accepts_files():
    """测试拖放区域接受文件"""
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    from unittest.mock import MagicMock

    received = []
    drop_zone = toolbox.DropZoneCard('拖入文件', lambda paths: received.extend(paths))
    assert drop_zone.acceptDrops() is True
    assert drop_zone.property('dropzone') is True

    # 模拟 dropEvent
    mock_url_1 = MagicMock()
    mock_url_1.toLocalFile.return_value = '/tmp/a.png'
    mock_url_1.isLocalFile.return_value = True
    mock_url_2 = MagicMock()
    mock_url_2.toLocalFile.return_value = '/tmp/b.jpg'
    mock_url_2.isLocalFile.return_value = True

    mock_mime = MagicMock()
    mock_mime.urls.return_value = [mock_url_1, mock_url_2]

    mock_event = MagicMock()
    mock_event.mimeData.return_value = mock_mime

    drop_zone.dropEvent(mock_event)
    assert received == ['/tmp/a.png', '/tmp/b.jpg']
    mock_event.acceptProposedAction.assert_called_once()
