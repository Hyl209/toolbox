from __future__ import annotations

from pathlib import Path


SETTINGS_PREFIX = 'filesorter'
TITLE = '文件分类'
SUBTITLE = '选择一个文件夹，按大类自动创建中文目录并移动第一层文件'
FOLDER_PLACEHOLDER = '选择需要分类的文件夹'
TIP_TEXT = '仅勾选的分类会被移动，未勾选的文件保持原位'
SUMMARY_EMPTY_TEXT = '请选择文件夹'
RUN_BUTTON_TEXT = '开始分类'
RUNNING_BUTTON_TEXT = '分类中...'
CHOOSE_BUTTON_TEXT = '选择路径'
SUMMARY_CATEGORY_ORDER = ('图片', '视频', '音频', '文档', '压缩包', '程序', '其他')


def format_file_sorter_summary(summary: dict[str, object]) -> str:
    total_files = int(summary.get('total_files', 0) or 0)
    if total_files <= 0:
        return '当前目录第一层没有可分类文件'
    counts = summary.get('category_counts', {})
    selected_total = int(summary.get('selected_total_files', 0) or 0)
    lines = [f'当前目录第一层共 {total_files} 个文件']
    for category in SUMMARY_CATEGORY_ORDER:
        count = 0
        if isinstance(counts, dict):
            count = int(counts.get(category, 0) or 0)
        if count:
            lines.append(f'{category}: {count}')
    lines.append(f'本次分类: {selected_total} 个文件')
    return '\n'.join(lines)


def validate_file_sorter_form(folder_path: str) -> list[str]:
    errors: list[str] = []
    cleaned = folder_path.strip()
    if not cleaned:
        errors.append('请选择需要分类的文件夹')
        return errors
    path = Path(cleaned)
    if not path.exists():
        errors.append('选择的文件夹不存在')
    elif not path.is_dir():
        errors.append('选择的路径不是文件夹')
    return errors


def build_file_sorter_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QCheckBox = deps['QCheckBox']
    QPlainTextEdit = deps['QPlainTextEdit']
    QFileDialog = deps['QFileDialog']
    QApplication = deps['QApplication']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    get_file_sorter_module = deps['get_file_sorter_module']
    ROOT = deps['ROOT']

    class FileSorterTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.sorter_module = get_file_sorter_module()
            self.current_summary: dict[str, object] | None = None
            self.category_checkboxes: dict[str, object] = {}
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

            tip_label = QLabel(TIP_TEXT)
            tip_label.setProperty('cardSub', True)
            tip_label.setWordWrap(True)
            layout.addWidget(tip_label)

            category_row_widget, category_row = make_transparent_row()
            for category in self.sorter_module.CATEGORY_ORDER:
                checkbox = QCheckBox(category)
                checkbox.setChecked(load_setting(settings, f'{SETTINGS_PREFIX}/category_{category}', '1') != '0')
                checkbox.stateChanged.connect(self.handle_category_selection_changed)
                self.category_checkboxes[category] = checkbox
                category_row.addWidget(checkbox)
            category_row.addStretch(1)
            layout.addWidget(category_row_widget)

            self.summary_label = QLabel(SUMMARY_EMPTY_TEXT)
            self.summary_label.setProperty('cardSub', True)
            self.summary_label.setWordWrap(True)
            layout.addWidget(self.summary_label)

            button_row = QHBoxLayout()
            button_row.addStretch(1)
            self.run_button = QPushButton(RUN_BUTTON_TEXT)
            self.run_button.clicked.connect(self.run_sorting)
            button_row.addWidget(self.run_button)
            layout.addLayout(button_row)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(160)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)

            root.addWidget(card)
            self.refresh_summary()

        def set_busy(self, busy: bool) -> None:
            self.is_running = busy
            self.folder_edit.setEnabled(not busy)
            self.choose_button.setEnabled(not busy)
            self.run_button.setEnabled(not busy)
            self.run_button.setText(RUNNING_BUTTON_TEXT if busy else RUN_BUTTON_TEXT)
            for checkbox in self.category_checkboxes.values():
                checkbox.setEnabled(not busy)
            if QApplication is not None:
                QApplication.processEvents()

        def get_selected_categories(self) -> tuple[str, ...]:
            return tuple(category for category, checkbox in self.category_checkboxes.items() if checkbox.isChecked())

        def save_selected_categories(self) -> None:
            for category, checkbox in self.category_checkboxes.items():
                save_setting(self.settings, f'{SETTINGS_PREFIX}/category_{category}', '1' if checkbox.isChecked() else '0')

        def summarize_folder(self, folder_path: str, selected_categories: tuple[str, ...] | None = None) -> dict[str, object]:
            categories = self.get_selected_categories() if selected_categories is None else selected_categories
            return self.sorter_module.summarize_folder(folder_path, categories)

        def append_result_log(self, item: dict[str, object]) -> tuple[int, int, int]:
            target_label = f'{item["category"]}\\{item["target_name"]}'
            if item.get('success'):
                if item.get('renamed'):
                    self.log.appendPlainText(f'RENAME {item["source_name"]} -> {target_label}')
                    return 1, 1, 0
                self.log.appendPlainText(f'OK {item["source_name"]} -> {target_label}')
                return 1, 0, 0
            self.log.appendPlainText(f'ERROR {item["source_name"]} -> {target_label}: {item["error"]}')
            return 0, 0, 1

        def handle_category_selection_changed(self):
            if self.is_running:
                return
            self.save_selected_categories()
            self.refresh_summary()

        def choose_folder(self):
            if self.is_running:
                return
            path = QFileDialog.getExistingDirectory(self, '选择需要分类的文件夹', self.folder_edit.text() or str(ROOT))
            if not path:
                return
            self.folder_edit.setText(path)
            save_setting(self.settings, f'{SETTINGS_PREFIX}/input_dir', path)
            self.refresh_summary()

        def refresh_summary(self):
            folder_path = self.folder_edit.text().strip()
            errors = validate_file_sorter_form(folder_path)
            if errors:
                self.current_summary = None
                self.summary_label.setText(errors[0])
                return
            try:
                summary = self.summarize_folder(folder_path)
            except Exception as exc:
                self.current_summary = None
                self.summary_label.setText(f'无法读取文件夹: {exc}')
                return
            self.current_summary = summary
            self.summary_label.setText(format_file_sorter_summary(summary))

        def run_sorting(self):
            if self.is_running:
                return
            folder_path = self.folder_edit.text().strip()
            errors = validate_file_sorter_form(folder_path)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return

            self.set_busy(True)
            self.log.clear()
            selected_categories = self.get_selected_categories()
            try:
                summary = self.summarize_folder(folder_path, selected_categories)
                self.current_summary = summary
                selected_total = int(summary.get('selected_total_files', 0) or 0)
                if selected_total <= 0:
                    show_themed_warning(self, '提示', '当前勾选分类没有可分类文件')
                    return

                save_setting(self.settings, f'{SETTINGS_PREFIX}/input_dir', folder_path)
                self.log.appendPlainText(f'分类目录: {folder_path}')
                self.log.appendPlainText(format_file_sorter_summary(summary))

                files = summary.get('files')
                results = self.sorter_module.classify_files(
                    folder_path,
                    selected_categories,
                    files if isinstance(files, list) else None,
                )
                moved_count = 0
                renamed_count = 0
                failed_count = 0
                for item in results:
                    moved_delta, renamed_delta, failed_delta = self.append_result_log(item)
                    moved_count += moved_delta
                    renamed_count += renamed_delta
                    failed_count += failed_delta

                show_themed_success(
                    self,
                    '完成',
                    [
                        f'已移动 {moved_count} 个文件',
                        f'已重命名 {renamed_count} 个文件',
                        f'失败 {failed_count} 个文件',
                        f'未处理 {max(0, int(summary.get("total_files", 0) or 0) - selected_total)} 个文件',
                    ],
                )
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '分类失败', str(exc))
            finally:
                self.set_busy(False)
                self.refresh_summary()

    return FileSorterTab
