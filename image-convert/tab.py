from __future__ import annotations

from pathlib import Path

from toolbox_app.tab_utils import format_drop_summary

_IMAGE_CONVERT_DIR = Path(__file__).resolve().parent


def _load_image_converter():
    from toolbox_app.loaders import load_module_once
    return load_module_once('image_convert_module', _IMAGE_CONVERT_DIR / 'converter.py')


def collect_image_convert_inputs(paths: list[str]) -> list[Path]:
    image_module = _load_image_converter()
    return image_module.collect_image_inputs(paths)


def format_image_convert_drop_summary(files: list[Path]) -> str:
    return format_drop_summary(files, 'JPG / PNG / WebP / HEIC 图片')


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
    image_module = _load_image_converter()
    try:
        image_module.validate_target_size_kb(target_size_text)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def get_jpg_background_value(label: str) -> str:
    mapping = {
        '白色': 'white',
        '黑色': 'black',
        '透明': 'transparent',
    }
    return mapping.get(label, label)


def build_image_convert_tab_class(deps: dict):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']
    QCheckBox = deps['QCheckBox']
    QComboBox = deps['QComboBox']
    QFileDialog = deps['QFileDialog']
    Qt = deps['Qt']
    DropZoneCard = deps['DropZoneCard']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    style_combo_popup = deps['style_combo_popup']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    get_image_convert_module = deps['get_image_convert_module']
    ROOT = deps['ROOT']
    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='imageconvert')


    class ImageConvertTab(BaseToolTab):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
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
            format_row.addWidget(QLabel('目标大小（KB）'))
            self.target_size_edit = QLineEdit('')
            format_row.addWidget(self.target_size_edit)
            layout.addLayout(format_row)
            alpha_row_widget, alpha_row = make_transparent_row()
            self.preserve_alpha_checkbox = QCheckBox('保留透明通道')
            self.preserve_alpha_checkbox.setChecked(True)
            alpha_row.addWidget(self.preserve_alpha_checkbox)
            alpha_row.addWidget(QLabel('JPG 背景色'))
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
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            action_row.addWidget(self.clear_files_button)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addLayout(action_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)

        def apply_theme(self, theme_name: str) -> None:
            self.current_theme = theme_name
            style_combo_popup(self.jpg_background_combo, theme_name if theme_name in {'dark', 'light'} else 'dark')

        def add_paths(self, paths: list[str]):
            files = collect_image_convert_inputs(paths)
            if not files:
                self.log.appendPlainText('没有新增图片')
                return
            picked = files[0].resolve()
            self.files = [picked]
            self.drop_zone.set_preview_image(
                str(picked),
                header_text='',
                body_text=picked.name,
            )
            self.log.appendPlainText(picked.name)

        def clear_form(self):
            self.clear_files(self.drop_zone, format_image_convert_drop_summary([]))

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

    return ImageConvertTab
