import json
import os
import sys
import base64
import binascii
from configparser import ConfigParser
from pathlib import Path

from toolbox_app.dynamic_modules import DynamicModuleLoader
from toolbox_app.tool_tabs import build_external_tab_classes
from toolbox_app.auth_dialog import build_auth_dialog_class
from toolbox_app.settings_dialog import build_settings_dialog_class
from toolbox_app.window import build_toolbox_window_class
from toolbox_app.plugins.manager import get_plugin_manager


_WEIXIN_B64_FILE = Path(__file__).resolve().parent / "modules" / "ncm-converter" / "weixin_base64.txt"
WEIXIN_IMAGE_BASE64 = _WEIXIN_B64_FILE.read_text(encoding="utf-8").strip() if _WEIXIN_B64_FILE.exists() else "" 


def build_help_popup_state(image_path: Path | None):
    resolved = Path(image_path) if image_path else None
    image_bytes = b''
    if resolved and resolved.exists():
        image_bytes = resolved.read_bytes()
    elif WEIXIN_IMAGE_BASE64:
        image_bytes = base64.b64decode(WEIXIN_IMAGE_BASE64)
    return {
        'image_path': resolved if resolved and resolved.exists() else None,
        'image_bytes': image_bytes,
        'has_image': bool(image_bytes),
        'close_on_main_click': True,
        'frameless': True,
        'max_width': 420,
        'max_height': 560,
        'caption': '感谢打赏' if image_bytes else '赞赏图片缺失，请联系开发者补充 weixin.png',
        'caption_font_size': 18,
        'caption_font_weight': 700,
    }

try:
    from PySide6.QtCore import QSettings, Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEventLoop, QTimer, QFileInfo, QObject, QThread, Signal, QUrl
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QFileIconProvider,
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
        QSpacerItem,
        QSpinBox,
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
    QFileInfo = None
    QObject = QThread = Signal = None
    QCheckBox = QFileDialog = QFileIconProvider = QFrame = QGraphicsOpacityEffect = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListView = None
    QMainWindow = QMessageBox = QPushButton = QPlainTextEdit = QProgressBar = QStackedWidget = QDialog = None
    QVBoxLayout = QWidget = QComboBox = QSizePolicy = QStyledItemDelegate = QScrollArea = QSpacerItem = QSpinBox = None
    QMediaPlayer = QAudioOutput = QUrl = None

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
SOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = SOURCE_DIR if getattr(sys, 'frozen', False) and (SOURCE_DIR / 'users.json').exists() else (Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else SOURCE_DIR)
PLUGINS_DIR = APP_DIR / 'plugins'
MUSIC_DIR = ROOT / 'modules' / 'ncm-converter'
ZIP_DIR = ROOT / 'modules' / 'file-disguise'
MP4_DIR = ROOT / 'modules' / 'audio-extractor'
IMAGE_CONVERT_DIR = ROOT / 'modules' / 'image-converter'
PDF_TOOLS_DIR = ROOT / 'modules' / 'pdf-tools'
VIDEO_DOWNLOADER_DIR = ROOT / 'modules' / 'video-downloader'
BASE64_DIR = ROOT / 'modules' / 'base64'
NAME_DIR = ROOT / 'modules' / 'batch-rename'
FILE_SORTER_DIR = ROOT / 'modules' / 'file-sorter'
SAME_DIR = ROOT / 'modules' / 'duplicate-finder'
LOGO_PATH = ROOT / 'logo.png'
SOUND_PATH = ROOT / 'sound.mp3'
WEIXIN_IMAGE_PATH = next((p for p in (MUSIC_DIR / 'weixin.png', ROOT / 'weixin.png') if p.exists()), None)
THEMES_DIR = ROOT / "themes"


def _load_theme_css(theme_name: str) -> str:
    """Load theme CSS from external .qss file."""
    qss_path = THEMES_DIR / f"{theme_name}.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


DARK_STYLESHEET = _load_theme_css("dark")
LIGHT_STYLESHEET = _load_theme_css("light")


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


_dynamic_modules = DynamicModuleLoader({
    'zip': ('zipandpng_module', ZIP_DIR / 'zipandpng.py'),
    'ncm': ('music_ncm_to_mp3', MUSIC_DIR / 'ncm_to_mp3.py'),
    'mp4': ('mp4_converter_module', MP4_DIR / 'converter.py'),
    'image_convert': ('image_convert_module', IMAGE_CONVERT_DIR / 'converter.py'),
    'pdf_tools': ('pdf_tools_module', PDF_TOOLS_DIR / 'converter.py'),
    'video_downloader': ('video_downloader_module', VIDEO_DOWNLOADER_DIR / 'converter.py'),
    'video_downloader_tab': ('video_downloader_tab_module', VIDEO_DOWNLOADER_DIR / 'tab.py'),
    'file_sorter': ('file_sorter_module', FILE_SORTER_DIR / 'converter.py'),
    'file_sorter_tab': ('file_sorter_tab_module', FILE_SORTER_DIR / 'tab.py'),
    'name': ('batch_rename_module', NAME_DIR / 'converter.py'),
    'name_tab': ('batch_rename_tab_module', NAME_DIR / 'tab.py'),
    'same': ('same_converter_module', SAME_DIR / 'converter.py'),
    'base64': ('base64_converter_module', BASE64_DIR / 'converter.py'),
    'music_tab': ('music_tab_module', MUSIC_DIR / 'tab.py'),
    'zip_tab': ('zip_tab_module', ZIP_DIR / 'tab.py'),
    'base64_tab': ('base64_tab_module', BASE64_DIR / 'tab.py'),
    'same_tab': ('same_tab_module', SAME_DIR / 'tab.py'),
    'mp4_tab': ('mp4_tab_module', MP4_DIR / 'tab.py'),
    'image_convert_tab': ('image_convert_tab_module', IMAGE_CONVERT_DIR / 'tab.py'),
    'pdf_tools_tab': ('pdf_tools_tab_module', PDF_TOOLS_DIR / 'tab.py'),
})


def _load_module(module_name: str, file_path: Path):
    return _dynamic_modules.load_path(module_name, file_path)


def _load_registered_module(key: str):
    return _dynamic_modules.load(key)


def _load_dynamic(key: str):
    """Shorthand to load a registered dynamic module by key."""
    return _load_registered_module(key)


# Convenience aliases so existing callers don't break.
_load_zip_module = lambda: _load_dynamic('zip')
_load_ncm_module = lambda: _load_dynamic('ncm')
_load_music_tab_module = lambda: _load_dynamic('music_tab')
_load_zip_tab_module = lambda: _load_dynamic('zip_tab')
_load_mp4_tab_module = lambda: _load_dynamic('mp4_tab')
_load_image_convert_tab_module = lambda: _load_dynamic('image_convert_tab')
_load_pdf_tools_tab_module = lambda: _load_dynamic('pdf_tools_tab')
_load_base64_tab_module = lambda: _load_dynamic('base64_tab')
_load_same_tab_module = lambda: _load_dynamic('same_tab')
_load_mp4_module = lambda: _load_dynamic('mp4')
_load_image_convert_module = lambda: _load_dynamic('image_convert')
_load_pdf_tools_module = lambda: _load_dynamic('pdf_tools')
_load_video_downloader_module = lambda: _load_dynamic('video_downloader')
_load_video_downloader_tab_module = lambda: _load_dynamic('video_downloader_tab')
_load_file_sorter_module = lambda: _load_dynamic('file_sorter')
_load_file_sorter_tab_module = lambda: _load_dynamic('file_sorter_tab')
_load_name_module = lambda: _load_dynamic('name')
_load_name_tab_module = lambda: _load_dynamic('name_tab')
_load_same_module = lambda: _load_dynamic('same')


def make_settings(base_dir: str):
    settings_path = Path(base_dir) / 'hyl_toolbox.ini'
    if QSettings is not None:
        return QSettings(str(settings_path), QSettings.Format.IniFormat)
    return IniSettings(str(settings_path))


from toolbox_app.utils import save_setting, load_setting


def get_user_store_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / 'users.json'


# Auth functions moved to toolbox_app/auth.py — proxy imports for backward compatibility
from toolbox_app.auth import (
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
    load_users,
    save_users,
    hash_password,
    verify_password,
    find_user,
    validate_password_policy,
    ensure_default_admin_user,
    register_user,
    verify_user_credentials,
    validate_auth_form,
    build_auth_state,
    normalize_auth_preferences,
    encode_saved_password,
    decode_saved_password,
    save_auth_preferences,
    load_auth_preferences,
    should_auto_login,
    clear_auth_fields,
    prepare_auth_mode_fields,
    build_user_menu_state,
    update_user_password,
)



from toolbox_app.tool_registry import TOOL_DEFINITIONS, get_tool_definitions  # noqa: F401


# TODO: Proxy functions below exist solely for backward compatibility.
# Callers (tests, tab builders) should import directly from sub-modules
# (e.g. music/tab.py, mp4/tab.py) so these can be removed.
# Two functions are NOT simple proxies and need manual migration:
#   - format_video_download_task_summary: calls TWO modules
#   - validate_video_downloader_form: passes extra kwargs

def collect_music_inputs(paths): return _load_music_tab_module().collect_music_inputs(paths)


def get_music_backend_status(): return _load_music_tab_module().get_music_backend_status()


def get_zip_module():
    return _load_zip_module()


def get_mp4_module():
    return _load_mp4_module()


def get_image_convert_module():
    return _load_image_convert_module()


def get_pdf_tools_module():
    return _load_pdf_tools_module()


def get_video_downloader_module():
    return _load_video_downloader_module()


def get_file_sorter_module():
    return _load_file_sorter_module()


def get_name_module():
    return _load_name_module()


def get_same_module():
    return _load_same_module()


def get_base64_module():
    return _load_registered_module('base64')


def choose_output_suffix(cover_path): return _load_zip_tab_module().choose_output_suffix(cover_path)


def normalize_output_name(name, cover_path='', payload_path=''): return _load_zip_tab_module().normalize_output_name(name, cover_path, payload_path)


def split_dropped_files(paths): return _load_zip_tab_module().split_dropped_files(paths)


def format_music_drop_summary(files): return _load_music_tab_module().format_music_drop_summary(files)


def get_music_file_items(paths): return _load_music_tab_module().get_music_file_items(paths)


def build_music_item_text(item): return _load_music_tab_module().build_music_item_text(item)


def format_music_log_added(items): return _load_music_tab_module().format_music_log_added(items)


def format_music_log_output_dir(output_dir): return _load_music_tab_module().format_music_log_output_dir(output_dir)


def format_music_log_success(src, out): return _load_music_tab_module().format_music_log_success(src, out)


def format_music_log_delete(src): return _load_music_tab_module().format_music_log_delete(src)


def format_music_log_delete_failed(src, exc): return _load_music_tab_module().format_music_log_delete_failed(src, exc)


def format_music_log_missing_dependency(message): return _load_music_tab_module().format_music_log_missing_dependency(message)


def format_music_log_summary(success_count, fail_count, deleted_count): return _load_music_tab_module().format_music_log_summary(success_count, fail_count, deleted_count)


def format_music_log_error(exc): return _load_music_tab_module().format_music_log_error(exc)


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


def collect_mp4_inputs(paths): return _load_mp4_tab_module().collect_mp4_inputs(paths)


def format_mp4_drop_summary(files): return _load_mp4_tab_module().format_mp4_drop_summary(files)


def validate_mp4_form(files, output_dir): return _load_mp4_tab_module().validate_mp4_form(files, output_dir)


def validate_zipandpng_form(payload_path, cover_png_path, output_dir, output_name): return _load_zip_tab_module().validate_zipandpng_form(payload_path, cover_png_path, output_dir, output_name)


def collect_image_convert_inputs(paths): return _load_image_convert_tab_module().collect_image_convert_inputs(paths)


def format_image_convert_drop_summary(files): return _load_image_convert_tab_module().format_image_convert_drop_summary(files)


def validate_image_convert_form(files, output_dir, target_format, quality_text, target_size_text): return _load_image_convert_tab_module().validate_image_convert_form(files, output_dir, target_format, quality_text, target_size_text)


def collect_pdf_tool_inputs(paths): return _load_pdf_tools_tab_module().collect_pdf_tool_inputs(paths)


def collect_base64_image_inputs(paths: list[str]) -> list[Path]:
    return _load_base64_tab_module().collect_base64_image_inputs(paths)


def format_base64_drop_summary(files: list[Path]) -> str:
    return _load_base64_tab_module().format_base64_drop_summary(files)


def validate_base64_form(mode: str, image_files: list[Path], base64_text: str, output_dir: str, output_name: str) -> list[str]:
    return _load_base64_tab_module().validate_base64_form(mode, image_files, base64_text, output_dir, output_name)


def format_video_download_task_summary(task_text: str) -> str:
    module = _load_video_downloader_tab_module()
    downloader = get_video_downloader_module()
    return module.format_video_task_summary(downloader.parse_task_lines(task_text))


def validate_video_downloader_form(
    task_text: str,
    output_dir: str,
    api_id: str,
    api_hash: str,
    phone: str,
    recent_limit: str,
    download_all_messages: bool = False,
    date_from: str = '',
    date_to: str = '',
    telegram_include_videos: bool = True,
    telegram_include_photos: bool = False,
    web_candidate_index: str = '',
    web_download_all_candidates: bool = False,
) -> list[str]:
    module = _load_video_downloader_tab_module()
    return module.validate_video_downloader_form(
        task_text,
        output_dir,
        api_id,
        api_hash,
        phone,
        recent_limit,
        download_all_messages,
        date_from,
        date_to,
        telegram_include_videos,
        telegram_include_photos,
        web_candidate_index,
        web_download_all_candidates,
        get_video_downloader_module=get_video_downloader_module,
    )


def format_file_sorter_summary(summary: dict[str, object]) -> str:
    return _load_file_sorter_tab_module().format_file_sorter_summary(summary)


def validate_file_sorter_form(folder_path: str) -> list[str]:
    return _load_file_sorter_tab_module().validate_file_sorter_form(folder_path)


def format_batch_rename_summary(summary: dict[str, object]) -> str:
    module = _load_name_tab_module()
    return module.format_batch_rename_summary(summary)


def validate_batch_rename_form(folder_path: str, prefix: str) -> list[str]:
    module = _load_name_tab_module()
    return module.validate_batch_rename_form(folder_path, prefix)


def format_same_summary(result: dict[str, object]) -> str:
    return _load_same_tab_module().format_same_summary(result)


def validate_same_form(folder_path: str) -> list[str]:
    return _load_same_tab_module().validate_same_form(folder_path)



def format_pdf_drop_summary(files): return _load_pdf_tools_tab_module().format_pdf_drop_summary(files)


def validate_pdf_form(action, files, output_dir, page_ranges_text, image_format, dpi_text, text_export_format=''): return _load_pdf_tools_tab_module().validate_pdf_form(action, files, output_dir, page_ranges_text, image_format, dpi_text, text_export_format)


def get_jpg_background_value(label): return _load_image_convert_tab_module().get_jpg_background_value(label)


def get_pdf_action_value(label): return _load_pdf_tools_tab_module().get_pdf_action_value(label)


def get_base64_mode_value(label: str) -> str:
    return _load_base64_tab_module().get_base64_mode_value(label)


def build_global_scrollbar_style() -> str:
    return (
        'QScrollBar:vertical {background: transparent; width: 10px; margin: 6px 0 6px 0;} '
        'QScrollBar::handle:vertical {background: rgba(125, 147, 181, 0.62); min-height: 36px; border-radius: 5px;} '
        'QScrollBar::handle:vertical:hover {background: rgba(125, 147, 181, 0.82);} '
        'QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height: 0px; background: transparent; border: none;} '
        'QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: transparent;} '
        'QScrollBar:horizontal {background: transparent; height: 10px; margin: 0 6px 0 6px;} '
        'QScrollBar::handle:horizontal {background: rgba(125, 147, 181, 0.62); min-width: 36px; border-radius: 5px;} '
        'QScrollBar::handle:horizontal:hover {background: rgba(125, 147, 181, 0.82);} '
        'QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {width: 0px; background: transparent; border: none;} '
        'QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {background: transparent;}'
    )


def build_music_scroll_area_style() -> str:
    return (
        'QScrollArea {border: none; background: transparent;} '
        'QScrollArea > QWidget > QWidget {background: transparent;} '
        + build_global_scrollbar_style()
    )


if QWidget is not None:
    from toolbox_app.widgets import (
        make_card,
        make_transparent_row,
        ComboItemDelegate,
        style_combo_popup,
        animate_fade,
        fade_out_and_close,
        resolve_theme_name,
        ThemedMessageDialog,
        show_themed_message,
        show_themed_warning,
        show_themed_success,
        show_themed_error,
        animate_stack_switch,
        pulse_widget,
        DropZoneCard,
        WindowControlButton,
        DragTitleBar,
    )





    AuthDialog = build_auth_dialog_class({
        'QDialog': QDialog,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QCheckBox': QCheckBox,
        'QWidget': QWidget,
        'Qt': Qt,
        'DragTitleBar': DragTitleBar,
        'load_setting': load_setting,
        'get_theme_stylesheet': get_theme_stylesheet,
        'load_auth_preferences': load_auth_preferences,
        'decode_saved_password': decode_saved_password,
        'build_auth_state': build_auth_state,
        'should_auto_login': should_auto_login,
        'load_users': load_users,
        'prepare_auth_mode_fields': prepare_auth_mode_fields,
        'validate_auth_form': validate_auth_form,
        'register_user': register_user,
        'verify_user_credentials': verify_user_credentials,
        'normalize_auth_preferences': normalize_auth_preferences,
        'encode_saved_password': encode_saved_password,
        'save_auth_preferences': save_auth_preferences,
        'update_user_password': update_user_password,
    })

    SettingsDialog = build_settings_dialog_class({
        'QDialog': QDialog,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QCheckBox': QCheckBox,
        'QWidget': QWidget,
        'QFrame': QFrame,
        'QListWidget': QListWidget,
        'QStackedWidget': QStackedWidget,
        'QScrollArea': QScrollArea,
        'Qt': Qt,
        'DragTitleBar': DragTitleBar,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'get_theme_stylesheet': get_theme_stylesheet,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'TOOL_DEFINITIONS': TOOL_DEFINITIONS,
        'QTimer': QTimer,
    })

    _external_tab_classes = build_external_tab_classes(
        {
            'QWidget': QWidget,
            'QVBoxLayout': QVBoxLayout,
            'QHBoxLayout': QHBoxLayout,
            'QScrollArea': QScrollArea,
            'QLineEdit': QLineEdit,
            'QPushButton': QPushButton,
            'QLabel': QLabel,
            'QCheckBox': QCheckBox,
            'QPlainTextEdit': QPlainTextEdit,
            'QFileDialog': QFileDialog,
            'QApplication': QApplication,
            'QComboBox': QComboBox,
            'QProgressBar': QProgressBar,
            'QObject': QObject,
            'QThread': QThread,
            'Signal': Signal,
            'load_setting': load_setting,
            'save_setting': save_setting,
            'make_card': make_card,
            'make_transparent_row': make_transparent_row,
            'build_global_scrollbar_style': build_global_scrollbar_style,
            'show_themed_warning': show_themed_warning,
            'show_themed_error': show_themed_error,
            'show_themed_success': show_themed_success,
            'style_combo_popup': style_combo_popup,
            'get_file_sorter_module': get_file_sorter_module,
            'get_name_module': get_name_module,
            'get_video_downloader_module': get_video_downloader_module,
            '_load_file_sorter_tab_module': _load_file_sorter_tab_module,
            '_load_name_tab_module': _load_name_tab_module,
            '_load_video_downloader_tab_module': _load_video_downloader_tab_module,
            'ROOT': ROOT,
            'VIDEO_DOWNLOADER_DIR': VIDEO_DOWNLOADER_DIR,
        }
    )
    FileSorterTab = _external_tab_classes['FileSorterTab']
    BatchRenameTab = _external_tab_classes['BatchRenameTab']
    VideoDownloaderTab = _external_tab_classes['VideoDownloaderTab']
    MusicTab = _load_music_tab_module().build_music_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QScrollArea': QScrollArea,
        'QFrame': QFrame,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QFileDialog': QFileDialog,
        'QCheckBox': QCheckBox,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'make_transparent_row': make_transparent_row,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'build_music_scroll_area_style': build_music_scroll_area_style,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'load_pixmap_from_data_url': load_pixmap_from_data_url,
        'ROOT': ROOT,
    })
    ZipAndPngTab = _load_zip_tab_module().build_zipandpng_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'get_zip_module': get_zip_module,
        'ROOT': ROOT,
    })
    Mp4ToMp3Tab = _load_mp4_tab_module().build_mp4_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'ROOT': ROOT,
    })
    ImageConvertTab = _load_image_convert_tab_module().build_image_convert_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QCheckBox': QCheckBox,
        'QComboBox': QComboBox,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'make_transparent_row': make_transparent_row,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'style_combo_popup': style_combo_popup,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'get_image_convert_module': get_image_convert_module,
        'ROOT': ROOT,
    })
    PdfToolsTab = _load_pdf_tools_tab_module().build_pdf_tools_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QCheckBox': QCheckBox,
        'QComboBox': QComboBox,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'make_transparent_row': make_transparent_row,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'style_combo_popup': style_combo_popup,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'get_pdf_tools_module': get_pdf_tools_module,
        'ROOT': ROOT,
    })
    Base64Tab = _load_base64_tab_module().build_base64_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QCheckBox': QCheckBox,
        'QComboBox': QComboBox,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'make_transparent_row': make_transparent_row,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'style_combo_popup': style_combo_popup,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'get_base64_module': get_base64_module,
        'ROOT': ROOT,
    })
    SameTab = _load_same_tab_module().build_same_tab_class({
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QLineEdit': QLineEdit,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QPlainTextEdit': QPlainTextEdit,
        'QProgressBar': QProgressBar,
        'QCheckBox': QCheckBox,
        'QFileDialog': QFileDialog,
        'Qt': Qt,
        'QObject': QObject,
        'QThread': QThread,
        'Signal': Signal,
        'DropZoneCard': DropZoneCard,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'make_card': make_card,
        'make_transparent_row': make_transparent_row,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'show_themed_warning': show_themed_warning,
        'show_themed_error': show_themed_error,
        'show_themed_success': show_themed_success,
        'get_same_module': get_same_module,
        'ROOT': ROOT,
    })

    def _get_or_create_plugin_manager():
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        return get_plugin_manager(PLUGINS_DIR)

    ToolboxWindow = build_toolbox_window_class({
        'QMainWindow': QMainWindow,
        'QWidget': QWidget,
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QFrame': QFrame,
        'QLabel': QLabel,
        'QPushButton': QPushButton,
        'QListWidget': QListWidget,
        'QStackedWidget': QStackedWidget,
        'QPixmap': QPixmap,
        'Qt': Qt,
        'QIcon': QIcon,
        'DragTitleBar': DragTitleBar,
        'load_setting': load_setting,
        'save_setting': save_setting,
        'get_theme_stylesheet': get_theme_stylesheet,
        'build_global_scrollbar_style': build_global_scrollbar_style,
        'build_help_popup_state': build_help_popup_state,
        'build_user_menu_state': build_user_menu_state,
        'SettingsDialog': SettingsDialog,
        'style_combo_popup': style_combo_popup,
        'animate_stack_switch': animate_stack_switch,
        'LOGO_PATH': LOGO_PATH,
        'WEIXIN_IMAGE_PATH': WEIXIN_IMAGE_PATH,
        'MusicTab': MusicTab,
        'ZipAndPngTab': ZipAndPngTab,
        'Mp4ToMp3Tab': Mp4ToMp3Tab,
        'ImageConvertTab': ImageConvertTab,
        'PdfToolsTab': PdfToolsTab,
        'VideoDownloaderTab': VideoDownloaderTab,
        'BatchRenameTab': BatchRenameTab,
        'FileSorterTab': FileSorterTab,
        'SameTab': SameTab,
        'Base64Tab': Base64Tab,
        'plugin_manager': _get_or_create_plugin_manager(),
    })

    def build_main_window_for_test(settings_dir: str):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QApplication.instance() or QApplication([])
        settings = make_settings(settings_dir)
        ensure_default_admin_user(get_user_store_path(settings_dir))
        window = ToolboxWindow(settings, load_setting(settings, 'auth/last_user', 'admin'))
        window.show()
        app.processEvents()
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
