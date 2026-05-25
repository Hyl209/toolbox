from __future__ import annotations

from pathlib import Path


SETTINGS_PREFIX = 'batchrename'
TITLE = '批量命名'
SUBTITLE = '按后缀 / 类型 / 全文件分组，批量改成统一前缀编号'
FOLDER_PLACEHOLDER = '选择需要批量命名的文件夹'
PREFIX_PLACEHOLDER = '输入命名前缀'
DEFAULT_PREFIX = '批量命名'
SUMMARY_EMPTY_TEXT = '请选择文件夹'
RUN_BUTTON_TEXT = '开始命名'
RUNNING_BUTTON_TEXT = '命名中...'
CHOOSE_BUTTON_TEXT = '选择路径'
TIP_TEXT = '只处理当前文件夹第一层文件，保留原后缀，编号格式固定为 前缀_001'

GROUP_MODE_LABELS = {
    '按后缀': 'suffix',
    '按类型': 'type',
    '全文件': 'all',
}
SORT_MODE_LABELS = {
    '按命名': 'name',
    '修改日期': 'mtime',
    '文件大小': 'size',
}
SORT_ORDER_LABELS = {
    '从小到大': 'asc',
    '从大到小': 'desc',
}


def get_group_mode_value(label: str) -> str:
    return GROUP_MODE_LABELS.get(label, 'suffix')


def get_sort_mode_value(label: str) -> str:
    return SORT_MODE_LABELS.get(label, 'name')


def get_sort_order_value(label: str) -> str:
    return SORT_ORDER_LABELS.get(label, 'asc')


def format_batch_rename_summary(summary: dict[str, object]) -> str:
    total_files = int(summary.get('total_files', 0) or 0)
    if total_files <= 0:
        return '当前目录第一层没有可命名文件'
    group_counts = summary.get('group_counts', {})
    lines = [
        f'当前目录第一层共 {total_files} 个文件',
        f'前缀: {summary.get("prefix", "")}',
    ]
    if isinstance(group_counts, dict) and group_counts:
        for group_key, count in group_counts.items():
            lines.append(f'{group_key}: {count}')
    plan = summary.get('plan', [])
    if isinstance(plan, list) and plan:
        preview = plan[:3]
        lines.append('预览:')
        for item in preview:
            lines.append(f'{item["source_name"]} -> {item["target_name"]}')
    return '\n'.join(lines)


def validate_batch_rename_form(folder_path: str, prefix: str) -> list[str]:
    errors: list[str] = []
    cleaned_path = folder_path.strip()
    if not cleaned_path:
        errors.append('请选择需要批量命名的文件夹')
        return errors
    path = Path(cleaned_path)
    if not path.exists():
        errors.append('选择的文件夹不存在')
    elif not path.is_dir():
        errors.append('选择的路径不是文件夹')
    cleaned_prefix = prefix.strip()
    if not cleaned_prefix:
        errors.append('请输入命名前缀')
    invalid_chars = '<>:"/\\|?*'
    if cleaned_prefix and any(char in invalid_chars for char in cleaned_prefix):
        errors.append('命名前缀不能包含 \\ / : * ? " < > |')
    if cleaned_prefix and cleaned_prefix.rstrip(' .') != cleaned_prefix:
        errors.append('命名前缀末尾不能是空格或点')
    return errors


def build_batch_rename_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QFileDialog = deps['QFileDialog']
    QApplication = deps['QApplication']
    QComboBox = deps['QComboBox']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    style_combo_popup = deps['style_combo_popup']
    get_name_module = deps['get_name_module']
    ROOT = deps['ROOT']

    class BatchRenameTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_summary: dict[str, object] | None = None
            self.is_running = False

            root = QVBoxLayout(self)
            card, layout = make_card(TITLE, SUBTITLE)

            path_row = QHBoxLayout()
            self.folder_edit = QLineEdit(load_setting(settings, f'{SETTINGS_PREFIX}/input_dir'))
            self.folder_edit.setPlaceholderText(FOLDER_PLACEHOLDER)
            self.folder_edit.editingFinished.connect(self.refresh_summary)
            self.choose_button = QPushButton(CHOOSE_BUTTON_TEXT)
            self.choose_button.clicked.connect(self.choose_folder)
            path_row.addWidget(self.folder_edit)
            path_row.addWidget(self.choose_button)
            layout.addLayout(path_row)

            prefix_row = QHBoxLayout()
            prefix_row.addWidget(QLabel('命名前缀'))
            self.prefix_edit = QLineEdit(load_setting(settings, f'{SETTINGS_PREFIX}/prefix', DEFAULT_PREFIX))
            self.prefix_edit.setPlaceholderText(PREFIX_PLACEHOLDER)
            self.prefix_edit.editingFinished.connect(self.handle_form_changed)
            prefix_row.addWidget(self.prefix_edit)
            layout.addLayout(prefix_row)

            option_row_widget, option_row = make_transparent_row()
            option_row.addWidget(QLabel('分组'))
            self.group_combo = QComboBox()
            self.group_combo.addItems(list(GROUP_MODE_LABELS.keys()))
            self.group_combo.setCurrentText(load_setting(settings, f'{SETTINGS_PREFIX}/group_mode', '按后缀'))
            self.group_combo.currentTextChanged.connect(self.handle_form_changed)
            style_combo_popup(self.group_combo, load_setting(settings, 'ui/theme', 'dark'))
            option_row.addWidget(self.group_combo)

            option_row.addWidget(QLabel('排序'))
            self.sort_combo = QComboBox()
            self.sort_combo.addItems(list(SORT_MODE_LABELS.keys()))
            self.sort_combo.setCurrentText(load_setting(settings, f'{SETTINGS_PREFIX}/sort_mode', '按命名'))
            self.sort_combo.currentTextChanged.connect(self.handle_form_changed)
            style_combo_popup(self.sort_combo, load_setting(settings, 'ui/theme', 'dark'))
            option_row.addWidget(self.sort_combo)

            option_row.addWidget(QLabel('方向'))
            self.order_combo = QComboBox()
            self.order_combo.addItems(list(SORT_ORDER_LABELS.keys()))
            self.order_combo.setCurrentText(load_setting(settings, f'{SETTINGS_PREFIX}/sort_order', '从小到大'))
            self.order_combo.currentTextChanged.connect(self.handle_form_changed)
            style_combo_popup(self.order_combo, load_setting(settings, 'ui/theme', 'dark'))
            option_row.addWidget(self.order_combo)
            option_row.addStretch(1)
            layout.addWidget(option_row_widget)

            tip_label = QLabel(TIP_TEXT)
            tip_label.setProperty('cardSub', True)
            tip_label.setWordWrap(True)
            layout.addWidget(tip_label)

            self.summary_label = QLabel(SUMMARY_EMPTY_TEXT)
            self.summary_label.setProperty('cardSub', True)
            self.summary_label.setWordWrap(True)
            layout.addWidget(self.summary_label)

            button_row = QHBoxLayout()
            button_row.addStretch(1)
            self.run_button = QPushButton(RUN_BUTTON_TEXT)
            self.run_button.clicked.connect(self.run_rename)
            button_row.addWidget(self.run_button)
            layout.addLayout(button_row)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(180)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)

            root.addWidget(card)
            self.refresh_summary()

        def set_busy(self, busy: bool) -> None:
            self.is_running = busy
            self.folder_edit.setEnabled(not busy)
            self.choose_button.setEnabled(not busy)
            self.prefix_edit.setEnabled(not busy)
            self.group_combo.setEnabled(not busy)
            self.sort_combo.setEnabled(not busy)
            self.order_combo.setEnabled(not busy)
            self.run_button.setEnabled(not busy)
            self.run_button.setText(RUNNING_BUTTON_TEXT if busy else RUN_BUTTON_TEXT)
            if QApplication is not None:
                QApplication.processEvents()

        def choose_folder(self):
            if self.is_running:
                return
            path = QFileDialog.getExistingDirectory(self, '选择需要批量命名的文件夹', self.folder_edit.text() or str(ROOT))
            if not path:
                return
            self.folder_edit.setText(path)
            save_setting(self.settings, f'{SETTINGS_PREFIX}/input_dir', path)
            self.refresh_summary()

        def handle_form_changed(self):
            if self.is_running:
                return
            save_setting(self.settings, f'{SETTINGS_PREFIX}/prefix', self.prefix_edit.text().strip() or DEFAULT_PREFIX)
            save_setting(self.settings, f'{SETTINGS_PREFIX}/group_mode', self.group_combo.currentText())
            save_setting(self.settings, f'{SETTINGS_PREFIX}/sort_mode', self.sort_combo.currentText())
            save_setting(self.settings, f'{SETTINGS_PREFIX}/sort_order', self.order_combo.currentText())
            self.refresh_summary()

        def refresh_summary(self):
            folder_path = self.folder_edit.text().strip()
            prefix = self.prefix_edit.text().strip() or DEFAULT_PREFIX
            errors = validate_batch_rename_form(folder_path, prefix)
            if errors:
                self.current_summary = None
                self.summary_label.setText(errors[0])
                return
            module = get_name_module()
            try:
                summary = module.summarize_folder(
                    folder_path,
                    prefix,
                    get_group_mode_value(self.group_combo.currentText()),
                    get_sort_mode_value(self.sort_combo.currentText()),
                    get_sort_order_value(self.order_combo.currentText()),
                )
            except Exception as exc:
                self.current_summary = None
                self.summary_label.setText(f'无法读取文件夹: {exc}')
                return
            self.current_summary = summary
            self.summary_label.setText(format_batch_rename_summary(summary))

        def run_rename(self):
            if self.is_running:
                return
            folder_path = self.folder_edit.text().strip()
            prefix = self.prefix_edit.text().strip() or DEFAULT_PREFIX
            errors = validate_batch_rename_form(folder_path, prefix)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return

            self.set_busy(True)
            self.log.clear()
            try:
                module = get_name_module()
                summary = module.summarize_folder(
                    folder_path,
                    prefix,
                    get_group_mode_value(self.group_combo.currentText()),
                    get_sort_mode_value(self.sort_combo.currentText()),
                    get_sort_order_value(self.order_combo.currentText()),
                )
                total_files = int(summary.get('total_files', 0) or 0)
                if total_files <= 0:
                    show_themed_warning(self, '提示', '当前目录第一层没有可命名文件')
                    return

                save_setting(self.settings, f'{SETTINGS_PREFIX}/input_dir', folder_path)
                save_setting(self.settings, f'{SETTINGS_PREFIX}/prefix', prefix)
                self.log.appendPlainText(f'命名目录: {folder_path}')
                self.log.appendPlainText(format_batch_rename_summary(summary))

                results = module.rename_files(
                    folder_path,
                    prefix,
                    get_group_mode_value(self.group_combo.currentText()),
                    get_sort_mode_value(self.sort_combo.currentText()),
                    get_sort_order_value(self.order_combo.currentText()),
                )
                renamed_count = 0
                skipped_count = 0
                for item in results:
                    if item.get('renamed'):
                        renamed_count += 1
                    else:
                        skipped_count += 1
                    self.log.appendPlainText(f'OK {item["source_name"]} -> {item["target_name"]}')

                show_themed_success(
                    self,
                    '完成',
                    [
                        f'已处理 {len(results)} 个文件',
                        f'实际改名 {renamed_count} 个文件',
                        f'原名一致 {skipped_count} 个文件',
                    ],
                )
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '批量命名失败', str(exc))
            finally:
                self.set_busy(False)
                self.refresh_summary()

    return BatchRenameTab
