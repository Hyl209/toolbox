from __future__ import annotations

from pathlib import Path


def collect_base64_image_inputs(paths: list[str]) -> list[Path]:
    from toolbox_app.loaders import load_module_once
    _dir = Path(__file__).resolve().parent
    base64_module = load_module_once('base64_converter_module', _dir / 'converter.py')
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


def get_base64_mode_value(label: str) -> str:
    mapping = {
        '图片转Base64': 'encode',
        'Base64转图片': 'decode',
    }
    return mapping.get(label, label)


def build_base64_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
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
    get_base64_module = deps['get_base64_module']
    ROOT = deps['ROOT']

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
            layout.addWidget(QLabel('Base64 编码内容'))
            self.base64_edit = QPlainTextEdit()
            self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 Data URL（data:image/...;base64,...）')
            self.base64_edit.setMinimumHeight(150)
            self.base64_edit.setStyleSheet(build_global_scrollbar_style())
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
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            action_row.addWidget(self.clear_files_button)
            self.run_button = QPushButton('开始处理')
            self.run_button.clicked.connect(self.run_action)
            action_row.addWidget(self.run_button)
            layout.addLayout(action_row)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)
            self.update_mode_ui(self.mode_combo.currentText())

        def add_paths(self, paths: list[str]):
            files = collect_base64_image_inputs(paths)
            if not files:
                self.log.appendPlainText('没有新增图片')
                return
            picked = files[0].resolve()
            self.files = [picked]
            if not self.output_name_edit.text().strip() or self.output_name_edit.text().strip() == 'output':
                self.output_name_edit.setText(picked.stem)
            self.drop_zone.set_preview_image(
                str(picked),
                header_text='',
                body_text=picked.name,
            )
            self.log.appendPlainText(picked.name)

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'base64/output_dir', path)

        def clear_form(self):
            had_files = bool(self.files)
            self.files = []
            self.drop_zone.set_body_text(format_base64_drop_summary(self.files))
            if self.mode_combo.currentText() == '图片转Base64':
                self.base64_edit.clear()
            if had_files:
                self.log.appendPlainText('已清空待编码图片')

        def update_mode_ui(self, label: str):
            mode = get_base64_mode_value(label)
            is_encode = mode == 'encode'
            self.drop_zone.setEnabled(is_encode)
            self.data_url_checkbox.setVisible(is_encode)
            self.base64_edit.setReadOnly(is_encode)
            if is_encode:
                self.base64_edit.setPlaceholderText('编码结果会显示在这里，可继续保存为 TXT')
                self.run_button.setText('生成 Base64 编码')
            else:
                self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 Data URL（data:image/...;base64,...）')
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

    return Base64Tab
