from __future__ import annotations

from pathlib import Path

from toolbox_app.tab_utils import format_drop_summary

_WORD_FORMATTER_DIR = Path(__file__).resolve().parent

STYLE_LABELS = {
    '标题1': 'heading1',
    '标题2': 'heading2',
    '标题3': 'heading3',
    '标题4': 'heading4',
    '正文': 'body',
    '表格': 'table',
}

STYLE_NAMES = {value: label for label, value in STYLE_LABELS.items()}

PAGE_LABELS = {
    'top_margin_cm': '上边距',
    'bottom_margin_cm': '下边距',
    'left_margin_cm': '左边距',
    'right_margin_cm': '右边距',
    'header_distance_cm': '页眉距',
    'footer_distance_cm': '页脚距',
}

OUTPUT_LABELS = {
    '另存副本': 'copy',
    '原地覆盖': 'overwrite',
}


def _load_word_converter():
    from toolbox_app.loaders import load_module_once
    return load_module_once('word_formatter_module', _WORD_FORMATTER_DIR / 'converter.py')


def collect_word_format_inputs(paths: list[str]) -> list[Path]:
    return _load_word_converter().collect_word_inputs(paths)


def format_word_format_drop_summary(files: list[Path]) -> str:
    return format_drop_summary(files, 'Word 文档')


def get_output_mode_value(label: str) -> str:
    return OUTPUT_LABELS.get(label, label)


def validate_word_format_form(files: list[Path], text: str, output_dir: str, output_mode: str, config: dict | None = None) -> list[str]:
    converter = _load_word_converter()
    errors = converter.validate_request(files, text, output_dir, output_mode)
    if config is not None:
        errors.extend(converter.validate_config(config))
    return errors


def build_word_formatter_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QScrollArea = deps['QScrollArea']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']
    QCheckBox = deps['QCheckBox']
    QComboBox = deps['QComboBox']
    QFileDialog = deps['QFileDialog']
    QMessageBox = deps.get('QMessageBox')
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
    get_word_formatter_module = deps['get_word_formatter_module']
    ROOT = deps['ROOT']

    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='wordformatter')

    class WordFormatterTab(BaseToolTab):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.files: list[Path] = []
            self.page_edits: dict[str, object] = {}
            self.config = self._load_config()

            root = QVBoxLayout(self)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(build_global_scrollbar_style())
            root.addWidget(scroll)
            host = QWidget()
            host.setStyleSheet('background: transparent;')
            scroll.setWidget(host)
            host_layout = QVBoxLayout(host)

            card, layout = make_card('Word排版统一', '统一页面设置、标题、正文与表格样式，支持拖拽 docx 或直接输入 Markdown 文本')
            self.drop_zone = DropZoneCard('拖入 Word 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)

            layout.addWidget(QLabel('直接文本输入（支持 # 到 #### 标题）'))
            self.text_edit = QPlainTextEdit()
            self.text_edit.setPlaceholderText('# 一级标题\n正文段落\n## 二级标题')
            self.text_edit.setMinimumHeight(118)
            self.text_edit.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.text_edit)

            output_row_widget, output_row = make_transparent_row()
            output_row.addWidget(QLabel('输出'))
            self.output_mode_combo = QComboBox()
            self.output_mode_combo.addItems(list(OUTPUT_LABELS.keys()))
            self.output_mode_combo.currentTextChanged.connect(self.update_output_ui)
            style_combo_popup(self.output_mode_combo, self.current_theme)
            output_row.addWidget(self.output_mode_combo)
            self.output_edit = QLineEdit(load_setting(settings, 'wordformatter/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            output_row.addWidget(self.output_edit, 1)
            self.choose_button = QPushButton('选择路径')
            self.choose_button.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.choose_button)
            layout.addWidget(output_row_widget)

            page_card, page_layout = make_card('页面设置', '')
            self._build_page_controls(page_layout)
            layout.addWidget(page_card)

            style_card, style_layout = make_card('样式设置', '')
            self._build_style_controls(style_layout)
            layout.addWidget(style_card)

            button_row = QHBoxLayout()
            button_row.addStretch(1)
            clear_button = QPushButton('清空')
            clear_button.clicked.connect(self.clear_form)
            button_row.addWidget(clear_button)
            self.run_button = QPushButton('开始排版')
            self.run_button.clicked.connect(self.run_action)
            button_row.addWidget(self.run_button)
            layout.addLayout(button_row)

            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(130)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)

            host_layout.addWidget(card)
            host_layout.addStretch(1)
            self.load_style_to_form(self.style_combo.currentText())
            self.update_output_ui(self.output_mode_combo.currentText())

        def _build_page_controls(self, layout):
            keys = list(PAGE_LABELS.keys())
            for start in range(0, len(keys), 3):
                row_widget, row = make_transparent_row()
                for key in keys[start:start + 3]:
                    row.addWidget(QLabel(f'{PAGE_LABELS[key]}(cm)'))
                    edit = QLineEdit(str(self.config['page'][key]))
                    edit.setMaximumWidth(84)
                    self.page_edits[key] = edit
                    row.addWidget(edit)
                row.addStretch(1)
                layout.addWidget(row_widget)

        def _build_style_controls(self, layout):
            target_row_widget, target_row = make_transparent_row()
            target_row.addWidget(QLabel('目标'))
            self.style_combo = QComboBox()
            self.style_combo.addItems(list(STYLE_LABELS.keys()))
            self.style_combo.currentTextChanged.connect(self.load_style_to_form)
            style_combo_popup(self.style_combo, self.current_theme)
            target_row.addWidget(self.style_combo)
            target_row.addStretch(1)
            layout.addWidget(target_row_widget)

            row1_widget, row1 = make_transparent_row()
            row1.addWidget(QLabel('字体'))
            self.font_edit = QLineEdit()
            row1.addWidget(self.font_edit, 1)
            row1.addWidget(QLabel('字号'))
            self.size_edit = QLineEdit()
            self.size_edit.setMaximumWidth(72)
            row1.addWidget(self.size_edit)
            self.bold_checkbox = QCheckBox('加粗')
            row1.addWidget(self.bold_checkbox)
            layout.addWidget(row1_widget)

            row2_widget, row2 = make_transparent_row()
            for label, attr in [('行距', 'line_spacing_edit'), ('段前(pt)', 'space_before_edit'), ('段后(pt)', 'space_after_edit'), ('首行缩进(cm)', 'first_indent_edit')]:
                row2.addWidget(QLabel(label))
                edit = QLineEdit()
                edit.setMaximumWidth(78)
                setattr(self, attr, edit)
                row2.addWidget(edit)
            row2.addStretch(1)
            layout.addWidget(row2_widget)

            save_row = QHBoxLayout()
            save_row.addStretch(1)
            save_button = QPushButton('保存当前样式')
            save_button.clicked.connect(self.save_current_style)
            save_row.addWidget(save_button)
            layout.addLayout(save_row)

        def _load_config(self):
            converter = get_word_formatter_module()
            config = converter.get_default_config()
            for key in config['page']:
                saved = load_setting(self.settings, f'wordformatter/page/{key}', '')
                if str(saved).strip():
                    try:
                        config['page'][key] = float(saved)
                    except ValueError:
                        pass
            for style_key, style in config['styles'].items():
                for field in style:
                    saved = load_setting(self.settings, f'wordformatter/styles/{style_key}/{field}', '')
                    if str(saved).strip():
                        try:
                            style[field] = saved if field == 'font' else self._coerce_style_value(field, saved)
                        except ValueError:
                            pass
            return config

        def _coerce_style_value(self, field: str, value: object):
            if field == 'bold':
                return str(value).lower() in {'1', 'true', 'yes'}
            return float(value)

        def _collect_config_from_form(self):
            config = get_word_formatter_module().get_default_config()
            for key, edit in self.page_edits.items():
                config['page'][key] = edit.text().strip()
            config['styles'] = self.config['styles']
            key = STYLE_LABELS.get(self.style_combo.currentText(), 'heading1')
            self.config['styles'][key] = self._read_current_style()
            return config

        def apply_theme(self, theme_name: str) -> None:
            self.current_theme = theme_name
            safe = theme_name if theme_name in {'dark', 'light'} else 'dark'
            style_combo_popup(self.output_mode_combo, safe)
            style_combo_popup(self.style_combo, safe)

        def add_paths(self, paths: list[str]):
            files = collect_word_format_inputs(paths)
            self.add_files_with_dedup(files, self.drop_zone)

        def clear_form(self):
            self.clear_files(self.drop_zone, format_word_format_drop_summary([]))
            self.text_edit.clear()

        def load_style_to_form(self, label: str):
            key = STYLE_LABELS.get(label, 'heading1')
            style = self.config['styles'][key]
            self.font_edit.setText(str(style['font']))
            self.size_edit.setText(str(style['size_pt']))
            self.bold_checkbox.setChecked(bool(style['bold']))
            self.line_spacing_edit.setText(str(style['line_spacing']))
            self.space_before_edit.setText(str(style['space_before_pt']))
            self.space_after_edit.setText(str(style['space_after_pt']))
            self.first_indent_edit.setText(str(style['first_line_indent_cm']))

        def save_current_style(self, show_message: bool = True):
            key = STYLE_LABELS.get(self.style_combo.currentText(), 'heading1')
            style = self._read_current_style()
            self.config['styles'][key] = style
            for field, value in style.items():
                save_setting(self.settings, f'wordformatter/styles/{key}/{field}', str(value))
            if show_message:
                self.log.appendPlainText(f'已保存 {STYLE_NAMES.get(key, key)} 样式')

        def _read_current_style(self) -> dict[str, object]:
            return {
                'font': self.font_edit.text().strip() or 'Microsoft YaHei',
                'size_pt': self.size_edit.text().strip(),
                'bold': self.bold_checkbox.isChecked(),
                'line_spacing': self.line_spacing_edit.text().strip(),
                'space_before_pt': self.space_before_edit.text().strip(),
                'space_after_pt': self.space_after_edit.text().strip(),
                'first_line_indent_cm': self.first_indent_edit.text().strip(),
            }

        def update_output_ui(self, label: str):
            is_copy = get_output_mode_value(label) == 'copy'
            self.output_edit.setEnabled(is_copy)
            self.choose_button.setEnabled(is_copy)

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'wordformatter/output_dir', path)

        def _confirm_overwrite(self) -> bool:
            if QMessageBox is None:
                show_themed_warning(self, '确认覆盖', '原地覆盖会改写原 Word 文件，请确认后再执行')
                return False
            result = QMessageBox.question(
                self,
                '确认覆盖',
                '原地覆盖会直接改写原 Word 文件，是否继续？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            return result == QMessageBox.Yes

        def run_action(self):
            output_mode = get_output_mode_value(self.output_mode_combo.currentText())
            output_dir = self.output_edit.text().strip()
            text = self.text_edit.toPlainText()
            config = self._collect_config_from_form()
            errors = validate_word_format_form(self.files, text, output_dir, output_mode, config)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            if output_mode == 'overwrite' and self.files and not self._confirm_overwrite():
                return
            self.save_current_style(show_message=False)
            for key, edit in self.page_edits.items():
                save_setting(self.settings, f'wordformatter/page/{key}', edit.text().strip())
            if output_mode == 'copy':
                save_setting(self.settings, 'wordformatter/output_dir', output_dir)
            self.progress.setMaximum(max(1, len(self.files) + (1 if text.strip() else 0)))
            self.progress.setValue(0)
            converter = get_word_formatter_module()

            def do_action():
                outputs = converter.format_batch(self.files, text, config, output_dir, output_mode)
                for index, out in enumerate(outputs, start=1):
                    self.log.appendPlainText(f'OK {out}')
                    self.progress.setValue(index)
                return outputs

            self.run_action_with_error_handling(
                'Word排版',
                do_action,
                'Word 排版完成',
                clear_on_success=False,
            )

    return WordFormatterTab
