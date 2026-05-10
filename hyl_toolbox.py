import importlib.util
import json
import os
import sys
import hashlib
import hmac
import base64
import binascii
from configparser import ConfigParser
from pathlib import Path


def build_help_popup_state(image_path: Path):
    resolved = Path(image_path)
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))
    return {
        'image_path': resolved,
        'close_on_main_click': True,
        'frameless': True,
        'max_width': 420,
        'max_height': 560,
        'caption': '感谢打赏',
        'caption_font_size': 18,
        'caption_font_weight': 700,
    }

try:
    from PySide6.QtCore import QSettings, Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEventLoop, QTimer
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QFrame,
        QGraphicsOpacityEffect,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListView,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QProgressBar,
        QScrollArea,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
        QComboBox,
        QSizePolicy,
        QStyledItemDelegate,
        QDialog,
    )
except ModuleNotFoundError:
    QSettings = None
    QApplication = None
    Qt = None
    QPoint = None
    QSize = None
    QPropertyAnimation = None
    QEasingCurve = None
    QParallelAnimationGroup = None
    QEventLoop = None
    QTimer = None
    QIcon = QPixmap = QPainter = QPen = QColor = None
    QCheckBox = QFileDialog = QFrame = QGraphicsOpacityEffect = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListView = None
    QMainWindow = QMessageBox = QPushButton = QPlainTextEdit = QProgressBar = QStackedWidget = QDialog = None
    QVBoxLayout = QWidget = QComboBox = QSizePolicy = QStyledItemDelegate = QScrollArea = None

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
SOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = SOURCE_DIR if getattr(sys, 'frozen', False) and (SOURCE_DIR / 'users.json').exists() else (Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else SOURCE_DIR)
MUSIC_DIR = ROOT / 'music'
ZIP_DIR = ROOT / 'zipandpng'
MP4_DIR = ROOT / 'mp4-mp3'
IMAGE_CONVERT_DIR = ROOT / 'image-convert'
PDF_TOOLS_DIR = ROOT / 'pdf-tools'
BASE64_DIR = ROOT / 'base64'
LOGO_PATH = ROOT / 'logo.png'
WEIXIN_IMAGE_PATH = MUSIC_DIR / 'weixin.png'
DARK_STYLESHEET = """
QMainWindow {
    background-color: #1b1f25;
}
QWidget {
    background-color: #1f2329;
    color: #eef2f7;
    font-family: 'PingFang SC', 'Source Han Sans SC', 'Microsoft YaHei UI', 'Segoe UI';
    font-size: 13px;
    font-weight: 400;
}
QWidget[windowSurface='true'] {
    background-color: #1b1f25;
    border: none;
    border-radius: 24px;
    padding: 10px;
}
QListWidget[navList='true'] {
    background-color: #1f2329;
    border: none;
    border-radius: 0;
    color: #aab4c2;
    padding: 4px 0;
    outline: none;
}
QListWidget[navList='true']::item {
    padding: 12px 14px;
    border-radius: 16px;
    margin: 4px 0;
    color: #aeb8c6;
}
QListWidget[navList='true']::item:selected {
    background-color: rgba(118, 160, 214, 0.28);
    color: #f4f7fb;
}
QListWidget[navList='true']::item:hover {
    background-color: rgba(90, 114, 145, 0.18);
}
QListWidget[navList='true'],
QListWidget[navList='true']::viewport {
    background-color: #1f2329;
}
QListWidget {
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: #aab4c2;
    padding: 4px 0;
    outline: none;
}
QListWidget::item {
    padding: 12px 14px;
    border-radius: 16px;
    margin: 4px 0;
    color: #aeb8c6;
}
QListWidget::item:selected {
    background-color: rgba(118, 160, 214, 0.28);
    color: #f4f7fb;
}
QListWidget::item:hover {
    background-color: rgba(90, 114, 145, 0.18);
}
QListWidget::item:focus,
QListWidget:focus,
QListWidget::item:selected:focus {
    outline: none;
    border: none;
}
QLineEdit, QPlainTextEdit {
    background-color: #2a3038;
    border: 1px solid #46505c;
    border-radius: 16px;
    padding: 10px 14px;
    color: #eef2f7;
    selection-background-color: #6d94c8;
}
QComboBox {
    background-color: #2a3038;
    border: 1px solid #46505c;
    border-radius: 18px;
    padding: 8px 32px 8px 16px;
    min-width: 118px;
    color: #eef2f7;
}
QComboBox:focus {
    border: 1px solid #7ea6d9;
    background-color: #303741;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
    width: 7px;
    height: 7px;
    border-right: 1.6px solid #eef2f7;
    border-bottom: 1.6px solid #eef2f7;
    transform: rotate(45deg);
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #2a3038;
    color: #eef2f7;
    border: 1px solid #46505c;
    border-radius: 14px;
    outline: none;
    padding: 6px;
    selection-background-color: #6d94c8;
    selection-color: #eef2f7;
}
QComboBox QAbstractItemView::item,
QComboBox QListView::item {
    min-height: 28px;
    padding: 6px 10px;
    border-radius: 10px;
}
QComboBox QAbstractItemView::item:selected,
QComboBox QListView::item:selected {
    background-color: #6d94c8;
    color: #eef2f7;
}
QComboBox QListView,
QComboBox QListView viewport,
QAbstractItemView,
QAbstractItemView::item,
QFrame QAbstractItemView {
    background-color: #2a3038;
    color: #eef2f7;
}
QPlainTextEdit {
    padding: 12px 14px;
}
QLineEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #7ea6d9;
    background-color: #303741;
}
QPushButton {
    background-color: #6f95c7;
    color: #eef4fb;
    border: 1px solid #7ea4d3;
    border-radius: 16px;
    padding: 9px 16px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #7b9fd0;
}
QPushButton:pressed {
    background-color: #6488b7;
}
QPushButton[windowControl='true'] {
    background-color: #9aa6b5;
    border: none;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0;
}
QPushButton[windowControl='true']:hover {
    background-color: #a9b4c1;
}
QPushButton[windowControl='true']:pressed {
    background-color: #8793a3;
}
QFrame[dragBar='true'] {
    background-color: transparent;
    border: none;
}
QFrame[dragBar='true'] QLabel {
    color: #9aa6b5;
}
QWidget[contentSurface='true'] {
    background-color: #1f2329;
    border: none;
    border-radius: 32px;
}
QFrame[navPanel='true'] {
    background-color: #1f2329;
    border: none;
}
QPushButton[themeToggle='true'] {
    background-color: rgba(58, 66, 78, 0.92);
    border: 1px solid #4b5563;
    padding: 0;
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    border-radius: 19px;
    font-size: 15px;
    font-weight: 500;
}
QCheckBox {
    color: #c8d0dc;
    spacing: 8px;
}
QProgressBar {
    border: none;
    border-radius: 8px;
    background: #2f3640;
    text-align: center;
    min-height: 8px;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #7ea6d9;
    border-radius: 8px;
}
QFrame[card='true'],
QFrame[panel='true'] {
    background-color: rgba(44, 50, 59, 0.88);
    border: 1px solid #3f4652;
    border-radius: 26px;
}
QFrame[dropzone='true'] {
    background-color: rgba(43, 49, 58, 0.92);
    border: 1px solid #4b5562;
    border-radius: 22px;
}
QFrame[dropzone='true'][active='true'] {
    background-color: rgba(62, 82, 108, 0.42);
    border: 1px solid #7ea6d9;
}
QLabel {
    color: #eef2f7;
    background: transparent;
}
QLabel[cardTitle='true'] {
    font-size: 18px;
    font-weight: 600;
    color: #f3f6fb;
}
QLabel[cardSub='true'] {
    color: #9aa6b5;
    font-size: 12px;
}
QLabel[brandTitle='true'] {
    font-size: 20px;
    font-weight: 600;
    color: #f3f6fb;
}
QLabel[brandSub='true'] {
    color: #9eabb9;
    font-size: 12px;
}
QLabel[dropBody='true'] {
    color: #a4b0bf;
    font-size: 13px;
}
"""

LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #e5e9ef;
}
QWidget {
    background-color: #eef1f5;
    color: #1f252d;
    font-family: 'PingFang SC', 'Source Han Sans SC', 'Microsoft YaHei UI', 'Segoe UI';
    font-size: 13px;
    font-weight: 400;
}
QWidget[windowSurface='true'] {
    background-color: #e5e9ef;
    border: none;
    border-radius: 24px;
    padding: 10px;
}
QListWidget[navList='true'] {
    background-color: #eef1f5;
    border: none;
    border-radius: 0;
    color: #697586;
    padding: 4px 0;
    outline: none;
}
QListWidget[navList='true']::item {
    padding: 12px 14px;
    border-radius: 16px;
    margin: 4px 0;
    color: #586474;
}
QListWidget[navList='true']::item:selected {
    background-color: #dfeafc;
    color: #1f252d;
}
QListWidget[navList='true']::item:hover {
    background-color: rgba(226, 234, 246, 0.72);
}
QListWidget[navList='true'],
QListWidget[navList='true']::viewport {
    background-color: #eef1f5;
}
QListWidget {
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: #697586;
    padding: 4px 0;
    outline: none;
}
QListWidget::item {
    padding: 12px 14px;
    border-radius: 16px;
    margin: 4px 0;
    color: #586474;
}
QListWidget::item:selected {
    background-color: #dfeafc;
    color: #1f252d;
}
QListWidget::item:hover {
    background-color: rgba(226, 234, 246, 0.72);
}
QListWidget::item:focus,
QListWidget:focus,
QListWidget::item:selected:focus {
    outline: none;
    border: none;
}
QLineEdit, QPlainTextEdit {
    background-color: #eef1f5;
    border: 1px solid #d8dee6;
    border-radius: 16px;
    padding: 10px 14px;
    color: #1f252d;
    selection-background-color: #d4e4ff;
}
QComboBox {
    background-color: #eef1f5;
    border: 1px solid #d8dee6;
    border-radius: 18px;
    padding: 8px 32px 8px 16px;
    min-width: 118px;
    color: #1f252d;
}
QComboBox:focus {
    border: 1px solid #8fb4e8;
    background-color: #e8edf4;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
    width: 7px;
    height: 7px;
    border-right: 1.6px solid #1f252d;
    border-bottom: 1.6px solid #1f252d;
    transform: rotate(45deg);
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #eef1f5;
    color: #1f252d;
    border: 1px solid #d8dee6;
    border-radius: 14px;
    outline: none;
    padding: 6px;
    selection-background-color: #d4e4ff;
    selection-color: #1f252d;
}
QComboBox QAbstractItemView::item,
QComboBox QListView::item {
    min-height: 28px;
    padding: 6px 10px;
    border-radius: 10px;
}
QComboBox QAbstractItemView::item:selected,
QComboBox QListView::item:selected {
    background-color: #d4e4ff;
    color: #1f252d;
}
QComboBox QListView,
QComboBox QListView viewport,
QAbstractItemView,
QAbstractItemView::item,
QFrame QAbstractItemView {
    background-color: #eef1f5;
    color: #1f252d;
}
QPlainTextEdit {
    padding: 12px 14px;
}
QLineEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #8fb4e8;
    background-color: #e8edf4;
}
QPushButton {
    background-color: #e4efff;
    color: #24415f;
    border: 1px solid #cfd9e8;
    border-radius: 16px;
    padding: 9px 16px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #edf4ff;
}
QPushButton:pressed {
    background-color: #d7e7fb;
}
QPushButton[windowControl='true'] {
    background-color: #d8dee7;
    border: none;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0;
}
QPushButton[windowControl='true']:hover {
    background-color: #c8d0db;
}
QPushButton[windowControl='true']:pressed {
    background-color: #b5bfcc;
}
QFrame[dragBar='true'] {
    background-color: transparent;
    border: none;
}
QFrame[dragBar='true'] QLabel {
    color: #7f8a99;
}
QWidget[contentSurface='true'] {
    background-color: #eef1f5;
    border: none;
    border-radius: 32px;
}
QFrame[navPanel='true'] {
    background-color: #eef1f5;
    border: none;
}
QPushButton[themeToggle='true'] {
    background-color: rgba(255, 255, 255, 0.82);
    border: 1px solid #d6dde7;
    padding: 0;
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    border-radius: 19px;
    font-size: 15px;
    font-weight: 500;
}
QCheckBox {
    color: #4e5968;
    spacing: 8px;
}
QProgressBar {
    border: none;
    border-radius: 8px;
    background: #dde5ee;
    text-align: center;
    min-height: 8px;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #8fb4e8;
    border-radius: 8px;
}
QFrame[card='true'],
QFrame[panel='true'] {
    background-color: rgba(255, 255, 255, 0.76);
    border: 1px solid #d9dfe7;
    border-radius: 26px;
}
QFrame[dropzone='true'] {
    background-color: rgba(248, 250, 253, 0.88);
    border: 1px solid #d8e0ea;
    border-radius: 22px;
}
QFrame[dropzone='true'][active='true'] {
    background-color: rgba(230, 239, 251, 0.92);
    border: 1px solid #8fb4e8;
}
QLabel {
    color: #1f252d;
    background: transparent;
}
QLabel[cardTitle='true'] {
    font-size: 18px;
    font-weight: 600;
    color: #20262d;
}
QLabel[cardSub='true'] {
    color: #748091;
    font-size: 12px;
}
QLabel[brandTitle='true'] {
    font-size: 20px;
    font-weight: 600;
    color: #20262d;
}
QLabel[brandSub='true'] {
    color: #7f8a99;
    font-size: 12px;
}
QLabel[dropBody='true'] {
    color: #7a8796;
    font-size: 13px;
}
"""


def get_theme_stylesheet(theme_name: str) -> str:
    return LIGHT_STYLESHEET if theme_name == 'light' else DARK_STYLESHEET


class IniSettings:
    def __init__(self, path: str):
        self.path = Path(path)
        self.parser = ConfigParser()
        if self.path.exists():
            self.parser.read(self.path, encoding='utf-8')

    def setValue(self, key: str, value: str) -> None:
        section, option = self._split_key(key)
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, option, value)

    def value(self, key: str, default: str = ''):
        section, option = self._split_key(key)
        if self.parser.has_option(section, option):
            return self.parser.get(section, option)
        return default

    def sync(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as f:
            self.parser.write(f)

    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:
        if '/' in key:
            section, option = key.split('/', 1)
            return section, option
        return 'default', key


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    parent_dir = str(file_path.parent)
    inserted = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        inserted = True
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted and sys.path[:1] == [parent_dir]:
            sys.path.pop(0)
    return module


def _load_zip_module():
    return _load_module('zipandpng_module', ZIP_DIR / 'zipandpng.py')


def _load_ncm_module():
    return _load_module('music_ncm_to_mp3', MUSIC_DIR / 'ncm_to_mp3.py')


def _load_mp4_module():
    return _load_module('mp4_converter_module', MP4_DIR / 'converter.py')


def _load_image_convert_module():
    return _load_module('image_convert_module', IMAGE_CONVERT_DIR / 'converter.py')


def _load_pdf_tools_module():
    return _load_module('pdf_tools_module', PDF_TOOLS_DIR / 'converter.py')


def make_settings(base_dir: str):
    settings_path = Path(base_dir) / 'hyl_toolbox.ini'
    if QSettings is not None:
        return QSettings(str(settings_path), QSettings.Format.IniFormat)
    return IniSettings(str(settings_path))


def save_setting(settings, key: str, value: str) -> None:
    settings.setValue(key, value)
    settings.sync()


def load_setting(settings, key: str, default: str = '') -> str:
    value = settings.value(key, default)
    return '' if value is None else str(value)


def get_user_store_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / 'users.json'


ALLOWED_PASSWORD_SYMBOLS = '!@#$%^&*()_+-='
FORBIDDEN_PASSWORD_FRAGMENTS = ('2024', '2025', '2026', 'admin', 'root', 'password')
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = '123'


def load_users(store_path: str | Path) -> list[dict[str, str]]:
    path = Path(store_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(data, list):
        return []
    users: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        username = str(item.get('username', '')).strip()
        password_hash = str(item.get('password_hash', '')).strip()
        if username and password_hash:
            users.append({'username': username, 'password_hash': password_hash})
    return users


def save_users(store_path: str | Path, users: list[dict[str, str]]) -> None:
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {'username': item['username'], 'password_hash': item['password_hash']}
        for item in users
        if item.get('username') and item.get('password_hash')
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.sha256(f'{salt}:{password}'.encode('utf-8')).hexdigest()
    return f'{salt}${digest}'


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split('$', 1)
    except ValueError:
        return False
    actual = hashlib.sha256(f'{salt}:{password}'.encode('utf-8')).hexdigest()
    return hmac.compare_digest(actual, expected)


def find_user(users: list[dict[str, str]], username: str):
    target = username.strip().casefold()
    for item in users:
        if str(item.get('username', '')).strip().casefold() == target:
            return item
    return None


def validate_password_policy(password: str, username: str = '') -> list[str]:
    clean_name = username.strip().casefold()
    if clean_name == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
        return []
    errors: list[str] = []
    if len(password) != 12:
        errors.append('密码长度必须严格等于 12 位')
    if password and not password[0].isupper():
        errors.append('首字符必须是大写字母')
    if password and not password[-1].isdigit():
        errors.append('尾字符必须是数字')
    upper_count = sum(1 for ch in password if ch.isupper())
    lower_count = sum(1 for ch in password if ch.islower())
    digit_count = sum(1 for ch in password if ch.isdigit())
    symbol_count = sum(1 for ch in password if ch in ALLOWED_PASSWORD_SYMBOLS)
    invalid_symbols = [ch for ch in password if not (ch.isupper() or ch.islower() or ch.isdigit() or ch in ALLOWED_PASSWORD_SYMBOLS)]
    if upper_count < 2 or lower_count < 2 or digit_count < 2 or symbol_count < 2:
        errors.append('密码必须包含大写字母、小写字母、数字、特殊符号各至少 2 个')
    if invalid_symbols:
        errors.append(f'特殊符号只能从 {ALLOWED_PASSWORD_SYMBOLS} 里选')
    for index in range(len(password) - 2):
        chunk = password[index:index + 3]
        if len(set(chunk)) == 1:
            errors.append('密码不能包含连续 3 位相同字符')
            break
    for index in range(len(password) - 2):
        a, b, c = password[index:index + 3]
        if ord(b) == ord(a) + 1 and ord(c) == ord(b) + 1:
            errors.append('密码不能包含连续 3 位顺序字符')
            break
    lowered = password.casefold()
    if any(fragment in lowered for fragment in FORBIDDEN_PASSWORD_FRAGMENTS):
        errors.append('密码不能包含 2024、2025、2026、admin、root、password 任何片段')
    return errors


def ensure_default_admin_user(store_path: str | Path) -> bool:
    users = load_users(store_path)
    if find_user(users, DEFAULT_ADMIN_USERNAME) is not None:
        return False
    users.append({'username': DEFAULT_ADMIN_USERNAME, 'password_hash': hash_password(DEFAULT_ADMIN_PASSWORD)})
    save_users(store_path, users)
    return True


def register_user(store_path: str | Path, username: str, password: str) -> dict[str, str]:
    clean_name = username.strip()
    users = load_users(store_path)
    if find_user(users, clean_name) is not None:
        raise ValueError('该用户名已存在')
    password_errors = validate_password_policy(password, clean_name)
    if password_errors:
        raise ValueError('\n'.join(password_errors))
    record = {'username': clean_name, 'password_hash': hash_password(password)}
    users.append(record)
    save_users(store_path, users)
    return {'username': clean_name}


def verify_user_credentials(store_path: str | Path, username: str, password: str) -> bool:
    user = find_user(load_users(store_path), username)
    if user is None:
        return False
    return verify_password(password, str(user.get('password_hash', '')))


def validate_auth_form(username: str, password: str, confirm_password: str = '', is_register: bool = False) -> list[str]:
    errors: list[str] = []
    clean_name = username.strip()
    if not clean_name:
        errors.append('请输入用户名')
    elif len(clean_name) < 3:
        errors.append('用户名至少需要 3 个字符')
    if not password:
        errors.append('请输入密码')
    elif is_register:
        errors.extend(validate_password_policy(password, clean_name))
    elif clean_name.casefold() == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
        pass
    elif len(password) < 4:
        errors.append('密码长度至少需要 4 个字符')
    if is_register and password != confirm_password:
        errors.append('两次输入的密码不一致')
    return errors


def build_auth_state(store_path: str | Path) -> dict[str, object]:
    users = load_users(store_path)
    has_users = bool(users)
    return {
        'has_users': has_users,
        'mode': 'login' if has_users else 'register',
        'user_count': len(users),
    }


def normalize_auth_preferences(remember_password: bool, auto_login: bool) -> dict[str, bool]:
    normalized_remember = bool(remember_password or auto_login)
    normalized_auto = bool(auto_login and normalized_remember)
    return {
        'remember_password': normalized_remember,
        'auto_login': normalized_auto,
    }


def encode_saved_password(username: str, password: str) -> str:
    if not username or not password:
        return ''
    key = hashlib.sha256(f'hyl-auth:{username.strip().casefold()}'.encode('utf-8')).digest()
    payload = password.encode('utf-8')
    encoded = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
    return encoded.hex()


def decode_saved_password(username: str, encoded_secret: str) -> str:
    if not username or not encoded_secret:
        return ''
    try:
        payload = bytes.fromhex(encoded_secret)
    except ValueError:
        return ''
    key = hashlib.sha256(f'hyl-auth:{username.strip().casefold()}'.encode('utf-8')).digest()
    decoded = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
    try:
        return decoded.decode('utf-8')
    except UnicodeDecodeError:
        return ''


def save_auth_preferences(settings, username: str, remember_password: bool, auto_login: bool, saved_secret: str = '') -> None:
    normalized = normalize_auth_preferences(remember_password, auto_login)
    save_setting(settings, 'auth/last_user', username.strip())
    save_setting(settings, 'auth/remember_password', '1' if normalized['remember_password'] else '0')
    save_setting(settings, 'auth/auto_login', '1' if normalized['auto_login'] else '0')
    save_setting(settings, 'auth/saved_secret', saved_secret if normalized['remember_password'] else '')


def load_auth_preferences(settings) -> dict[str, object]:
    normalized = normalize_auth_preferences(
        load_setting(settings, 'auth/remember_password', '0') == '1',
        load_setting(settings, 'auth/auto_login', '0') == '1',
    )
    last_username = load_setting(settings, 'auth/last_user', '').strip()
    if not last_username:
        last_username = load_setting(settings, 'auth/last_username', '').strip()
    return {
        'last_username': last_username,
        'remember_password': normalized['remember_password'],
        'auto_login': normalized['auto_login'],
        'saved_secret': load_setting(settings, 'auth/saved_secret', '') if normalized['remember_password'] else '',
    }


def should_auto_login(users: list[dict], prefs: dict[str, object]) -> dict[str, str] | None:
    username = str(prefs.get('last_username', '')).strip()
    if not prefs.get('remember_password') or not prefs.get('auto_login') or not username:
        return None
    password = decode_saved_password(username, str(prefs.get('saved_secret', '')))
    if not password:
        return None
    user = find_user(users, username)
    if user is None:
        return None
    if not verify_password(password, str(user.get('password_hash', ''))):
        return None
    return {
        'username': username,
        'password': password,
    }


def clear_auth_fields(fields: dict[str, str]) -> dict[str, str]:
    return {key: '' for key in fields}


def prepare_auth_mode_fields(previous_mode: str, next_mode: str, current_fields: dict[str, str], login_snapshot: dict[str, str] | None) -> dict[str, dict[str, str] | None]:
    snapshot = dict(login_snapshot or {})
    visible_fields = dict(current_fields)
    if next_mode in {'register', 'change_password'} and previous_mode == 'login':
        snapshot = dict(current_fields)
        visible_fields = clear_auth_fields(current_fields)
    elif next_mode == 'login' and previous_mode in {'register', 'change_password'} and snapshot:
        visible_fields = dict(snapshot)
    return {
        'visible_fields': visible_fields,
        'login_snapshot': snapshot or None,
    }


def build_user_menu_state(username: str) -> dict[str, str]:
    clean_name = username.strip()
    return {
        'username': clean_name or '未登录',
        'avatar_text': (clean_name[:1] or 'U').upper(),
        'logout_text': '退出账号',
        'avatar_button_size': 38,
        'avatar_border_radius': 19,
        'avatar_uses_theme_toggle_style': True,
        'menu_width': 236,
        'menu_height': 148,
        'menu_padding': 20,
        'menu_spacing': 14,
    }


def update_user_password(store_path: str | Path, username: str, current_password: str, new_password: str) -> None:
    users = load_users(store_path)
    user = find_user(users, username)
    if user is None:
        raise ValueError('账号不存在')
    if not verify_password(current_password, str(user.get('password_hash', ''))):
        raise ValueError('当前密码错误')
    password_errors = validate_password_policy(new_password, username)
    if password_errors:
        raise ValueError('\n'.join(password_errors))
    user['password_hash'] = hash_password(new_password)
    save_users(store_path, users)


def get_tool_definitions() -> list[dict]:
    return [
        {'key': 'music', 'title': 'NCM转换'},
        {'key': 'zipandpng', 'title': 'PNG伪装'},
        {'key': 'mp4mp3', 'title': 'MP4转MP3'},
        {'key': 'imageconvert', 'title': '图片格式互转'},
        {'key': 'pdftools', 'title': 'PDF工具'},
        {'key': 'base64', 'title': '图片Base64'},
    ]


def collect_music_inputs(paths: list[str]) -> list[Path]:
    ncm_module = _load_ncm_module()
    return ncm_module.collect_input_paths([Path(p) for p in paths])


def get_music_backend_status() -> tuple[bool, str]:
    ncm_module = _load_ncm_module()
    return ncm_module.probe_converter_backend()


def get_zip_module():
    return _load_zip_module()


def get_mp4_module():
    return _load_mp4_module()


def get_image_convert_module():
    return _load_image_convert_module()


def get_pdf_tools_module():
    return _load_pdf_tools_module()


def get_base64_module():
    return _load_module('base64_converter_module', BASE64_DIR / 'converter.py')


def choose_output_suffix(cover_path: str) -> str:
    suffix = Path(cover_path).suffix.lower().strip()
    if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
        return suffix
    return '.png'


def normalize_output_name(name: str, cover_path: str = '', payload_path: str = '') -> str:
    base = name.strip()
    if not base and payload_path:
        base = Path(payload_path).stem
    if not base:
        base = 'output'
    suffix = choose_output_suffix(cover_path)
    return f'{Path(base).stem}{suffix}'


def split_dropped_files(paths: list[str]) -> dict[str, str]:
    payload = ''
    cover_png = ''
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    for raw in paths:
        path = Path(raw).resolve()
        if path.suffix.lower() in image_exts and not cover_png:
            cover_png = str(path)
        elif not payload:
            payload = str(path)
    return {'payload': payload, 'cover_png': cover_png}


def format_music_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 .ncm 文件或文件夹'
    names = [p.stem for p in files[:3]]
    text = '\n'.join(names)
    if len(files) > 3:
        text += f'\n…共 {len(files)} 首歌曲'
    return text


def get_music_file_items(paths: list[str]) -> list[dict[str, str]]:
    ncm_module = _load_ncm_module()
    files = ncm_module.collect_input_paths([Path(p) for p in paths])
    return [ncm_module.extract_song_info(path) for path in files]


def build_music_item_text(item: dict[str, str]) -> str:
    title = str(item.get('title', '')).strip() or Path(str(item.get('file_path', ''))).stem
    artist = str(item.get('artist', '')).strip()
    return f'{title}\n{artist}' if artist else title


def load_pixmap_from_data_url(data_url: str):
    if QPixmap is None or not data_url or not data_url.startswith('data:image'):
        return None
    try:
        _, encoded = data_url.split(',', 1)
        payload = base64.b64decode(encoded)
    except (ValueError, TypeError, binascii.Error):
        return None
    pixmap = QPixmap()
    if not pixmap.loadFromData(payload):
        return None
    return pixmap


def format_drop_card_text(path_text: str, empty_text: str) -> str:
    cleaned = path_text.strip()
    if not cleaned:
        return empty_text
    return Path(cleaned).name


def collect_mp4_inputs(paths: list[str]) -> list[Path]:
    unique: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file() and path.suffix.lower() == '.mp4':
            unique[path] = None
        elif path.is_dir():
            for item in sorted(path.rglob('*.mp4')):
                if item.is_file():
                    unique[item.resolve()] = None
    return sorted(unique.keys())


def format_mp4_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 .mp4 文件或文件夹'
    names = [p.stem for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 个视频'
    return f'已添加 {len(files)} 个视频\n\n{summary}'


def validate_mp4_form(files: list[Path], output_dir: str) -> list[str]:
    errors: list[str] = []
    if not files:
        errors.append('请先添加要转换的 .mp4 文件')
    if not output_dir.strip():
        errors.append('请选择输出目录')
    return errors


def validate_zipandpng_form(payload_path: str, cover_png_path: str, output_dir: str, output_name: str) -> list[str]:
    errors: list[str] = []
    if not payload_path:
        errors.append('请选择要伪装的文件')
    elif not Path(payload_path).exists():
        errors.append('要伪装的文件不存在')
    if not cover_png_path:
        errors.append('请选择PNG封面')
    elif not Path(cover_png_path).exists():
        errors.append('PNG封面不存在')
    if not output_dir:
        errors.append('请选择输出目录')
    elif not Path(output_dir).exists():
        errors.append('输出目录不存在')
    if not output_name.strip():
        errors.append('请输入输出文件名')
    return errors


def collect_image_convert_inputs(paths: list[str]) -> list[Path]:
    image_module = get_image_convert_module()
    return image_module.collect_image_inputs(paths)


def format_image_convert_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 JPG / PNG / WebP / HEIC 图片或文件夹'
    names = [p.stem for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 张图片'
    return f'已添加 {len(files)} 张图片\n\n{summary}'


def validate_image_convert_form(files: list[Path], output_dir: str, target_format: str, quality_text: str, target_size_text: str) -> list[str]:
    errors: list[str] = []
    if not files:
        errors.append('请先添加要转换的图片')
    if not output_dir.strip():
        errors.append('请选择输出目录')
    if not target_format.strip():
        errors.append('请选择输出格式')
    try:
        quality = int(quality_text.strip())
        if quality < 1 or quality > 100:
            errors.append('质量必须在 1 到 100 之间')
    except ValueError:
        errors.append('质量必须是 1 到 100 的整数')
    image_module = get_image_convert_module()
    try:
        image_module.validate_target_size_kb(target_size_text)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def collect_pdf_tool_inputs(paths: list[str]) -> list[Path]:
    pdf_module = get_pdf_tools_module()
    return pdf_module.collect_pdf_inputs(paths)


def collect_base64_image_inputs(paths: list[str]) -> list[Path]:
    base64_module = get_base64_module()
    unique: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file() and path.suffix.lower() in base64_module.SUPPORTED_IMAGE_SUFFIXES:
            unique[path] = None
        elif path.is_dir():
            for item in sorted(path.iterdir()):
                if item.is_file() and item.suffix.lower() in base64_module.SUPPORTED_IMAGE_SUFFIXES:
                    unique[item.resolve()] = None
    return sorted(unique.keys())


def format_base64_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 PNG / JPG / JPEG / WebP / GIF / BMP 图片'
    names = [p.name for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 张图片'
    return f'已添加 {len(files)} 张图片\n\n{summary}'


def validate_base64_form(mode: str, image_files: list[Path], base64_text: str, output_dir: str, output_name: str) -> list[str]:
    errors: list[str] = []
    if mode == 'encode':
        if not image_files:
            errors.append('请先添加要转换的图片')
        elif len(image_files) != 1:
            errors.append('图片转 Base64 仅支持单张图片')
        if not output_dir.strip():
            errors.append('请选择输出目录')
    else:
        if not base64_text.strip():
            errors.append('请输入 Base64 内容')
        if not output_dir.strip():
            errors.append('请选择输出目录')
    if not output_name.strip():
        errors.append('请输入输出文件名')
    return errors



def format_pdf_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 PDF 文件或文件夹'
    names = [p.stem for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 个PDF'
    return f'已添加 {len(files)} 个PDF\n\n{summary}'


def validate_pdf_form(action: str, files: list[Path], output_dir: str, page_ranges_text: str, image_format: str, dpi_text: str, text_export_format: str = '') -> list[str]:
    errors: list[str] = []
    pdf_module = get_pdf_tools_module()
    errors.extend(pdf_module.validate_pdf_action(action, files, page_ranges_text))
    if not output_dir.strip():
        errors.append('请选择输出目录')
    if action == 'images':
        if not image_format.strip():
            errors.append('请选择图片格式')
        try:
            dpi = int(dpi_text.strip())
            if dpi <= 0:
                errors.append('DPI 必须大于 0')
        except ValueError:
            errors.append('DPI 必须是整数')
    if action == 'text' and not text_export_format.strip():
        errors.append('请选择文本导出格式')
    return errors


def get_jpg_background_value(label: str) -> str:
    mapping = {
        '白色': 'white',
        '黑色': 'black',
        '透明': 'transparent',
    }
    return mapping.get(label, label)


def get_pdf_action_value(label: str) -> str:
    mapping = {
        '合并': 'merge',
        '拆分': 'split',
        '转图片': 'images',
        '提取文本': 'text',
    }
    return mapping.get(label, label)


def get_base64_mode_value(label: str) -> str:
    mapping = {
        '图片转Base64': 'encode',
        'Base64转图片': 'decode',
    }
    return mapping.get(label, label)


if QWidget is not None:
    def make_card(title: str, subtitle: str = ''):
        frame = QFrame()
        frame.setProperty('card', True)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        title_label = QLabel(title)
        title_label.setProperty('cardTitle', True)
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty('cardSub', True)
            layout.addWidget(sub)
        return frame, layout


    def make_transparent_row():
        row = QWidget()
        row.setAttribute(Qt.WA_StyledBackground, True)
        row.setStyleSheet('background: transparent;')
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        return row, layout


    class ComboItemDelegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            hint = super().sizeHint(option, index)
            return QSize(max(hint.width(), 120), 34)


    def style_combo_popup(combo: QComboBox, theme_name: str):
        if QListView is None:
            return
        popup_view = combo.view()
        if popup_view is None:
            return
        popup_view.setObjectName('comboPopupView')
        popup_view.setProperty('comboPopupTheme', theme_name)
        popup_view.viewport().setProperty('comboPopupTheme', theme_name)
        if theme_name == 'light':
            popup_style = (
                'QListView, QListView[comboPopupTheme="light"] {background-color: #eef1f5; color: #1f252d; '
                'border: 1px solid #d8dee6; border-radius: 0; outline: none; padding: 2px;} '
                'QListView::item {border-radius: 10px;} '
                'QListView::item:selected {background-color: #d4e4ff; color: #1f252d;} '
                'QWidget[comboPopupTheme="light"] {background-color: #eef1f5; color: #1f252d; border-radius: 0;}'
            )
        else:
            popup_style = (
                'QListView, QListView[comboPopupTheme="dark"] {background-color: #2a3038; color: #eef2f7; '
                'border: 1px solid #46505c; border-radius: 0; outline: none; padding: 2px;} '
                'QListView::item {border-radius: 10px;} '
                'QListView::item:selected {background-color: #6d94c8; color: #eef2f7;} '
                'QWidget[comboPopupTheme="dark"] {background-color: #2a3038; color: #eef2f7; border-radius: 0;}'
            )
        popup_view.setStyleSheet(popup_style)
        popup_view.setItemDelegate(ComboItemDelegate(popup_view))
        popup_view.setSpacing(2)
        popup_view.setFrameShape(QFrame.NoFrame)
        popup_view.viewport().setAutoFillBackground(False)


    def animate_fade(widget: QWidget, start: float = 0.0, end: float = 1.0, duration: int = 180):
        if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
            return None
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(start)
        animation = QPropertyAnimation(effect, b'opacity', widget)
        animation.setDuration(duration)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._fade_animation = animation
        return animation


    def fade_out_and_close(widget: QWidget, duration: int = 160):
        if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
            widget.close()
            return None
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(1.0)
        animation = QPropertyAnimation(effect, b'opacity', widget)
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(widget.accept if hasattr(widget, 'accept') else widget.close)
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._fade_close_animation = animation
        return animation


    class ThemedMessageDialog(QDialog):
        def __init__(self, parent, title: str, lines: list[str], button_text: str = '完成'):
            super().__init__(parent)
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            self.setModal(True)
            self.setAttribute(Qt.WA_StyledBackground, False)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self._closed_with_fade = False
            theme_name = getattr(parent, 'current_theme', 'light') if parent is not None else 'light'
            if theme_name == 'dark':
                surface = '#232933'
                title_color = '#f4f7fb'
                text_color = '#d5dce6'
                button_bg = '#6f95c7'
                button_hover = '#7b9fd0'
                button_text_color = '#eef4fb'
                button_border = '#7ea4d3'
            else:
                surface = '#f7f9fc'
                title_color = '#243447'
                text_color = '#4e5968'
                button_bg = '#e4efff'
                button_hover = '#edf4ff'
                button_text_color = '#24415f'
                button_border = '#cfd9e8'
            self.setStyleSheet(
                f"QFrame[messageCard='true'] {{background-color: {surface}; border: none; border-radius: 0px;}}"
                f"QLabel[messageTitle='true'] {{color: {title_color}; font-size: 17px; font-weight: 600; background: transparent;}}"
                f"QLabel[messageLine='true'] {{color: {text_color}; font-size: 13px; font-weight: 500; background: transparent;}}"
                f"QPushButton[messageButton='true'] {{background-color: {button_bg}; color: {button_text_color}; border: 1px solid {button_border}; border-radius: 6px; padding: 8px 20px; min-width: 96px; font-weight: 600;}}"
                f"QPushButton[messageButton='true']:hover {{background-color: {button_hover};}}"
            )
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            card = QFrame()
            card.setProperty('messageCard', True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            card_layout.setSpacing(10)
            title_label = QLabel(title)
            title_label.setProperty('messageTitle', True)
            card_layout.addWidget(title_label)
            for line in lines:
                if not line:
                    continue
                label = QLabel(line)
                label.setProperty('messageLine', True)
                label.setWordWrap(True)
                card_layout.addWidget(label)
            button_row = QHBoxLayout()
            button_row.addStretch(1)
            confirm_button = QPushButton(button_text)
            confirm_button.setProperty('messageButton', True)
            confirm_button.clicked.connect(self.close_with_fade)
            button_row.addWidget(confirm_button)
            button_row.addStretch(1)
            card_layout.addSpacing(2)
            card_layout.addLayout(button_row)
            root.addWidget(card)
            self.resize(352, card.sizeHint().height())
            animate_fade(self, 0.0, 1.0, 180)

        def close_with_fade(self):
            if self._closed_with_fade:
                return
            self._closed_with_fade = True
            fade_out_and_close(self, 160)


    def show_themed_message(parent, title: str, lines: list[str], button_text: str = '完成'):
        dialog = ThemedMessageDialog(parent, title, lines, button_text)
        if QEventLoop is None or QTimer is None:
            dialog.exec()
            return
        loop = QEventLoop()
        dialog.finished.connect(loop.quit)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        loop.exec()


    def show_themed_warning(parent, title: str, message: str):
        lines = [line for line in message.splitlines() if line.strip()] or [message]
        show_themed_message(parent, title, lines, '完成')


    def show_themed_success(parent, title: str, lines: list[str]):
        show_themed_message(parent, title, lines, '完成')


    def show_themed_error(parent, title: str, message: str):
        lines = [line for line in message.splitlines() if line.strip()] or [message]
        show_themed_message(parent, title, lines, '完成')


    def animate_stack_switch(stack: QStackedWidget, index: int):
        current_index = stack.currentIndex()
        if index < 0 or index == current_index:
            return
        stack.setCurrentIndex(index)
        page = stack.currentWidget()
        if page is None:
            return
        if QPropertyAnimation is None:
            return
        end_pos = page.pos()
        offset = 100 if index > current_index else -100
        start_pos = QPoint(end_pos.x(), end_pos.y() + offset)
        page.move(start_pos)
        move = QPropertyAnimation(page, b'pos', page)
        move.setDuration(600)
        move.setStartValue(start_pos)
        move.setEndValue(end_pos)
        move.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade = animate_fade(page, 0.35, 1.0, 350)
        move.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        page._slide_animation = (move, fade)


    def pulse_widget(widget: QWidget, duration: int = 150):
        if QPropertyAnimation is None:
            return None
        original = widget.geometry()
        grown = original.adjusted(-2, -2, 2, 2)
        grow = QPropertyAnimation(widget, b'geometry', widget)
        grow.setDuration(duration)
        grow.setStartValue(original)
        grow.setEndValue(grown)
        grow.setEasingCurve(QEasingCurve.Type.OutCubic)
        shrink = QPropertyAnimation(widget, b'geometry', widget)
        shrink.setDuration(duration)
        shrink.setStartValue(grown)
        shrink.setEndValue(original)
        shrink.setEasingCurve(QEasingCurve.Type.OutCubic)
        group = QParallelAnimationGroup(widget)
        grow.finished.connect(shrink.start)
        group.addAnimation(grow)
        group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
        widget._pulse_animation = (group, shrink)
        return group


    class DropZoneCard(QFrame):
        def __init__(self, body_text: str, on_files_dropped=None):
            super().__init__()
            self.on_files_dropped = on_files_dropped
            self.empty_text = body_text
            self.setProperty('dropzone', True)
            self.setProperty('active', False)
            self.setAcceptDrops(True)
            self.setMinimumHeight(190)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(10)
            self.preview_label = QLabel()
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setMinimumHeight(120)
            self.preview_label.hide()
            layout.addStretch(1)
            layout.addWidget(self.preview_label)
            self.body_label = QLabel(body_text)
            self.body_label.setProperty('dropBody', True)
            self.body_label.setAlignment(Qt.AlignCenter)
            self.body_label.setWordWrap(True)
            layout.addWidget(self.body_label)
            layout.addStretch(1)

        def set_body_text(self, text: str):
            self.body_label.setText(text)
            self.body_label.setVisible(bool(text))
            if text:
                self.preview_label.hide()
                self.preview_label.clear()

        def set_preview_image(self, path: str):
            if QPixmap is None:
                self.set_body_text(Path(path).name)
                return
            pixmap = QPixmap(path)
            if pixmap.isNull():
                self.set_body_text(Path(path).name)
                return
            scaled = pixmap.scaled(220, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
            self.preview_label.show()
            self.body_label.hide()

        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                self.setProperty('active', True)
                self.style().unpolish(self)
                self.style().polish(self)
                pulse_widget(self)
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragLeaveEvent(self, event):
            self.setProperty('active', False)
            self.style().unpolish(self)
            self.style().polish(self)
            event.accept()

        def dropEvent(self, event):
            self.setProperty('active', False)
            self.style().unpolish(self)
            self.style().polish(self)
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if self.on_files_dropped:
                self.on_files_dropped(paths)
            event.acceptProposedAction()


    class WindowControlButton(QPushButton):
        def __init__(self, control_type: str, tooltip: str, parent=None):
            super().__init__('', parent)
            self.control_type = control_type
            self.setToolTip(tooltip)
            self.setProperty('windowControl', True)
            self.setCursor(Qt.PointingHandCursor)
            self.setFixedSize(24, 24)
            self.setFlat(True)

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            color = '#f5f7fa' if self.window().current_theme == 'dark' else '#4d5866'
            pen = QPen(color)
            pen.setWidthF(1.8)
            painter.setPen(pen)
            if self.control_type == 'min':
                painter.drawLine(6, 12, 18, 12)
            elif self.control_type == 'max':
                painter.drawRect(6, 6, 12, 12)
            elif self.control_type == 'restore':
                painter.drawRect(8, 6, 8, 8)
                painter.drawLine(10, 6, 18, 6)
                painter.drawLine(18, 6, 18, 14)
                painter.drawLine(10, 8, 18, 8)
                painter.drawLine(6, 10, 14, 10)
                painter.drawLine(6, 10, 6, 18)
                painter.drawLine(6, 18, 14, 18)
            else:
                painter.drawLine(7, 7, 17, 17)
                painter.drawLine(17, 7, 7, 17)
            painter.end()


    class DragTitleBar(QFrame):
        def __init__(self, window):
            super().__init__(window)
            self.window = window
            self.setProperty('dragBar', True)
            self.setFixedHeight(34)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 7, 20, 0)
            layout.setSpacing(8)
            self.title_label = QLabel('')
            self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            layout.addWidget(self.title_label, 1)
            self.window.window_controls_layout = QHBoxLayout()
            self.window.window_controls_layout.setContentsMargins(0, 0, 0, 0)
            self.window.window_controls_layout.setSpacing(10)
            self.window.min_button = WindowControlButton('min', '最小化', self)
            self.window.max_button = WindowControlButton('max', '最大化', self)
            self.window.close_button = WindowControlButton('close', '关闭', self)
            self.window.min_button.clicked.connect(self.window.showMinimized)
            self.window.max_button.clicked.connect(self.window.toggle_max_restore)
            self.window.close_button.clicked.connect(self.window.close)
            self.window.window_controls_layout.addWidget(self.window.min_button)
            self.window.window_controls_layout.addWidget(self.window.max_button)
            self.window.window_controls_layout.addWidget(self.window.close_button)
            layout.addLayout(self.window.window_controls_layout)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.window.start_window_drag(event.globalPosition().toPoint())
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            self.window.update_window_drag(event.globalPosition().toPoint())
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self.window.stop_window_drag()
            super().mouseReleaseEvent(event)

        def mouseDoubleClickEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.window.toggle_max_restore()
            super().mouseDoubleClickEvent(event)


    class MusicTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            self.file_items: list[dict[str, str]] = []
            root = QVBoxLayout(self)
            card, layout = make_card('NCM转换MP3')
            self.drop_zone = DropZoneCard('拖入 .ncm 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            self.song_list_hint = QLabel('已添加歌曲')
            self.song_list_hint.setProperty('cardSub', True)
            layout.addWidget(self.song_list_hint)
            self.song_list_scroll = QScrollArea()
            self.song_list_scroll.setWidgetResizable(True)
            self.song_list_scroll.setMinimumHeight(220)
            self.song_list_scroll.setFrameShape(QFrame.NoFrame)
            self.song_list_scroll.setStyleSheet('QScrollArea {border: none; background: transparent;}')
            self.song_list_container = QWidget()
            self.song_list_layout = QVBoxLayout(self.song_list_container)
            self.song_list_layout.setContentsMargins(0, 0, 0, 0)
            self.song_list_layout.setSpacing(10)
            self.song_list_scroll.setWidget(self.song_list_container)
            layout.addWidget(self.song_list_scroll)
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'music/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row_widget, action_row = make_transparent_row()
            self.overwrite_checkbox = QCheckBox('覆盖同名文件')
            action_row.addWidget(self.overwrite_checkbox)
            self.delete_source_checkbox = QCheckBox('删除原 NCM')
            action_row.addWidget(self.delete_source_checkbox)
            action_row.addStretch(1)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addWidget(action_row_widget)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)
            self.refresh_song_list()

        def add_paths(self, paths: list[str]):
            items = get_music_file_items(paths)
            existing = {p.resolve() for p in self.files}
            new_items: list[dict[str, str]] = []
            for item in items:
                file_path = Path(str(item.get('file_path', ''))).resolve()
                if file_path not in existing:
                    normalized = dict(item)
                    normalized['file_path'] = str(file_path)
                    self.files.append(file_path)
                    self.file_items.append(normalized)
                    existing.add(file_path)
                    new_items.append(normalized)
            self.drop_zone.set_body_text(format_music_drop_summary(self.files))
            self.refresh_song_list()
            if new_items:
                self.log.appendPlainText('\n'.join(str(item.get('display_name', '')) for item in new_items))
            else:
                self.log.appendPlainText('没有新增歌曲')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'music/output_dir', path)

        def refresh_song_list(self):
            while self.song_list_layout.count():
                item = self.song_list_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            if not self.file_items:
                empty = QLabel('暂时还没有歌曲喵，拖一点 .ncm 进来吧~')
                empty.setProperty('cardSub', True)
                empty.setAlignment(Qt.AlignCenter)
                empty.setMinimumHeight(80)
                self.song_list_layout.addWidget(empty)
                self.song_list_layout.addStretch(1)
                return
            for index, item in enumerate(self.file_items, start=1):
                self.song_list_layout.addWidget(self.build_song_item_widget(index, item))
            self.song_list_layout.addStretch(1)

        def build_song_item_widget(self, index: int, item: dict[str, str]):
            row = QFrame()
            row.setProperty('card', True)
            row.setStyleSheet('QFrame[card="true"] {border-radius: 18px; padding: 0px;}')
            layout = QHBoxLayout(row)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(12)
            cover_label = QLabel()
            cover_label.setFixedSize(56, 56)
            cover_label.setAlignment(Qt.AlignCenter)
            cover_label.setStyleSheet('border-radius: 12px; background-color: rgba(120, 146, 184, 0.18);')
            pixmap = load_pixmap_from_data_url(str(item.get('cover_data_url', '')))
            if pixmap is not None:
                cover_label.setPixmap(pixmap.scaled(56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            else:
                cover_label.setText('♪')
            layout.addWidget(cover_label)
            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(4)
            title_label = QLabel(str(item.get('title', '')) or Path(str(item.get('file_path', ''))).stem)
            title_label.setStyleSheet('font-size: 14px; font-weight: 700;')
            title_label.setWordWrap(True)
            text_col.addWidget(title_label)
            artist_text = str(item.get('artist', '')).strip() or Path(str(item.get('file_path', ''))).name
            artist_label = QLabel(artist_text)
            artist_label.setProperty('cardSub', True)
            artist_label.setWordWrap(True)
            text_col.addWidget(artist_label)
            layout.addLayout(text_col, 1)
            index_label = QLabel(f'{index:02d}')
            index_label.setStyleSheet('font-size: 12px; color: #9aa6b5; font-weight: 600;')
            layout.addWidget(index_label, 0, Qt.AlignRight | Qt.AlignVCenter)
            return row

        def convert_files(self):
            output_dir = self.output_edit.text().strip()
            if not output_dir:
                show_themed_warning(self, '提示', '请先选择输出目录')
                return
            if not self.files:
                show_themed_warning(self, '提示', '请先添加要转换的 .ncm 文件')
                return
            available, message = get_music_backend_status()
            if not available:
                show_themed_warning(self, '缺少依赖', message)
                self.log.appendPlainText(f'ERROR {message}')
                return
            save_setting(self.settings, 'music/output_dir', output_dir)
            self.log.appendPlainText(f'已保存输出目录: {output_dir}')
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            delete_source = self.delete_source_checkbox.isChecked()
            ncm_module = _load_ncm_module()
            success_count = 0
            deleted_count = 0
            try:
                for idx, (src, out) in enumerate(ncm_module.convert_many(self.files, Path(output_dir), self.overwrite_checkbox.isChecked()), start=1):
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    if delete_source and Path(out).exists():
                        try:
                            Path(src).unlink()
                            deleted_count += 1
                            self.log.appendPlainText(f'DELETED {src}')
                        except Exception as exc:
                            self.log.appendPlainText(f'DELETE FAILED {src}: {exc}')
                    self.progress.setValue(idx)
                fail_count = max(0, len(self.files) - success_count)
                lines = [
                    f'✅ 成功：{success_count}个',
                    f'❌ 失败：{fail_count}个',
                ]
                if deleted_count:
                    lines.append(f'🗑 删除：{deleted_count}个')
                self.files = []
                self.file_items = []
                self.drop_zone.set_body_text(format_music_drop_summary(self.files))
                self.refresh_song_list()
                summary = f'转换完成: 成功{success_count} 个文件'
                if delete_source:
                    summary += f'，删除NCM {deleted_count} 个'
                show_themed_success(self, '完成', lines)
                self.log.appendPlainText(summary)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '转换失败', str(exc))


    class Mp4ToMp3Tab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('MP4转MP3', '拖入 MP4 视频，输出 MP3 音频文件')
            self.drop_zone = DropZoneCard('拖入 .mp4 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'mp4mp3/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addLayout(action_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)

        def add_paths(self, paths: list[str]):
            files = collect_mp4_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            self.drop_zone.set_body_text(format_mp4_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.stem for p in new_files))
            else:
                self.log.appendPlainText('没有新增视频')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'mp4mp3/output_dir', path)

        def clear_form(self):
            self.files = []
            self.drop_zone.set_body_text(format_mp4_drop_summary(self.files))

        def convert_files(self):
            output_dir = self.output_edit.text().strip()
            errors = validate_mp4_form(self.files, output_dir)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            save_setting(self.settings, 'mp4mp3/output_dir', output_dir)
            self.log.appendPlainText(f'已保存输出目录: {output_dir}')
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            mp4_module = get_mp4_module()
            success_count = 0
            try:
                for idx, src in enumerate(self.files, start=1):
                    out = mp4_module.convert_mp4_to_mp3(src, Path(output_dir) / f'{src.stem}.mp3')
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    self.progress.setValue(idx)
                self.clear_form()
                summary = f'转换完成: 成功{success_count} 个视频'
                show_themed_success(self, '完成', [summary])
                self.log.appendPlainText(summary)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '转换失败', str(exc))


    class ZipAndPngTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            root = QVBoxLayout(self)
            card, layout = make_card('PNG伪装', '拖入任意文件与 PNG/JPG/GIF/WEBP 封面，输出伪装后的图片文件')
            self.payload_path = ''
            self.cover_path = ''
            self.payload_drop = DropZoneCard('拖入 zip / exe / pdf / mp4 等任意文件', self.handle_payload_drop)
            layout.addWidget(self.payload_drop)
            self.cover_drop = DropZoneCard('拖入 PNG / JPG / GIF / WEBP 封面', self.handle_cover_drop)
            layout.addWidget(self.cover_drop)
            layout.addWidget(QLabel('输出文件名'))
            self.output_name_edit = QLineEdit()
            self.output_name_edit.setPlaceholderText('例如：my_secret_file')
            layout.addWidget(self.output_name_edit)
            row = QHBoxLayout()
            self.output_dir_edit = QLineEdit(load_setting(settings, 'zipandpng/output_dir'))
            self.output_dir_edit.setPlaceholderText('选择或输入伪装 png 输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_dir_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.start_button = QPushButton('开始伪装')
            self.start_button.clicked.connect(self.run_disguise)
            action_row.addWidget(self.start_button)
            layout.addLayout(action_row)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)

        def handle_payload_drop(self, paths: list[str]):
            result = split_dropped_files(paths)
            if result['payload']:
                self.payload_path = result['payload']
                self.payload_drop.set_body_text(format_drop_card_text(self.payload_path, '拖入 zip / exe / pdf / mp4 等任意文件'))
                if not self.output_name_edit.text().strip():
                    self.output_name_edit.setText(Path(self.payload_path).stem)
            if result['cover_png'] and not self.cover_path:
                self.cover_path = result['cover_png']
                self.cover_drop.set_preview_image(self.cover_path)

        def handle_cover_drop(self, paths: list[str]):
            allowed = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
            for raw in paths:
                path = Path(raw)
                if path.suffix.lower() in allowed:
                    self.cover_path = str(path.resolve())
                    self.cover_drop.set_preview_image(self.cover_path)
                    break

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_dir_edit.text() or str(ROOT))
            if path:
                self.output_dir_edit.setText(path)
                save_setting(self.settings, 'zipandpng/output_dir', path)

        def clear_form(self):
            self.payload_path = ''
            self.cover_path = ''
            self.payload_drop.set_body_text('拖入 zip / exe / pdf / mp4 等任意文件')
            self.cover_drop.set_body_text('拖入 PNG / JPG / GIF / WEBP 封面')
            self.output_name_edit.clear()

        def run_disguise(self):
            errors = validate_zipandpng_form(
                self.payload_path,
                self.cover_path,
                self.output_dir_edit.text().strip(),
                self.output_name_edit.text().strip(),
            )
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            save_setting(self.settings, 'zipandpng/output_dir', self.output_dir_edit.text().strip())
            out_name = normalize_output_name(
                self.output_name_edit.text(),
                self.cover_path,
                self.payload_path,
            )
            out_path = Path(self.output_dir_edit.text().strip()) / out_name
            zip_module = _load_zip_module()
            zip_module.disguise_file(
                Path(self.cover_path),
                Path(self.payload_path),
                out_path,
            )
            self.log.appendPlainText(f'伪装完成: {out_path}')
            self.clear_form()


    class ImageConvertTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('图片格式互转', '拖入 JPG / PNG / WebP / HEIC 图片，支持批量转换与压缩')
            self.drop_zone = DropZoneCard('拖入 JPG / PNG / WebP / HEIC 图片或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            format_row = QHBoxLayout()
            format_row.addWidget(QLabel('输出格式'))
            self.format_combo = QComboBox()
            self.format_combo.addItems(['jpg', 'png', 'webp', 'heic'])
            self.format_combo.setMinimumWidth(132)
            format_row.addWidget(self.format_combo)
            format_row.addWidget(QLabel('质量'))
            self.quality_edit = QLineEdit('85')
            format_row.addWidget(self.quality_edit)
            format_row.addWidget(QLabel('目标大小(KB)'))
            self.target_size_edit = QLineEdit('')
            format_row.addWidget(self.target_size_edit)
            layout.addLayout(format_row)
            alpha_row_widget, alpha_row = make_transparent_row()
            self.preserve_alpha_checkbox = QCheckBox('保留透明通道')
            self.preserve_alpha_checkbox.setChecked(True)
            alpha_row.addWidget(self.preserve_alpha_checkbox)
            alpha_row.addWidget(QLabel('JPG底色'))
            self.jpg_background_combo = QComboBox()
            self.jpg_background_combo.addItems(['白色', '黑色', '透明'])
            self.jpg_background_combo.setMinimumWidth(154)
            style_combo_popup(self.jpg_background_combo, load_setting(settings, 'ui/theme', 'dark'))
            alpha_row.addWidget(self.jpg_background_combo)
            alpha_row.addStretch(1)
            layout.addWidget(alpha_row_widget)
            output_row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'imageconvert/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.output_edit)
            output_row.addWidget(choose_btn)
            layout.addLayout(output_row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addLayout(action_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)

        def add_paths(self, paths: list[str]):
            files = collect_image_convert_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            self.drop_zone.set_body_text(format_image_convert_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.name for p in new_files))
            else:
                self.log.appendPlainText('没有新增图片')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'imageconvert/output_dir', path)

        def clear_form(self):
            self.files = []
            self.drop_zone.set_body_text(format_image_convert_drop_summary(self.files))

        def convert_files(self):
            target_format = self.format_combo.currentText()
            output_dir = self.output_edit.text().strip()
            quality_text = self.quality_edit.text()
            target_size_text = self.target_size_edit.text()
            errors = validate_image_convert_form(self.files, output_dir, target_format, quality_text, target_size_text)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            image_module = get_image_convert_module()
            available, message = image_module.probe_imagemagick()
            if not available:
                show_themed_warning(self, '缺少依赖', message)
                self.log.appendPlainText(f'ERROR {message}')
                return
            save_setting(self.settings, 'imageconvert/output_dir', output_dir)
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            quality = int(quality_text.strip())
            target_size_kb = image_module.validate_target_size_kb(target_size_text)
            success_count = 0
            for idx, src in enumerate(self.files, start=1):
                try:
                    out = image_module.convert_image(
                        input_path=src,
                        output_dir=Path(output_dir),
                        target_format=target_format,
                        quality=quality,
                        preserve_alpha=self.preserve_alpha_checkbox.isChecked(),
                        jpg_background=get_jpg_background_value(self.jpg_background_combo.currentText()),
                        target_size_kb=target_size_kb,
                    )
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    self.progress.setValue(idx)
                except Exception as exc:
                    self.log.appendPlainText(f'ERROR {src}: {exc}')
                    show_themed_error(self, '转换失败', str(exc))
                    return
            self.clear_form()
            summary = f'转换完成: 成功{success_count} 张图片'
            self.log.appendPlainText(summary)
            show_themed_success(self, '完成', [summary])


    class PdfToolsTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('PDF工具', '支持合并、拆分、转图片、导出 TXT / DOCX')
            self.drop_zone = DropZoneCard('拖入 PDF 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            action_row = QHBoxLayout()
            action_row.addWidget(QLabel('操作'))
            self.action_combo = QComboBox()
            self.action_combo.addItems(['合并', '拆分', '转图片', '提取文本'])
            self.action_combo.setMinimumWidth(132)
            self.action_combo.currentTextChanged.connect(self.update_action_ui)
            action_row.addWidget(self.action_combo)
            action_row.addWidget(QLabel('页码范围'))
            self.page_ranges_edit = QLineEdit('')
            self.page_ranges_edit.setPlaceholderText('例如 1-3,5')
            action_row.addWidget(self.page_ranges_edit)
            action_row.addWidget(QLabel('图片格式'))
            self.image_format_combo = QComboBox()
            self.image_format_combo.addItems(['png', 'jpg', 'webp'])
            self.image_format_combo.setMinimumWidth(132)
            action_row.addWidget(self.image_format_combo)
            action_row.addWidget(QLabel('DPI'))
            self.dpi_edit = QLineEdit('150')
            action_row.addWidget(self.dpi_edit)
            layout.addLayout(action_row)
            text_row = QHBoxLayout()
            self.text_format_label = QLabel('文本格式')
            text_row.addWidget(self.text_format_label)
            self.text_format_combo = QComboBox()
            self.text_format_combo.addItems(['txt', 'docx'])
            text_row.addWidget(self.text_format_combo)
            self.ocr_checkbox = QCheckBox('文字层为空时启用 OCR')
            text_row.addWidget(self.ocr_checkbox)
            text_row.addStretch(1)
            layout.addLayout(text_row)
            output_row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'pdftools/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.output_edit)
            output_row.addWidget(choose_btn)
            layout.addLayout(output_row)
            button_row = QHBoxLayout()
            button_row.addStretch(1)
            self.run_button = QPushButton('开始处理')
            self.run_button.clicked.connect(self.run_action)
            button_row.addWidget(self.run_button)
            layout.addLayout(button_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)
            self.update_action_ui(self.action_combo.currentText())

        def add_paths(self, paths: list[str]):
            files = collect_pdf_tool_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            self.drop_zone.set_body_text(format_pdf_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.name for p in new_files))
            else:
                self.log.appendPlainText('没有新增 PDF')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'pdftools/output_dir', path)

        def clear_form(self):
            self.files = []
            self.drop_zone.set_body_text(format_pdf_drop_summary(self.files))

        def update_action_ui(self, action: str):
            action_value = get_pdf_action_value(action)
            is_split = action_value == 'split'
            is_images = action_value == 'images'
            is_text = action_value == 'text'
            self.page_ranges_edit.setEnabled(is_split)
            self.image_format_combo.setEnabled(is_images)
            self.dpi_edit.setEnabled(is_images)
            self.text_format_label.setVisible(is_text)
            self.text_format_combo.setVisible(is_text)
            self.ocr_checkbox.setVisible(is_text)

        def run_action(self):
            action = get_pdf_action_value(self.action_combo.currentText())
            output_dir = self.output_edit.text().strip()
            page_ranges_text = self.page_ranges_edit.text()
            image_format = self.image_format_combo.currentText()
            dpi_text = self.dpi_edit.text()
            text_export_format = self.text_format_combo.currentText()
            errors = validate_pdf_form(action, self.files, output_dir, page_ranges_text, image_format, dpi_text, text_export_format)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            pdf_module = get_pdf_tools_module()
            save_setting(self.settings, 'pdftools/output_dir', output_dir)
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            try:
                if action == 'merge':
                    out = pdf_module.merge_pdfs(self.files, Path(output_dir) / 'merged.pdf')
                    self.log.appendPlainText(f'OK merged -> {out}')
                elif action == 'split':
                    reader = pdf_module.PdfReader(str(self.files[0]))
                    page_indexes = pdf_module.parse_page_ranges(page_ranges_text, len(reader.pages))
                    outputs = pdf_module.split_pdf(self.files[0], Path(output_dir), page_indexes)
                    self.log.appendPlainText(f'OK split -> {len(outputs)} files')
                elif action == 'images':
                    outputs = pdf_module.pdf_to_images(self.files[0], Path(output_dir), image_format, int(dpi_text.strip()))
                    self.log.appendPlainText(f'OK images -> {len(outputs)} files')
                else:
                    out = pdf_module.export_pdf_text(
                        self.files[0],
                        Path(output_dir),
                        text_export_format,
                        ocr_fallback=self.ocr_checkbox.isChecked(),
                    )
                    self.log.appendPlainText(f'OK text -> {out}')
                self.progress.setValue(self.progress.maximum())
                self.clear_form()
                show_themed_success(self, '完成', ['PDF 处理完成'])
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '处理失败', str(exc))


    class Base64Tab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('图片Base64', '支持图片转 Base64 / Data URL，或把 Base64 还原为图片')
            self.drop_zone = DropZoneCard('拖入 PNG / JPG / JPEG / WebP / GIF / BMP 图片', self.add_paths)
            layout.addWidget(self.drop_zone)
            mode_row_widget, mode_row = make_transparent_row()
            mode_row.addWidget(QLabel('模式'))
            self.mode_combo = QComboBox()
            self.mode_combo.addItems(['图片转Base64', 'Base64转图片'])
            self.mode_combo.setMinimumWidth(144)
            style_combo_popup(self.mode_combo, load_setting(settings, 'ui/theme', 'dark'))
            self.mode_combo.currentTextChanged.connect(self.update_mode_ui)
            mode_row.addWidget(self.mode_combo)
            self.data_url_checkbox = QCheckBox('输出 Data URL')
            mode_row.addWidget(self.data_url_checkbox)
            mode_row.addStretch(1)
            layout.addWidget(mode_row_widget)
            layout.addWidget(QLabel('Base64 内容'))
            self.base64_edit = QPlainTextEdit()
            self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 data:image/...;base64,...')
            self.base64_edit.setMinimumHeight(150)
            layout.addWidget(self.base64_edit)
            name_row = QHBoxLayout()
            name_row.addWidget(QLabel('输出文件名'))
            self.output_name_edit = QLineEdit('output')
            name_row.addWidget(self.output_name_edit)
            layout.addLayout(name_row)
            output_row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'base64/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.output_edit)
            output_row.addWidget(choose_btn)
            layout.addLayout(output_row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.run_button = QPushButton('开始处理')
            self.run_button.clicked.connect(self.run_action)
            action_row.addWidget(self.run_button)
            layout.addLayout(action_row)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            layout.addWidget(self.log)
            root.addWidget(card)
            self.update_mode_ui(self.mode_combo.currentText())

        def add_paths(self, paths: list[str]):
            files = collect_base64_image_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            self.drop_zone.set_body_text(format_base64_drop_summary(self.files))
            if new_files:
                picked = new_files[0]
                if not self.output_name_edit.text().strip() or self.output_name_edit.text().strip() == 'output':
                    self.output_name_edit.setText(picked.stem)
                self.log.appendPlainText('\n'.join(p.name for p in new_files))
            else:
                self.log.appendPlainText('没有新增图片')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'base64/output_dir', path)

        def clear_form(self):
            self.files = []
            self.drop_zone.set_body_text(format_base64_drop_summary(self.files))
            if self.mode_combo.currentText() == '图片转Base64':
                self.base64_edit.clear()

        def update_mode_ui(self, label: str):
            mode = get_base64_mode_value(label)
            is_encode = mode == 'encode'
            self.drop_zone.setEnabled(is_encode)
            self.data_url_checkbox.setVisible(is_encode)
            self.base64_edit.setReadOnly(is_encode)
            if is_encode:
                self.base64_edit.setPlaceholderText('编码结果会显示在这里，可继续保存为 txt')
                self.run_button.setText('生成 Base64')
            else:
                self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 data:image/...;base64,...')
                self.run_button.setText('还原图片')

        def run_action(self):
            mode = get_base64_mode_value(self.mode_combo.currentText())
            base64_text = self.base64_edit.toPlainText()
            output_dir = self.output_edit.text().strip()
            output_name = self.output_name_edit.text().strip()
            errors = validate_base64_form(mode, self.files, base64_text, output_dir, output_name)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            base64_module = get_base64_module()
            save_setting(self.settings, 'base64/output_dir', output_dir)
            try:
                if mode == 'encode':
                    image_path = self.files[0]
                    encoded = base64_module.encode_image_to_base64(image_path)
                    if self.data_url_checkbox.isChecked():
                        encoded = base64_module.build_data_url(encoded, image_path.suffix)
                    self.base64_edit.setPlainText(encoded)
                    out = base64_module.save_base64_text(encoded, output_dir, output_name)
                    self.log.appendPlainText(f'OK base64 -> {out}')
                    self.clear_form()
                else:
                    out = base64_module.decode_base64_to_file(base64_text, output_dir, output_name)
                    self.log.appendPlainText(f'OK image -> {out}')
                show_themed_success(self, '完成', ['Base64 处理完成'])
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '处理失败', str(exc))


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


    class ToolboxWindow(QMainWindow):
        def __init__(self, settings, authenticated_username: str = ''):
            super().__init__()
            self.settings = settings
            self.authenticated_username = authenticated_username.strip() or load_setting(settings, 'auth/last_user', '')
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self._drag_offset = None
            self._normal_geometry = None
            self.relogin_requested = False
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setWindowTitle('格式转换工具')
            self.resize(1180, 820)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            if LOGO_PATH.exists() and QIcon is not None:
                self.setWindowIcon(QIcon(str(LOGO_PATH)))
            root = QWidget()
            root.setObjectName('windowSurface')
            root.setProperty('windowSurface', True)
            root_layout = QVBoxLayout(root)
            root_layout.setContentsMargins(10, 10, 10, 10)
            root_layout.setSpacing(0)
            self.content_surface = QWidget()
            self.content_surface.setProperty('contentSurface', True)
            content_layout = QVBoxLayout(self.content_surface)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            self.drag_bar = DragTitleBar(self)
            content_layout.addWidget(self.drag_bar)
            central = QWidget()
            central.setAttribute(Qt.WA_TranslucentBackground, True)
            shell = QHBoxLayout(central)
            shell.setContentsMargins(18, 20, 18, 20)
            shell.setSpacing(20)
            side_panel = QFrame()
            side_panel.setProperty('navPanel', True)
            side_layout = QVBoxLayout(side_panel)
            side_layout.setContentsMargins(18, 22, 18, 18)
            side_layout.setSpacing(14)
            brand = QLabel('  格式转换工具')
            brand.setProperty('brandTitle', True)
            sub = QLabel('    by HhhYl')
            sub.setProperty('brandSub', True)
            side_layout.addWidget(brand)
            side_layout.addWidget(sub)
            self.theme_button = QPushButton('☀️' if self.current_theme == 'dark' else '🌙')
            self.theme_button.setProperty('themeToggle', True)
            self.theme_button.setMinimumSize(44, 44)
            self.theme_button.setMaximumSize(44, 44)
            self.theme_button.clicked.connect(self.toggle_theme)
            self.sidebar = QListWidget()
            self.sidebar.setProperty('navList', True)
            self.sidebar.setFixedWidth(196)
            self.sidebar.addItem('NCM转换MP3')
            self.sidebar.addItem('图片伪装')
            self.sidebar.addItem('MP4转MP3')
            self.sidebar.addItem('图片格式互转')
            self.sidebar.addItem('PDF工具')
            self.sidebar.addItem('图片Base64')
            self.sidebar.setCurrentRow(0)
            side_layout.addWidget(self.sidebar, 1)
            bottom_row = QHBoxLayout()
            bottom_row.setContentsMargins(0, 0, 0, 0)
            bottom_row.setSpacing(10)
            self.user_avatar_button = QPushButton()
            self.user_avatar_button.setProperty('themeToggle', True)
            self.user_avatar_button.setMinimumSize(38, 38)
            self.user_avatar_button.setMaximumSize(38, 38)
            self.user_avatar_button.setCursor(Qt.PointingHandCursor)
            self.user_avatar_button.clicked.connect(self.toggle_user_menu)
            bottom_row.addWidget(self.user_avatar_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            bottom_row.addWidget(self.theme_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            self.hint_button = QPushButton('❕')
            self.hint_button.setProperty('themeToggle', True)
            self.hint_button.setMinimumSize(38, 38)
            self.hint_button.setMaximumSize(38, 38)
            self.hint_button.setCursor(Qt.PointingHandCursor)
            self.hint_button.clicked.connect(self.toggle_help_popup)
            bottom_row.addWidget(self.hint_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            bottom_row.addStretch(1)
            side_layout.addLayout(bottom_row)
            shell.addWidget(side_panel)
            self.stack = QStackedWidget()
            self.music_tab = MusicTab(settings)
            self.zip_tab = ZipAndPngTab(settings)
            self.mp4_tab = Mp4ToMp3Tab(settings)
            self.image_convert_tab = ImageConvertTab(settings)
            self.pdf_tools_tab = PdfToolsTab(settings)
            self.base64_tab = Base64Tab(settings)
            self.stack.addWidget(self.music_tab)
            self.stack.addWidget(self.zip_tab)
            self.stack.addWidget(self.mp4_tab)
            self.stack.addWidget(self.image_convert_tab)
            self.stack.addWidget(self.pdf_tools_tab)
            self.stack.addWidget(self.base64_tab)
            shell.addWidget(self.stack, 1)
            self.sidebar.currentRowChanged.connect(self.switch_tool_page)
            content_layout.addWidget(central, 1)
            root_layout.addWidget(self.content_surface)
            self.setCentralWidget(root)
            self.central_surface = self.content_surface
            self._build_user_menu()
            self._build_help_popup()
            self.update_user_menu_ui()
            self.update_window_controls()

        def start_window_drag(self, global_pos):
            if self.isMaximized():
                return
            self._drag_offset = global_pos - self.frameGeometry().topLeft()

        def update_window_drag(self, global_pos):
            if self._drag_offset is None or self.isMaximized():
                return
            self.move(global_pos - self._drag_offset)

        def stop_window_drag(self):
            self._drag_offset = None

        def toggle_max_restore(self):
            if self.isMaximized():
                self.showNormal()
                if self._normal_geometry is not None:
                    self.setGeometry(self._normal_geometry)
            else:
                self._normal_geometry = self.geometry()
                self.showMaximized()
            self.update_window_controls()

        def update_window_controls(self):
            if not hasattr(self, 'max_button'):
                return
            is_max = self.isMaximized()
            self.max_button.control_type = 'restore' if is_max else 'max'
            self.max_button.setToolTip('还原' if is_max else '最大化')
            self.max_button.update()

        def _build_user_menu(self):
            self.user_menu = QFrame(self)
            self.user_menu.setVisible(False)
            self.user_menu.setFrameShape(QFrame.StyledPanel)
            self.user_menu.setStyleSheet('border-radius: 18px; padding: 0px;')
            layout = QVBoxLayout(self.user_menu)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(14)
            self.user_menu_name_label = QLabel('')
            self.user_menu_name_label.setProperty('brandSub', True)
            layout.addWidget(self.user_menu_name_label)
            self.logout_button = QPushButton('退出账号')
            self.logout_button.setMinimumHeight(40)
            self.logout_button.clicked.connect(self.logout)
            layout.addWidget(self.logout_button)
            self.user_menu.resize(236, 148)

        def _build_help_popup(self):
            state = build_help_popup_state(WEIXIN_IMAGE_PATH)
            self.help_overlay = QFrame(self)
            self.help_overlay.setGeometry(self.rect())
            self.help_overlay.setStyleSheet('background-color: rgba(0, 0, 0, 110); border-radius: 24px;')
            self.help_overlay.setVisible(False)
            self.help_popup = QFrame(self)
            self.help_popup.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
            self.help_popup.setProperty('contentSurface', True)
            self.help_popup.setAttribute(Qt.WA_StyledBackground, True)
            self.help_popup.setStyleSheet('border-radius: 18px; padding: 10px;')
            self.help_popup.setVisible(False)
            layout = QVBoxLayout(self.help_popup)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)
            self.help_image_label = QLabel()
            self.help_image_label.setAlignment(Qt.AlignCenter)
            pixmap = QPixmap(str(state['image_path']))
            scaled_pixmap = pixmap.scaled(
                state['max_width'],
                state['max_height'],
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.help_image_label.setPixmap(scaled_pixmap)
            self.help_image_label.setMinimumSize(scaled_pixmap.size())
            layout.addWidget(self.help_image_label)
            self.help_caption_label = QLabel(state['caption'])
            self.help_caption_label.setAlignment(Qt.AlignCenter)
            self.help_caption_label.setProperty('cardSub', True)
            self.help_caption_label.setStyleSheet(
                f'font-size: {state["caption_font_size"]}px; font-weight: {state["caption_font_weight"]};'
            )
            layout.addWidget(self.help_caption_label)
            self.help_popup.adjustSize()

        def update_user_menu_ui(self):
            state = build_user_menu_state(self.authenticated_username)
            self.user_avatar_button.setText(state['avatar_text'])
            self.user_avatar_button.setToolTip(state['username'])
            self.user_avatar_button.setProperty('themeToggle', state['avatar_uses_theme_toggle_style'])
            self.user_avatar_button.setMinimumSize(state['avatar_button_size'], state['avatar_button_size'])
            self.user_avatar_button.setMaximumSize(state['avatar_button_size'], state['avatar_button_size'])
            self.user_avatar_button.setStyleSheet(
                f'border-radius: {state["avatar_border_radius"]}px; font-weight: 700; padding: 0px;'
            )
            self.user_menu.layout().setContentsMargins(
                state['menu_padding'],
                state['menu_padding'],
                state['menu_padding'],
                state['menu_padding'],
            )
            self.user_menu.layout().setSpacing(state['menu_spacing'])
            self.user_menu.resize(state['menu_width'], state['menu_height'])
            self.user_menu_name_label.setText(f'当前用户：{state["username"]}')
            self.logout_button.setText(state['logout_text'])

        def toggle_user_menu(self):
            if self.user_menu.isVisible():
                self.user_menu.hide()
                return
            button_pos = self.user_avatar_button.mapTo(self, self.user_avatar_button.rect().topLeft())
            menu_x = button_pos.x() + self.user_avatar_button.width() - self.user_menu.width()
            menu_y = button_pos.y() - self.user_menu.height() - 8
            self.user_menu.move(max(12, menu_x), max(12, menu_y))
            self.user_menu.show()
            self.user_menu.raise_()

        def show_help_popup(self):
            self.help_overlay.setGeometry(self.rect())
            self.help_overlay.setVisible(True)
            self.help_overlay.raise_()
            self.help_popup.adjustSize()
            popup_x = max(12, (self.width() - self.help_popup.width()) // 2)
            popup_y = max(12, (self.height() - self.help_popup.height()) // 2)
            self.help_popup.move(popup_x, popup_y)
            self.help_popup.setVisible(True)
            self.help_popup.raise_()

        def hide_help_popup(self):
            self.help_popup.setVisible(False)
            self.help_overlay.setVisible(False)

        def toggle_help_popup(self):
            if self.help_popup.isVisible():
                self.hide_help_popup()
                return
            self.show_help_popup()

        def handle_global_mouse_press(self, global_pos):
            if not self.help_popup.isVisible():
                return
            local_pos = self.mapFromGlobal(global_pos)
            if self.rect().contains(local_pos):
                self.hide_help_popup()

        def mousePressEvent(self, event):
            if self.help_popup.isVisible() and event is not None:
                self.handle_global_mouse_press(event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos())
                event.accept()
                return
            super().mousePressEvent(event)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if hasattr(self, 'help_overlay'):
                self.help_overlay.setGeometry(self.rect())

        def logout(self):
            self.relogin_requested = True
            save_setting(self.settings, 'auth/auto_login', '0')
            self.user_menu.hide()
            self.close()

        def switch_tool_page(self, index: int):
            animate_stack_switch(self.stack, index)

        def changeEvent(self, event):
            super().changeEvent(event)
            self.update_window_controls()

        def toggle_theme(self):
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
            save_setting(self.settings, 'ui/theme', self.current_theme)
            self.theme_button.setText('☀️' if self.current_theme == 'dark' else '🌙')
            style_combo_popup(self.image_convert_tab.jpg_background_combo, self.current_theme)
            style_combo_popup(self.base64_tab.mode_combo, self.current_theme)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self.content_surface.setGraphicsEffect(None)
            self.update_window_controls()


    def build_main_window_for_test(settings_dir: str):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QApplication.instance() or QApplication([])
        settings = make_settings(settings_dir)
        ensure_default_admin_user(get_user_store_path(settings_dir))
        window = ToolboxWindow(settings, load_setting(settings, 'auth/last_user', 'admin'))
        return window, app


    def main():
        app = QApplication.instance() or QApplication(sys.argv)
        settings = make_settings(str(APP_DIR))
        ensure_default_admin_user(get_user_store_path(APP_DIR))
        while True:
            auth_dialog = AuthDialog(settings, get_user_store_path(APP_DIR))
            result = auth_dialog.result()
            if result != QDialog.Accepted:
                result = auth_dialog.exec()
            if result != QDialog.Accepted:
                return 0
            save_setting(settings, 'auth/last_user', auth_dialog.authenticated_username)
            window = ToolboxWindow(settings, auth_dialog.authenticated_username)
            window.show()
            app.exec()
            if not window.relogin_requested:
                return 0
else:
    def build_main_window_for_test(settings_dir: str):
        raise RuntimeError('PySide6 is not installed in this Python environment')

    def main():
        raise RuntimeError('PySide6 is not installed in this Python environment')


if __name__ == '__main__':
    raise SystemExit(main())
