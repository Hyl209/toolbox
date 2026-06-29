from __future__ import annotations

from pathlib import Path

from toolbox_app.tab_utils import format_drop_summary


_IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}


def collect_base64_file_inputs(paths: list[str]) -> list[Path]:
    files: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        try:
            if path.is_file():
                files[path] = None
            elif path.is_dir():
                for item in sorted(path.iterdir()):
                    if item.is_file():
                        files[item.resolve()] = None
        except OSError:
            continue
    return sorted(files)


def collect_base64_image_inputs(paths: list[str]) -> list[Path]:
    return collect_base64_file_inputs(paths)


def format_base64_drop_summary(files: list[Path]) -> str:
    return format_drop_summary(files, '文件')


def validate_base64_form(mode: str, files: list[Path], base64_text: str, output_dir: str, output_name: str) -> list[str]:
    errors: list[str] = []
    if mode == 'encode':
        if not files:
            errors.append('请先添加要转换的文件')
        elif len(files) != 1:
            errors.append('文件转 Base64 仅支持单个文件')
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
        '文件转Base64': 'encode',
        'Base64转文件': 'decode',
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
    ROOT = deps['ROOT']
    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='base64')


    class Base64Tab(BaseToolTab):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('文件Base64', '支持任意文件转 Base64 / Data URL，或把 Base64 还原为文件')
            self.drop_zone = DropZoneCard('拖入任意文件', self.add_paths)
            layout.addWidget(self.drop_zone)
            mode_row_widget, mode_row = make_transparent_row()
            mode_row.addWidget(QLabel('模式'))
            self.mode_combo = QComboBox()
            self.mode_combo.addItems(['文件转Base64', 'Base64转文件'])
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
            self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 Data URL（data:...;base64,...）')
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

        def apply_theme(self, theme_name: str) -> None:
            self.current_theme = theme_name
            style_combo_popup(self.mode_combo, theme_name if theme_name in {'dark', 'light'} else 'dark')

        def add_paths(self, paths: list[str]):
            files = collect_base64_file_inputs(paths)
            if not files:
                self.log.appendPlainText('没有新增文件')
                return
            picked = files[0].resolve()
            self.files = [picked]
            if not self.output_name_edit.text().strip() or self.output_name_edit.text().strip() == 'output':
                self.output_name_edit.setText(picked.stem)
            if picked.suffix.lower() in _IMAGE_SUFFIXES:
                self.drop_zone.set_preview_image(str(picked), header_text='', body_text=picked.name)
            else:
                self.drop_zone.set_preview_file_icon(str(picked), header_text='', body_text=picked.name)
            self.log.appendPlainText(picked.name)

        def clear_form(self):
            self.clear_files(self.drop_zone, format_base64_drop_summary([]))
            if get_base64_mode_value(self.mode_combo.currentText()) == 'encode':
                self.base64_edit.clear()

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
                self.base64_edit.setPlaceholderText('可直接粘贴 Base64 或 Data URL（data:...;base64,...）')
                self.run_button.setText('还原文件')

        def run_action(self):
            mode = get_base64_mode_value(self.mode_combo.currentText())
            base64_text = self.base64_edit.toPlainText()
            output_dir = self.output_edit.text().strip()
            output_name = self.output_name_edit.text().strip()
            errors = validate_base64_form(mode, self.files, base64_text, output_dir, output_name)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            save_setting(self.settings, 'base64/output_dir', output_dir)
            from toolbox_app.services.base64_service import Base64Service
            service = Base64Service()

            def do_action():
                if mode == 'encode':
                    file_path = self.files[0]
                    encoded = service.encode(file_path, data_url=self.data_url_checkbox.isChecked())
                    self.base64_edit.setPlainText(encoded)
                    out = service.save_text(encoded, output_dir, output_name)
                    self.log.appendPlainText(f'OK base64 -> {out}')
                else:
                    out = service.decode(base64_text, output_dir, output_name)
                    self.log.appendPlainText(f'OK file -> {out}')
                return True

            result = self.run_action_with_error_handling('处理', do_action, 'Base64 处理完成', clear_on_success=False)
            if result is not None and mode == 'encode':
                self.clear_form()

    return Base64Tab
