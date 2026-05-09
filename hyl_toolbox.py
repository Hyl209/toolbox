import importlib.util
import os
import sys
from configparser import ConfigParser
from pathlib import Path

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
    QVBoxLayout = QWidget = QComboBox = QSizePolicy = QStyledItemDelegate = None

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
MUSIC_DIR = ROOT / 'music'
ZIP_DIR = ROOT / 'zipandpng'
MP4_DIR = ROOT / 'mp4-mp3'
IMAGE_CONVERT_DIR = ROOT / 'image-convert'
PDF_TOOLS_DIR = ROOT / 'pdf-tools'
BASE64_DIR = ROOT / 'base64'
LOGO_PATH = ROOT / 'logo.png'
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
    names = [p.stem for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 首歌曲'
    return f'已添加 {len(files)} 首歌曲\n\n{summary}'


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
                border = '#46505c'
                title_color = '#f4f7fb'
                text_color = '#d5dce6'
                button_bg = '#6f95c7'
                button_hover = '#7b9fd0'
                button_text_color = '#eef4fb'
                button_border = '#7ea4d3'
            else:
                surface = '#f7f9fc'
                border = '#d8e0ea'
                title_color = '#243447'
                text_color = '#4e5968'
                button_bg = '#e4efff'
                button_hover = '#edf4ff'
                button_text_color = '#24415f'
                button_border = '#cfd9e8'
            self.setStyleSheet(
                f"QFrame[messageCard='true'] {{background-color: {surface}; border: 1px solid {border}; border-radius: 10px;}}"
                f"QLabel[messageTitle='true'] {{color: {title_color}; font-size: 17px; font-weight: 600; background: transparent;}}"
                f"QLabel[messageLine='true'] {{color: {text_color}; font-size: 13px; font-weight: 500; background: transparent;}}"
                f"QPushButton[messageButton='true'] {{background-color: {button_bg}; color: {button_text_color}; border: 1px solid {button_border}; border-radius: 6px; padding: 8px 20px; min-width: 96px; font-weight: 600;}}"
                f"QPushButton[messageButton='true']:hover {{background-color: {button_hover};}}"
            )
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 10, 10, 10)
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
            self.resize(352, card.sizeHint().height() + 20)
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
            root = QVBoxLayout(self)
            card, layout = make_card('NCM转换MP3')
            self.drop_zone = DropZoneCard('拖入 .ncm 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
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

        def add_paths(self, paths: list[str]):
            files = collect_music_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            self.drop_zone.set_body_text(format_music_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.stem for p in new_files))
            else:
                self.log.appendPlainText('没有新增歌曲')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'music/output_dir', path)

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
                self.drop_zone.set_body_text(format_music_drop_summary(self.files))
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


    class ToolboxWindow(QMainWindow):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self._drag_offset = None
            self._normal_geometry = None
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
            sub = QLabel('    Clean local toolbox')
            sub.setProperty('brandSub', True)
            side_layout.addWidget(brand)
            side_layout.addWidget(sub)
            self.theme_button = QPushButton('🌙' if self.current_theme == 'dark' else '☀️')
            self.theme_button.setProperty('themeToggle', True)
            self.theme_button.setMinimumSize(44, 44)
            self.theme_button.setMaximumSize(44, 44)
            self.theme_button.clicked.connect(self.toggle_theme)
            self.sidebar = QListWidget()
            self.sidebar.setProperty('navList', True)
            self.sidebar.setFixedWidth(196)
            self.sidebar.addItem('NCM转换MP3')
            self.sidebar.addItem('ZIP伪装PNG')
            self.sidebar.addItem('MP4转MP3')
            self.sidebar.addItem('图片格式互转')
            self.sidebar.addItem('PDF工具')
            self.sidebar.addItem('图片Base64')
            self.sidebar.setCurrentRow(0)
            side_layout.addWidget(self.sidebar, 1)
            side_layout.addWidget(self.theme_button, 0, Qt.AlignHCenter | Qt.AlignBottom)
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

        def switch_tool_page(self, index: int):
            animate_stack_switch(self.stack, index)

        def changeEvent(self, event):
            super().changeEvent(event)
            self.update_window_controls()

        def toggle_theme(self):
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
            save_setting(self.settings, 'ui/theme', self.current_theme)
            self.theme_button.setText('🌙' if self.current_theme == 'dark' else '☀️')
            style_combo_popup(self.image_convert_tab.jpg_background_combo, self.current_theme)
            style_combo_popup(self.base64_tab.mode_combo, self.current_theme)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self.content_surface.setGraphicsEffect(None)
            self.update_window_controls()


    def build_main_window_for_test(settings_dir: str):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QApplication.instance() or QApplication([])
        settings = make_settings(settings_dir)
        window = ToolboxWindow(settings)
        return window, app


    def main():
        app = QApplication.instance() or QApplication(sys.argv)
        settings = make_settings(str(APP_DIR))
        window = ToolboxWindow(settings)
        window.show()
        return app.exec()
else:
    def build_main_window_for_test(settings_dir: str):
        raise RuntimeError('PySide6 is not installed in this Python environment')

    def main():
        raise RuntimeError('PySide6 is not installed in this Python environment')


if __name__ == '__main__':
    raise SystemExit(main())
