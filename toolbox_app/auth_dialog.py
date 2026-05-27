"""Extracted AuthDialog — receives all dependencies via builder."""

from __future__ import annotations

from pathlib import Path


def build_auth_dialog_class(deps: dict):
    """Return an AuthDialog class with all Qt/helper deps injected."""

    QDialog = deps['QDialog']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QCheckBox = deps['QCheckBox']
    QWidget = deps['QWidget']
    Qt = deps['Qt']
    DragTitleBar = deps['DragTitleBar']
    load_setting = deps['load_setting']
    get_theme_stylesheet = deps['get_theme_stylesheet']
    load_auth_preferences = deps['load_auth_preferences']
    decode_saved_password = deps['decode_saved_password']
    build_auth_state = deps['build_auth_state']
    should_auto_login = deps['should_auto_login']
    load_users = deps['load_users']
    prepare_auth_mode_fields = deps['prepare_auth_mode_fields']
    validate_auth_form = deps['validate_auth_form']
    register_user = deps['register_user']
    verify_user_credentials = deps['verify_user_credentials']
    normalize_auth_preferences = deps['normalize_auth_preferences']
    encode_saved_password = deps['encode_saved_password']
    save_auth_preferences = deps['save_auth_preferences']
    update_user_password = deps['update_user_password']

    class AuthDialog(QDialog):
        def __init__(self, settings, store_path: Path, parent=None):
            super().__init__(parent)
            self.settings = settings
            self.store_path = Path(store_path)
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.authenticated_username = ''
            self.mode = 'login'
            self.login_form_snapshot = None
            self.setWindowTitle('登录')
            self.setModal(True)
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            self._drag_offset = None
            self.resize(440, 360)
            self._build_ui()
            self.apply_theme()
            self.restore_saved_state()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 10, 10, 10)
            root.setSpacing(0)
            self.content_surface = QWidget()
            self.content_surface.setProperty('contentSurface', True)
            content_layout = QVBoxLayout(self.content_surface)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            self.drag_bar = DragTitleBar(self)
            self.drag_bar.title_label.setText('')
            if hasattr(self, 'min_button'):
                self.min_button.hide()
            if hasattr(self, 'max_button'):
                self.max_button.hide()
            content_layout.addWidget(self.drag_bar)
            body = QWidget()
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(24, 18, 24, 24)
            body_layout.setSpacing(14)
            self.title_label = QLabel('登录工具箱')
            self.title_label.setProperty('brandTitle', True)
            body_layout.addWidget(self.title_label)
            self.subtitle_label = QLabel('请先登录后再进入工具箱')
            self.subtitle_label.setProperty('cardSub', True)
            self.subtitle_label.setWordWrap(True)
            body_layout.addWidget(self.subtitle_label)
            self.username_edit = QLineEdit()
            self.username_edit.setPlaceholderText('用户名')
            body_layout.addWidget(self.username_edit)
            self.password_edit = QLineEdit()
            self.password_edit.setPlaceholderText('密码')
            self.password_edit.setEchoMode(QLineEdit.Password)
            body_layout.addWidget(self.password_edit)
            self.confirm_password_edit = QLineEdit()
            self.confirm_password_edit.setPlaceholderText('确认密码')
            self.confirm_password_edit.setEchoMode(QLineEdit.Password)
            body_layout.addWidget(self.confirm_password_edit)
            self.current_password_edit = QLineEdit()
            self.current_password_edit.setPlaceholderText('当前密码')
            self.current_password_edit.setEchoMode(QLineEdit.Password)
            body_layout.addWidget(self.current_password_edit)
            self.new_password_edit = QLineEdit()
            self.new_password_edit.setPlaceholderText('新密码')
            self.new_password_edit.setEchoMode(QLineEdit.Password)
            body_layout.addWidget(self.new_password_edit)
            self.new_password_confirm_edit = QLineEdit()
            self.new_password_confirm_edit.setPlaceholderText('确认新密码')
            self.new_password_confirm_edit.setEchoMode(QLineEdit.Password)
            body_layout.addWidget(self.new_password_confirm_edit)
            self.remember_checkbox = QCheckBox('记住密码')
            self.auto_login_checkbox = QCheckBox('自动登录')
            self.remember_checkbox.toggled.connect(self.on_remember_toggled)
            self.auto_login_checkbox.toggled.connect(self.on_auto_login_toggled)
            body_layout.addWidget(self.remember_checkbox)
            body_layout.addWidget(self.auto_login_checkbox)
            self.status_label = QLabel('')
            self.status_label.setWordWrap(True)
            body_layout.addWidget(self.status_label)
            button_row = QHBoxLayout()
            self.toggle_button = QPushButton('去注册')
            self.toggle_button.clicked.connect(self.toggle_mode)
            button_row.addWidget(self.toggle_button)
            self.change_password_button = QPushButton('修改密码')
            self.change_password_button.clicked.connect(lambda: self.refresh_mode('change_password'))
            button_row.addWidget(self.change_password_button)
            button_row.addStretch(1)
            self.submit_button = QPushButton('登录')
            self.submit_button.clicked.connect(self.submit)
            button_row.addWidget(self.submit_button)
            body_layout.addLayout(button_row)
            content_layout.addWidget(body)
            root.addWidget(self.content_surface)
            self.close_button.clicked.disconnect()
            self.close_button.clicked.connect(self.reject)

        def restore_saved_state(self):
            prefs = load_auth_preferences(self.settings)
            self.username_edit.setText(str(prefs['last_username']))
            self.remember_checkbox.setChecked(bool(prefs['remember_password']))
            self.auto_login_checkbox.setChecked(bool(prefs['auto_login']))
            if prefs['remember_password'] and prefs['last_username']:
                saved_password = decode_saved_password(str(prefs['last_username']), str(prefs['saved_secret']))
                if saved_password:
                    self.password_edit.setText(saved_password)
            state = build_auth_state(self.store_path)
            self.refresh_mode(state['mode'])
            auto_login_payload = should_auto_login(load_users(self.store_path), prefs)
            if state['has_users'] and auto_login_payload is not None:
                self.username_edit.setText(auto_login_payload['username'])
                self.password_edit.setText(auto_login_payload['password'])
                self.submit(auto_trigger=True)

        def apply_theme(self):
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self._set_status_error_style()

        def _set_status_error_style(self):
            self.status_label.setStyleSheet('color: #d46a6a;' if self.current_theme == 'dark' else 'color: #b74c4c;')

        def _set_status_success_style(self):
            self.status_label.setStyleSheet('color: #6fa36f;' if self.current_theme == 'dark' else 'color: #3d8b5a;')

        def start_window_drag(self, global_pos):
            self._drag_offset = global_pos - self.frameGeometry().topLeft()

        def update_window_drag(self, global_pos):
            if self._drag_offset is None:
                return
            self.move(global_pos - self._drag_offset)

        def stop_window_drag(self):
            self._drag_offset = None

        def toggle_max_restore(self):
            return

        def refresh_mode(self, mode: str):
            previous_mode = self.mode
            self.mode = mode if mode in {'register', 'change_password'} else 'login'
            transitioned = prepare_auth_mode_fields(
                previous_mode,
                self.mode,
                {
                    'username': self.username_edit.text(),
                    'password': self.password_edit.text(),
                    'confirm_password': self.confirm_password_edit.text(),
                    'current_password': self.current_password_edit.text(),
                    'new_password': self.new_password_edit.text(),
                    'new_password_confirm': self.new_password_confirm_edit.text(),
                },
                self.login_form_snapshot,
            )
            self.login_form_snapshot = transitioned['login_snapshot']
            visible_fields = transitioned['visible_fields']
            self.username_edit.setText(visible_fields['username'])
            self.password_edit.setText(visible_fields['password'])
            self.confirm_password_edit.setText(visible_fields['confirm_password'])
            self.current_password_edit.setText(visible_fields['current_password'])
            self.new_password_edit.setText(visible_fields['new_password'])
            self.new_password_confirm_edit.setText(visible_fields['new_password_confirm'])
            is_register = self.mode == 'register'
            is_change = self.mode == 'change_password'
            self.confirm_password_edit.setVisible(is_register)
            self.current_password_edit.setVisible(is_change)
            self.new_password_edit.setVisible(is_change)
            self.new_password_confirm_edit.setVisible(is_change)
            self.remember_checkbox.setVisible(not is_register and not is_change)
            self.auto_login_checkbox.setVisible(not is_register and not is_change)
            self.change_password_button.setVisible(self.mode == 'login' and build_auth_state(self.store_path)['has_users'])
            if is_register:
                self.title_label.setText('注册本地账号')
                self.subtitle_label.setText('第一次使用请先注册，本地可保存多个账号。')
                self.submit_button.setText('注册')
                self.toggle_button.setText('去登录')
            elif is_change:
                self.title_label.setText('修改密码')
                self.subtitle_label.setText('请输入当前密码并设置新密码。')
                self.submit_button.setText('确认修改')
                self.toggle_button.setText('返回登录')
            else:
                self.title_label.setText('登录工具箱')
                self.subtitle_label.setText('请输入已注册的本地账号和密码。')
                self.submit_button.setText('登录')
                self.toggle_button.setText('去注册')
            self.status_label.setText('')

        def toggle_mode(self):
            if self.mode == 'register':
                self.refresh_mode('login')
            elif self.mode == 'change_password':
                self.refresh_mode('login')
            else:
                self.refresh_mode('register')

        def on_remember_toggled(self, checked: bool):
            if not checked and self.auto_login_checkbox.isChecked():
                self.auto_login_checkbox.setChecked(False)

        def on_auto_login_toggled(self, checked: bool):
            if checked and not self.remember_checkbox.isChecked():
                self.remember_checkbox.setChecked(True)

        def submit(self, auto_trigger: bool = False):
            username = self.username_edit.text().strip()
            password = self.password_edit.text()
            self._set_status_error_style()
            if self.mode == 'change_password':
                errors = validate_auth_form(username, self.new_password_edit.text(), confirm_password=self.new_password_confirm_edit.text(), is_register=True)
                if not self.current_password_edit.text():
                    errors.append('请输入当前密码')
                if errors:
                    self.status_label.setText('\n'.join(errors))
                    return
                try:
                    update_user_password(self.store_path, username, self.current_password_edit.text(), self.new_password_edit.text())
                except ValueError as exc:
                    self.status_label.setText(str(exc))
                    return
                self._set_status_success_style()
                self.status_label.setText('密码修改成功，请使用新密码登录。')
                self.password_edit.setText(self.new_password_edit.text())
                self.current_password_edit.clear()
                self.new_password_edit.clear()
                self.new_password_confirm_edit.clear()
                self.refresh_mode('login')
                return
            confirm = self.confirm_password_edit.text()
            errors = validate_auth_form(username, password, confirm_password=confirm, is_register=self.mode == 'register')
            if errors:
                self.status_label.setText('\n'.join(errors))
                return
            try:
                if self.mode == 'register':
                    register_user(self.store_path, username, password)
                    self._set_status_success_style()
                    self.status_label.setText('注册成功，请使用新账号登录。')
                    self.password_edit.clear()
                    self.confirm_password_edit.clear()
                    self.refresh_mode('login')
                    self.username_edit.setText(username)
                    return
                if not verify_user_credentials(self.store_path, username, password):
                    self.status_label.setText('账号或密码错误')
                    return
                normalized = normalize_auth_preferences(self.remember_checkbox.isChecked(), self.auto_login_checkbox.isChecked())
                saved_secret = encode_saved_password(username, password) if normalized['remember_password'] else ''
                save_auth_preferences(self.settings, username, normalized['remember_password'], normalized['auto_login'], saved_secret)
                self.authenticated_username = username
                self.accept()
            except ValueError as exc:
                self.status_label.setText(str(exc))
                return
            if auto_trigger:
                return

    return AuthDialog
