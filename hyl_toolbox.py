import importlib.util
import os
import sys
from configparser import ConfigParser
from pathlib import Path

try:
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtGui import QIcon, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QProgressBar,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
        QComboBox,
    )
except ModuleNotFoundError:
    QSettings = None
    QApplication = None
    Qt = None
    QIcon = QPixmap = None
    QCheckBox = QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QListWidget = None
    QMainWindow = QMessageBox = QPushButton = QPlainTextEdit = QProgressBar = QStackedWidget = None
    QVBoxLayout = QWidget = QComboBox = None

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
MUSIC_DIR = ROOT / 'music'
ZIP_DIR = ROOT / 'zipandpng'
MP4_DIR = ROOT / 'mp4-mp3'
IMAGE_CONVERT_DIR = ROOT / 'image-convert'
LOGO_PATH = ROOT / 'logo.png'
DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0b0f14;
    color: #e8ecf1;
    font-family: 'Segoe UI', 'Microsoft YaHei';
    font-size: 13px;
}
QListWidget {
    background-color: #0b0f14;
    border: 1px solid #1f2937;
    border-radius: 18px;
    color: #7f8ea3;
    padding: 12px;
}
QListWidget::item {
    padding: 14px 12px;
    border-radius: 12px;
    margin: 6px 0;
    color: #6f7f92;
}
QListWidget::item:selected {
    background-color: #161f2b;
    color: #f3f6fb;
}
QListWidget::item:focus,
QListWidget:focus,
QListWidget::item:selected:focus {
    outline: none;
    border: none;
}
QLineEdit, QPlainTextEdit {
    background-color: #0b0f14;
    border: 1px solid #243041;
    border-radius: 12px;
    padding: 10px 12px;
    color: #f3f6fb;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton[themeToggle='true'] {
    padding: 0;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3b82f6;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QProgressBar {
    border: 1px solid #243041;
    border-radius: 10px;
    background: #0b0f14;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #22c55e;
    border-radius: 10px;
}
QFrame[card='true'] {
    background-color: #0b0f14;
    border: 1px solid #1f2937;
    border-radius: 20px;
}
QFrame[panel='true'] {
    background-color: #0b0f14;
    border: 1px solid #1f2937;
    border-radius: 20px;
}
QFrame[dropzone='true'] {
    background-color: #0b0f14;
    border: 2px dashed #31445f;
    border-radius: 18px;
}
QFrame[dropzone='true'][active='true'] {
    border: 2px dashed #60a5fa;
    background-color: #182235;
}
QLabel[cardTitle='true'] {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}
QLabel[cardSub='true'] {
    color: #7f8ea3;
}
QLabel[brandTitle='true'] {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
}
QLabel[brandSub='true'] {
    color: #7f8ea3;
    font-size: 12px;
}
QLabel[dropBody='true'] {
    color: #6f7f92;
    font-size: 13px;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f7f3e8;
    color: #4f4638;
    font-family: 'Segoe UI', 'Microsoft YaHei';
    font-size: 13px;
}
QListWidget {
    background-color: #f7f3e8;
    border: 1px solid #e3d9bd;
    border-radius: 18px;
    color: #9c8d69;
    padding: 12px;
}
QListWidget::item {
    padding: 14px 12px;
    border-radius: 12px;
    margin: 6px 0;
    color: #9f9171;
}
QListWidget::item:selected {
    background-color: #fff7d6;
    color: #5d5033;
}
QListWidget::item:focus,
QListWidget:focus,
QListWidget::item:selected:focus {
    outline: none;
    border: none;
}
QLineEdit, QPlainTextEdit {
    background-color: #f7f3e8;
    border: 1px solid #e3d9bd;
    border-radius: 12px;
    padding: 10px 12px;
    color: #5d5033;
}
QPushButton {
    background-color: #f4dc8c;
    color: #5a4924;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton[themeToggle='true'] {
    padding: 0;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #f7e4a6;
}
QPushButton:pressed {
    background-color: #ead27e;
}
QProgressBar {
    border: 1px solid #e3d9bd;
    border-radius: 10px;
    background: #f7f3e8;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #f4dc8c;
    border-radius: 10px;
}
QFrame[card='true'] {
    background-color: #f7f3e8;
    border: 1px solid #e3d9bd;
    border-radius: 20px;
}
QFrame[panel='true'] {
    background-color: #f7f3e8;
    border: 1px solid #e3d9bd;
    border-radius: 20px;
}
QFrame[dropzone='true'] {
    background-color: #f7f3e8;
    border: 2px dashed #dbcda8;
    border-radius: 18px;
}
QFrame[dropzone='true'][active='true'] {
    border: 2px dashed #e5c96d;
    background-color: #fff7d6;
}
QLabel[cardTitle='true'] {
    font-size: 20px;
    font-weight: 700;
    color: #5a4a34;
}
QLabel[cardSub='true'] {
    color: #aa9b7c;
}
QLabel[brandTitle='true'] {
    font-size: 22px;
    font-weight: 700;
    color: #5a4a34;
}
QLabel[brandSub='true'] {
    color: #aa9b7c;
    font-size: 12px;
}
QLabel[dropBody='true'] {
    color: #aa9b7c;
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


if QWidget is not None:
    def make_card(title: str, subtitle: str = ''):
        frame = QFrame()
        frame.setProperty('card', True)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        title_label = QLabel(title)
        title_label.setProperty('cardTitle', True)
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty('cardSub', True)
            layout.addWidget(sub)
        return frame, layout


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
            layout.setContentsMargins(22, 22, 22, 22)
            layout.setSpacing(8)
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
            action_row = QHBoxLayout()
            self.overwrite_checkbox = QCheckBox('覆盖同名文件')
            action_row.addWidget(self.overwrite_checkbox)
            self.delete_source_checkbox = QCheckBox('删除原 NCM')
            action_row.addWidget(self.delete_source_checkbox)
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
                QMessageBox.warning(self, '提示', '请先选择输出目录')
                return
            if not self.files:
                QMessageBox.warning(self, '提示', '请先添加要转换的 .ncm 文件')
                return
            available, message = get_music_backend_status()
            if not available:
                QMessageBox.warning(self, '缺少依赖', message)
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
                self.files = []
                self.drop_zone.set_body_text(format_music_drop_summary(self.files))
                summary = f'转换完成: 成功{success_count} 个文件'
                if delete_source:
                    summary += f'，删除NCM {deleted_count} 个'
                QMessageBox.information(self, '完成', summary)
                self.log.appendPlainText(summary)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                QMessageBox.critical(self, '转换失败', str(exc))


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
                QMessageBox.warning(self, '提示', '\n'.join(errors))
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
                QMessageBox.information(self, '完成', summary)
                self.log.appendPlainText(summary)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                QMessageBox.critical(self, '转换失败', str(exc))


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
            choose_btn = QPushButton('选择输出目录')
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
                QMessageBox.warning(self, '提示', '\n'.join(errors))
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
            format_row.addWidget(self.format_combo)
            format_row.addWidget(QLabel('质量'))
            self.quality_edit = QLineEdit('85')
            format_row.addWidget(self.quality_edit)
            format_row.addWidget(QLabel('目标大小(KB)'))
            self.target_size_edit = QLineEdit('')
            format_row.addWidget(self.target_size_edit)
            layout.addLayout(format_row)

            alpha_row = QHBoxLayout()
            self.preserve_alpha_checkbox = QCheckBox('保留透明通道')
            self.preserve_alpha_checkbox.setChecked(True)
            alpha_row.addWidget(self.preserve_alpha_checkbox)
            alpha_row.addWidget(QLabel('JPG底色'))
            self.jpg_background_combo = QComboBox()
            self.jpg_background_combo.addItems(['white', 'black', 'transparent'])
            alpha_row.addWidget(self.jpg_background_combo)
            alpha_row.addStretch(1)
            layout.addLayout(alpha_row)

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
                QMessageBox.warning(self, '提示', '\n'.join(errors))
                return
            image_module = get_image_convert_module()
            available, message = image_module.probe_imagemagick()
            if not available:
                QMessageBox.warning(self, '缺少依赖', message)
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
                        jpg_background=self.jpg_background_combo.currentText(),
                        target_size_kb=target_size_kb,
                    )
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    self.progress.setValue(idx)
                except Exception as exc:
                    self.log.appendPlainText(f'ERROR {src}: {exc}')
                    QMessageBox.critical(self, '转换失败', str(exc))
                    return
            self.clear_form()
            summary = f'转换完成: 成功{success_count} 张图片'
            self.log.appendPlainText(summary)
            QMessageBox.information(self, '完成', summary)


    class ToolboxWindow(QMainWindow):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.setWindowTitle('格式转换工具')
            self.resize(1180, 820)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            if LOGO_PATH.exists() and QIcon is not None:
                self.setWindowIcon(QIcon(str(LOGO_PATH)))

            central = QWidget()
            shell = QHBoxLayout(central)
            shell.setContentsMargins(15, 18, 15, 18)
            shell.setSpacing(18)

            side_panel = QFrame()
            side_panel.setProperty('panel', True)
            side_layout = QVBoxLayout(side_panel)
            side_layout.setContentsMargins(0, 18, 0, 18)
            side_layout.setSpacing(12)
            brand = QLabel('   格式转换工具')
            brand.setProperty('brandTitle', True)
            sub = QLabel('       by HhhYl')
            sub.setProperty('brandSub', True)
            side_layout.addWidget(brand)
            side_layout.addWidget(sub)
            self.theme_button = QPushButton('🌙' if self.current_theme == 'dark' else '☀️')
            self.theme_button.setProperty('themeToggle', True)
            self.theme_button.setMinimumSize(44, 44)
            self.theme_button.setMaximumSize(44, 44)
            self.theme_button.clicked.connect(self.toggle_theme)
            self.sidebar = QListWidget()
            self.sidebar.setFixedWidth(180)
            self.sidebar.addItem('NCM转换MP3')
            self.sidebar.addItem('ZIP伪装PNG')
            self.sidebar.addItem('MP4转MP3')
            self.sidebar.addItem('图片格式互转')
            self.sidebar.setCurrentRow(0)
            side_layout.addWidget(self.sidebar, 1)
            side_layout.addWidget(self.theme_button, 0, Qt.AlignHCenter | Qt.AlignBottom)
            shell.addWidget(side_panel)

            self.stack = QStackedWidget()
            self.music_tab = MusicTab(settings)
            self.zip_tab = ZipAndPngTab(settings)
            self.mp4_tab = Mp4ToMp3Tab(settings)
            self.image_convert_tab = ImageConvertTab(settings)
            self.stack.addWidget(self.music_tab)
            self.stack.addWidget(self.zip_tab)
            self.stack.addWidget(self.mp4_tab)
            self.stack.addWidget(self.image_convert_tab)
            shell.addWidget(self.stack, 1)

            self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
            self.setCentralWidget(central)

        def toggle_theme(self):
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
            save_setting(self.settings, 'ui/theme', self.current_theme)
            self.theme_button.setText('🌙' if self.current_theme == 'dark' else '☀️')
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))


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
