from __future__ import annotations

from pathlib import Path

_PDF_TOOLS_DIR = Path(__file__).resolve().parent


def _load_pdf_converter():
    from toolbox_app.loaders import load_module_once
    return load_module_once('pdf_tools_module', _PDF_TOOLS_DIR / 'converter.py')


def collect_pdf_tool_inputs(paths: list[str]) -> list[Path]:
    pdf_module = _load_pdf_converter()
    return pdf_module.collect_pdf_inputs(paths)


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
    pdf_module = _load_pdf_converter()
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


def get_pdf_action_value(label: str) -> str:
    mapping = {
        '合并': 'merge',
        '拆分': 'split',
        '转图片': 'images',
        '提取文本': 'text',
    }
    return mapping.get(label, label)


def build_pdf_tools_tab_class(deps: dict):
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
    get_pdf_tools_module = deps['get_pdf_tools_module']
    ROOT = deps['ROOT']
    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='pdftools')


    class PdfToolsTab(BaseToolTab):
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
            style_combo_popup(self.action_combo, load_setting(settings, 'ui/theme', 'dark'))
            action_row.addWidget(QLabel('页码范围'))
            self.page_ranges_edit = QLineEdit('')
            self.page_ranges_edit.setPlaceholderText('例如 1-3,5')
            action_row.addWidget(self.page_ranges_edit)
            action_row.addWidget(QLabel('图片格式'))
            self.image_format_combo = QComboBox()
            self.image_format_combo.addItems(['png', 'jpg', 'webp'])
            self.image_format_combo.setMinimumWidth(132)
            action_row.addWidget(self.image_format_combo)
            style_combo_popup(self.image_format_combo, load_setting(settings, 'ui/theme', 'dark'))
            action_row.addWidget(QLabel('DPI'))
            self.dpi_edit = QLineEdit('150')
            action_row.addWidget(self.dpi_edit)
            layout.addLayout(action_row)
            text_row_widget, text_row = make_transparent_row()
            self.text_format_label = QLabel('文本格式')
            text_row.addWidget(self.text_format_label)
            self.text_format_combo = QComboBox()
            self.text_format_combo.addItems(['txt', 'docx'])
            text_row.addWidget(self.text_format_combo)
            style_combo_popup(self.text_format_combo, load_setting(settings, 'ui/theme', 'dark'))
            self.ocr_checkbox = QCheckBox('文字层为空时启用 OCR')
            text_row.addWidget(self.ocr_checkbox)
            text_row.addStretch(1)
            layout.addWidget(text_row_widget)
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
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            button_row.addWidget(self.clear_files_button)
            self.run_button = QPushButton('开始处理')
            self.run_button.clicked.connect(self.run_action)
            button_row.addWidget(self.run_button)
            layout.addLayout(button_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
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
            if self.files:
                self.drop_zone.set_preview_file_icon(
                    str(self.files[0]),
                    header_text=f'已添加 {len(self.files)} 个PDF',
                    body_text='\n'.join(p.stem for p in self.files[:3]) + (f'\n... 另有 {len(self.files) - 3} 个PDF' if len(self.files) > 3 else ''),
                )
            else:
                self.drop_zone.set_body_text(format_pdf_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.name for p in new_files))
            else:
                self.log.appendPlainText('没有新增 PDF')

        def clear_form(self):
            had_files = bool(self.files)
            self.files = []
            self.drop_zone.set_body_text(format_pdf_drop_summary(self.files))
            if had_files:
                self.log.appendPlainText('已清空待处理 PDF')

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

    return PdfToolsTab
