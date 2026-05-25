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


def test_tool_definitions_include_image_convert_pdf_split_video_downloaders_base64_file_sorter_same_and_batch_rename_tools():
    toolbox = load_module()
    titles = [item['title'] for item in toolbox.get_tool_definitions()]
    assert '鍥剧墖鏍煎紡浜掕浆' in titles
    assert 'PDF宸ュ叿' in titles
    assert 'TG涓嬭浇' in titles
    assert '缃戦〉瑙嗛涓嬭浇' in titles
    assert '鎵归噺鍛藉悕' in titles
    assert '鏂囦欢鍒嗙被' in titles
    assert '閲嶅鏂囦欢' in titles
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


def test_get_video_downloader_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_video_downloader_module()
    assert hasattr(module, 'parse_task_lines')
    assert hasattr(module, 'classify_source')
    assert hasattr(module, 'download_batch')


def test_get_base64_module_loads_converter_helpers():
    toolbox = load_module()
    module = toolbox.get_base64_module()
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
    assert toolbox.FILE_SORTER_DIR.name == '鍒嗙被'
    assert (ROOT / '鍒嗙被' / 'converter.py').exists()
    assert (ROOT / '鍒嗙被' / 'tab.py').exists()


def test_name_modules_live_under_name_directory():
    toolbox = load_module()
    assert toolbox.NAME_DIR.name == 'name'
    assert (ROOT / 'name' / 'converter.py').exists()
    assert (ROOT / 'name' / 'tab.py').exists()


def test_video_downloader_modules_live_under_video_downloader_directory():
    toolbox = load_module()
    assert toolbox.VIDEO_DOWNLOADER_DIR.name == 'video-downloader'
    assert (ROOT / 'video-downloader' / 'converter.py').exists()
    assert (ROOT / 'video-downloader' / 'tab.py').exists()


def test_get_same_module_loads_duplicate_helpers():
    toolbox = load_module()
    module = toolbox.get_same_module()
    assert hasattr(module, 'scan_files')
    assert hasattr(module, 'find_duplicate_groups')
    assert hasattr(module, 'move_duplicates')


def test_validate_pdf_form_requires_output_and_extra_fields_for_text_actions():
    toolbox = load_module()
    errors = toolbox.validate_pdf_form('text', [], '', '', '', '150')
    assert '璇ュ姛鑳藉彧鏀寔鍗曚釜 PDF' in errors
    assert '璇烽€夋嫨杈撳嚭鐩綍' in errors


def test_password_hash_roundtrip_and_verify_user_credentials():
    toolbox = load_module()
    hashed = toolbox.hash_password('Aa11!!Bb22@1')
    assert hashed != 'Aa11!!Bb22@1'
    assert toolbox.verify_password('Aa11!!Bb22@1', hashed)
    assert not toolbox.verify_password('wrong', hashed)


def test_password_policy_enforces_exact_12_chars_and_pattern_rules():
    toolbox = load_module()
    assert toolbox.validate_password_policy('Aa11!!Bb22@1') == []
    errors = toolbox.validate_password_policy('Aa11!!Bb22@12')
    assert any('涓ユ牸绛変簬 12 浣? in item for item in errors)
    errors = toolbox.validate_password_policy('aA11!!Bb22@1')
    assert any('棣栧瓧绗﹀繀椤绘槸澶у啓瀛楁瘝' in item for item in errors)
    errors = toolbox.validate_password_policy('Aa11!!Bb22@A')
    assert any('灏惧瓧绗﹀繀椤绘槸鏁板瓧' in item for item in errors)
    errors = toolbox.validate_password_policy('Aa!!BcdeFg@1')
    assert any('鍚勮嚦灏?2 涓? in item for item in errors)
    errors = toolbox.validate_password_policy('Aa111!Bb22@1')
    assert any('杩炵画 3 浣嶇浉鍚屽瓧绗? in item for item in errors)
    errors = toolbox.validate_password_policy('Abc123!!De@1')
    assert any('杩炵画 3 浣嶉『搴忓瓧绗? in item for item in errors)
    errors = toolbox.validate_password_policy('Aa!!Bb2024C1')
    assert any('涓嶈兘鍖呭惈' in item for item in errors)
    errors = toolbox.validate_password_policy('Aa11!!Bb22?1')
    assert any('鐗规畩绗﹀彿鍙兘浠? in item for item in errors)


def test_ensure_default_admin_user_creates_admin_account_once():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        created = toolbox.ensure_default_admin_user(store)
        assert created is True
        assert toolbox.verify_user_credentials(store, 'admin', '123')
        created_again = toolbox.ensure_default_admin_user(store)
        assert created_again is False
        users = toolbox.load_users(store)
        assert [item['username'] for item in users] == ['admin']


def test_register_user_allows_admin_password_123_only_for_admin_exception():
    toolbox = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        created = toolbox.register_user(store, 'admin', '123')
        assert created['username'] == 'admin'
        assert toolbox.verify_user_credentials(store, 'admin', '123')
        try:
            toolbox.register_user(store, 'alice', '123')
        except ValueError as exc:
            assert '涓ユ牸绛変簬 12 浣? in str(exc)
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
            assert '宸插瓨鍦? in str(exc)
        else:
            raise AssertionError('expected duplicate username error')


def test_validate_auth_form_requires_username_and_password_lengths():
    toolbox = load_module()
    login_errors = toolbox.validate_auth_form('', '')
    assert '璇疯緭鍏ョ敤鎴峰悕' in login_errors
    assert '璇疯緭鍏ュ瘑鐮? in login_errors
    assert toolbox.validate_auth_form('admin', '123') == []
    register_errors = toolbox.validate_auth_form('ab', '123', confirm_password='12', is_register=True)
    assert any('鐢ㄦ埛鍚? in item for item in register_errors)
    assert any('涓ユ牸绛変簬 12 浣? in item or '瀵嗙爜闀垮害' in item for item in register_errors)
    assert '涓ゆ杈撳叆鐨勫瘑鐮佷笉涓€鑷? in register_errors


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
        {'title': '灏忕尗涔嬫瓕', 'artist': 'daddy', 'file_path': '/tmp/a.ncm'},
        {'title': '', 'artist': '', 'file_path': '/tmp/b.ncm'},
    ])
    assert '馃幍 宸叉坊鍔犳瓕鏇? in text
    assert '鈥?01锝滃皬鐚箣姝? in text
    assert '馃懁 daddy' in text
    assert '鈥?02锝渂' in text


def test_format_music_log_summary_uses_emoji_layout():
    toolbox = load_module()
    text = toolbox.format_music_log_summary(3, 1, 2)
    assert '鉁?杞崲瀹屾垚' in text
    assert '鉁?鎴愬姛锛?' in text
    assert '鉂?澶辫触锛?' in text
    assert '馃棏 鍒犻櫎锛?' in text


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
        toolbox.save_setting(settings, 'auth/saved_secret', toolbox.encode_saved_password('admin', '123'))
        prefs = toolbox.load_auth_preferences(settings)
        assert toolbox.should_auto_login(toolbox.load_users(store), prefs) == {'username': 'admin', 'password': '123'}


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
        toolbox.sys.executable = str(exe_dir / '鏍煎紡杞崲宸ュ叿.exe')
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


def test_should_auto_login_only_when_saved_credentials_are_valid():
    toolbox = load_module()
    prefs = {
        'last_username': 'admin',
        'remember_password': True,
        'auto_login': True,
        'saved_secret': toolbox.encode_saved_password('admin', '123'),
    }
    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / 'users.json'
        toolbox.ensure_default_admin_user(store)
        decision = toolbox.should_auto_login(toolbox.load_users(store), prefs)
        assert decision == {'username': 'admin', 'password': '123'}
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
            assert '褰撳墠瀵嗙爜' in str(exc)
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
        toolbox.ensure_default_admin_user(store)
        toolbox.save_auth_preferences(settings, 'admin', True, True, toolbox.encode_saved_password('admin', '123'))
        app = toolbox.QApplication.instance() or toolbox.QApplication([])
        dialog = toolbox.AuthDialog(settings, store)
        assert dialog.result() == toolbox.QDialog.Accepted
        assert dialog.authenticated_username == 'admin'
        dialog.show()
        app.processEvents()
        assert dialog.isVisible() is True
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
    assert state['logout_text'] == '閫€鍑鸿处鍙?


def test_build_user_menu_state_exposes_username_and_logout_action():
    toolbox = load_module()
    state = toolbox.build_user_menu_state('admin')
    assert state['username'] == 'admin'
    assert state['avatar_text'] == 'A'
    assert state['logout_text'] == '閫€鍑鸿处鍙?


def test_help_popup_state_uses_weixin_png_and_hides_on_main_area_click():
    toolbox = load_module()
    state = toolbox.build_help_popup_state(toolbox.WEIXIN_IMAGE_PATH)
    assert state['image_path'] == toolbox.WEIXIN_IMAGE_PATH
    assert state['close_on_main_click'] is True
    assert state['frameless'] is True
    assert state['max_width'] == 420
    assert state['max_height'] == 560
    assert state['caption'] == '鎰熻阿鎵撹祻'
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
        assert state['caption'] == '鎰熻阿鎵撹祻'


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
        assert window.help_caption_label.text() == '鎰熻阿鎵撹祻'
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
        click_pos = window.mapToGlobal(window.rect().center())
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
        toolbox.save_auth_preferences(settings, 'admin', True, True, toolbox.encode_saved_password('admin', '123'))
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
        assert window.hint_button.text() == '鉂?


def test_build_user_menu_state_exposes_avatar_button_and_roomier_popup_style():
    toolbox = load_module()
    state = toolbox.build_user_menu_state('admin')
    assert state['username'] == 'admin'
    assert state['avatar_text'] == 'A'
    assert state['logout_text'] == '閫€鍑鸿处鍙?
    assert state['avatar_button_size'] == 38
    assert state['avatar_border_radius'] == 19
    assert state['avatar_uses_theme_toggle_style'] is True
    assert state['menu_width'] >= 220
    assert state['menu_height'] >= 132
    assert state['menu_padding'] >= 18
    assert state['menu_spacing'] >= 12


def test_build_main_window_sidebar_includes_image_convert_pdf_split_video_downloaders_batch_rename_base64_file_sorter_and_same_tab_when_pyside_available():
    toolbox = load_module()
    if toolbox.QWidget is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        window, app = toolbox.build_main_window_for_test(tmp)
        sidebar_titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
        assert '鍥剧墖鏍煎紡浜掕浆' in sidebar_titles
        assert 'PDF宸ュ叿' in sidebar_titles
        assert 'TG涓嬭浇' in sidebar_titles
        assert '缃戦〉瑙嗛涓嬭浇' in sidebar_titles
        assert '鎵归噺鍛藉悕' in sidebar_titles
        assert '鏂囦欢鍒嗙被' in sidebar_titles
        assert '閲嶅鏂囦欢' in sidebar_titles
        assert '鍥剧墖Base64' in sidebar_titles
        assert window.stack.count() == 11
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
        assert 'QComboBox QAbstractItemView {' in toolbox.DARK_STYLESHEET
        assert 'selection-background-color: #6d94c8;' in toolbox.DARK_STYLESHEET
        assert 'border-radius: 0;' in window.image_convert_tab.jpg_background_combo.view().styleSheet()
        assert 'arrow-dark.svg' in toolbox.DARK_STYLESHEET
        assert 'arrow-light.svg' in toolbox.LIGHT_STYLESHEET
        assert 'padding: 8px 48px 8px 16px;' in toolbox.DARK_STYLESHEET
        assert 'background-color: transparent;' in toolbox.DARK_STYLESHEET
        assert 'border: none;' in toolbox.DARK_STYLESHEET
        assert 'padding: 4px 0;' in toolbox.DARK_STYLESHEET
        assert 'background-color: #eef1f5;' in toolbox.LIGHT_STYLESHEET
        assert 'QComboBox::drop-down {' in toolbox.LIGHT_STYLESHEET
        assert 'QComboBox QAbstractItemView {' in toolbox.LIGHT_STYLESHEET
        assert 'selection-background-color: #d4e4ff;' in toolbox.LIGHT_STYLESHEET
        assert 'border: 1px solid #d9dfe7;' in toolbox.LIGHT_STYLESHEET
        assert window.image_convert_tab.format_combo.minimumWidth() == 132
        assert window.image_convert_tab.jpg_background_combo.minimumWidth() == 154
        assert window.image_convert_tab.jpg_background_combo.itemText(0) == '鐧借壊'
        assert window.image_convert_tab.jpg_background_combo.itemText(1) == '榛戣壊'
        assert window.image_convert_tab.jpg_background_combo.view().objectName() == 'comboPopupView'
        assert window.image_convert_tab.jpg_background_combo.view().frameShape() == toolbox.QFrame.NoFrame
        assert window.image_convert_tab.jpg_background_combo.view().property('comboPopupTheme') == window.current_theme
        assert window.image_convert_tab.jpg_background_combo.view().spacing() == 2
        assert window.image_convert_tab.jpg_background_combo.view().sizeHintForRow(0) == 34
        assert 'comboPopupTheme' in window.image_convert_tab.jpg_background_combo.view().styleSheet()
        assert not window.image_convert_tab.format_combo.isEditable()
        assert not window.image_convert_tab.jpg_background_combo.isEditable()
        assert window.pdf_tools_tab.action_combo.minimumWidth() == 132
        assert window.pdf_tools_tab.image_format_combo.minimumWidth() == 132
        assert window.pdf_tools_tab.action_combo.itemText(0) == '鍚堝苟'
        assert window.pdf_tools_tab.action_combo.itemText(2) == '杞浘鐗?
        assert not window.pdf_tools_tab.action_combo.isEditable()
        assert not window.pdf_tools_tab.image_format_combo.isEditable()
        assert window.tg_downloader_tab.output_edit.placeholderText() == '閫夋嫨瑙嗛杈撳嚭鐩綍'
        assert window.tg_downloader_tab.run_button.text() == '寮€濮嬩笅杞?
        assert window.tg_downloader_tab.send_code_button.text() == '鍙戦€侀獙璇佺爜'
        assert window.tg_downloader_tab.check_status_button.text() == '妫€鏌ョ姸鎬?
        assert window.tg_downloader_tab.progress_bar.value() == 0
        assert window.tg_downloader_tab.task_edit.minimumHeight() == 150
        assert window.tg_downloader_tab.log.minimumHeight() == 150
        assert window.tg_downloader_tab.progress_label.text() == '绛夊緟寮€濮?
        assert window.tg_downloader_tab.overwrite_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        assert window.web_video_downloader_tab.output_edit.placeholderText() == '閫夋嫨瑙嗛杈撳嚭鐩綍'
        assert window.web_video_downloader_tab.run_button.text() == '寮€濮嬩笅杞?
        assert window.web_video_downloader_tab.progress_bar.value() == 0
        assert window.web_video_downloader_tab.task_edit.minimumHeight() == 110
        assert window.web_video_downloader_tab.log.minimumHeight() == 110
        assert window.web_video_downloader_tab.progress_label.text() == '绛夊緟寮€濮?
        assert window.web_video_downloader_tab.web_candidate_index_edit is not None
        assert window.web_video_downloader_tab.send_code_button is None
        assert window.web_video_downloader_tab.refresh_status_button is None
        assert window.web_video_downloader_tab.backend_status_label is None
        assert window.file_sorter_tab.folder_edit.placeholderText() == '閫夋嫨闇€瑕佸垎绫荤殑鏂囦欢澶?
        assert window.file_sorter_tab.run_button.text() == '寮€濮嬪垎绫?
        assert window.file_sorter_tab.mode_combo.minimumWidth() == 144
        assert window.file_sorter_tab.mode_combo.itemText(0) == '鎸夊ぇ绫诲垎绫?
        assert window.file_sorter_tab.mode_combo.itemText(1) == '鎸夊垎杈ㄧ巼鍒嗙被'
        assert window.file_sorter_tab.mode_combo.view().objectName() == 'comboPopupView'
        assert window.file_sorter_tab.mode_combo.view().frameShape() == toolbox.QFrame.NoFrame
        assert window.file_sorter_tab.mode_combo.view().property('comboPopupTheme') == window.current_theme
        assert window.file_sorter_tab.mode_combo.view().spacing() == 2
        assert window.file_sorter_tab.mode_combo.view().sizeHintForRow(0) == 34
        assert 'comboPopupTheme' in window.file_sorter_tab.mode_combo.view().styleSheet()
        assert not window.file_sorter_tab.mode_combo.isEditable()
        assert window.same_tab.folder_edit.placeholderText() == '閫夋嫨闇€瑕佹娴嬬殑鏂囦欢澶?
        assert window.same_tab.detect_button.text() == '寮€濮嬫娴?
        assert window.same_tab.move_button.text() == '绉诲姩閲嶅浠?
        assert window.same_tab.move_button.isEnabled() is False
        assert window.same_tab.recursive_checkbox.isChecked() is True
        assert window.base64_tab.mode_combo.minimumWidth() == 144
        assert window.base64_tab.mode_combo.itemText(0) == '鍥剧墖杞珺ase64'
        assert window.base64_tab.mode_combo.itemText(1) == 'Base64杞浘鐗?
        assert window.base64_tab.mode_combo.view().objectName() == 'comboPopupView'
        assert window.base64_tab.mode_combo.view().frameShape() == toolbox.QFrame.NoFrame
        assert window.base64_tab.mode_combo.view().property('comboPopupTheme') == window.current_theme
        assert window.base64_tab.mode_combo.view().spacing() == 2
        assert window.base64_tab.mode_combo.view().sizeHintForRow(0) == 34
        assert 'comboPopupTheme' in window.base64_tab.mode_combo.view().styleSheet()
        assert not window.base64_tab.mode_combo.isEditable()
        assert len(window.file_sorter_tab.category_checkboxes) == 7
        assert window.file_sorter_tab.category_checkboxes[toolbox.get_file_sorter_module().CATEGORY_ORDER[1]].isChecked() is True
        assert window.music_tab.overwrite_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        assert window.music_tab.delete_source_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        assert window.image_convert_tab.preserve_alpha_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        assert window.base64_tab.data_url_checkbox.parentWidget().styleSheet() == 'background: transparent;'
        initial_maximized = window.isMaximized()
        window.toggle_max_restore()
        assert window.isMaximized() != initial_maximized
        window.toggle_max_restore()
        assert window.isMaximized() == initial_maximized
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

