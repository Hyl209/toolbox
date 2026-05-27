from __future__ import annotations

from pathlib import Path


def format_same_summary(result: dict[str, object]) -> str:
    scanned_files = int(result.get('scanned_files', 0) or 0)
    mode_text = '递归扫描' if result.get('recursive') else '仅第一层'
    if scanned_files <= 0:
        return f'{mode_text}: 当前范围没有可检测文件'
    duplicate_group_count = int(result.get('duplicate_group_count', 0) or 0)
    duplicate_file_count = int(result.get('duplicate_file_count', 0) or 0)
    lines = [f'{mode_text}: 共扫描 {scanned_files} 个文件']
    if duplicate_group_count <= 0:
        lines.append('未发现重复文件')
        return '\n'.join(lines)
    lines.append(f'发现 {duplicate_group_count} 组重复文件')
    lines.append(f'待移动 {duplicate_file_count} 个重复文件')
    target_dir = result.get('target_dir')
    if target_dir:
        lines.append(f'目标目录: {target_dir}')
    return '\n'.join(lines)


def validate_same_form(folder_path: str) -> list[str]:
    errors: list[str] = []
    cleaned = folder_path.strip()
    if not cleaned:
        errors.append('请选择需要检测的文件夹')
        return errors
    path = Path(cleaned)
    if not path.exists():
        errors.append('选择的文件夹不存在')
    elif not path.is_dir():
        errors.append('选择的路径不是文件夹')
    return errors


def build_same_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QCheckBox = deps['QCheckBox']
    QFileDialog = deps['QFileDialog']
    Qt = deps['Qt']
    QObject = deps.get('QObject')
    QThread = deps.get('QThread')
    Signal = deps.get('Signal')
    DropZoneCard = deps['DropZoneCard']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    get_same_module = deps['get_same_module']
    ROOT = deps['ROOT']

    class _FallbackSignal:
        def __init__(self):
            self._callbacks: list[object] = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for callback in list(self._callbacks):
                callback(*args)

    if QObject is not None and Signal is not None:
        class SameDetectionWorker(QObject):
            finished = Signal(object)
            failed = Signal(str)

            def __init__(self, module, folder_path: str, recursive: bool):
                super().__init__()
                self.module = module
                self.folder_path = folder_path
                self.recursive = recursive

            def run(self):
                try:
                    self.finished.emit(self.module.find_duplicate_groups(self.folder_path, self.recursive))
                except Exception as exc:
                    self.failed.emit(str(exc))
    else:
        class SameDetectionWorker:
            def __init__(self, module, folder_path: str, recursive: bool):
                self.module = module
                self.folder_path = folder_path
                self.recursive = recursive
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    self.finished.emit(self.module.find_duplicate_groups(self.folder_path, self.recursive))
                except Exception as exc:
                    self.failed.emit(str(exc))

    class SameTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.current_result: dict[str, object] | None = None
            self.is_detecting = False
            self.worker_thread = None
            self.worker = None
            root = QVBoxLayout(self)
            card, layout = make_card('重复文件', '普通文件按字节完全一致判重，视频按 95% 内容相似度判重，保留首个文件并移动其余重复件')
            path_row = QHBoxLayout()
            self.folder_edit = QLineEdit(load_setting(settings, 'same/input_dir'))
            self.folder_edit.setPlaceholderText('选择需要检测的文件夹')
            self.folder_edit.editingFinished.connect(self.handle_input_changed)
            self.choose_button = QPushButton('选择路径')
            self.choose_button.clicked.connect(self.choose_folder)
            path_row.addWidget(self.folder_edit)
            path_row.addWidget(self.choose_button)
            layout.addLayout(path_row)
            option_row_widget, option_row = make_transparent_row()
            self.recursive_checkbox = QCheckBox('递归扫描子目录')
            self.recursive_checkbox.setChecked(load_setting(settings, 'same/recursive', '1') != '0')
            self.recursive_checkbox.stateChanged.connect(self.handle_recursive_changed)
            option_row.addWidget(self.recursive_checkbox)
            option_row.addStretch(1)
            layout.addWidget(option_row_widget)
            tip_label = QLabel('普通文件仍是精确判重；视频会抽取多帧做 95% 平均相似度比较，移动目标固定为根目录下的"重复文件"')
            tip_label.setProperty('cardSub', True)
            tip_label.setWordWrap(True)
            layout.addWidget(tip_label)
            self.summary_label = QLabel('请选择文件夹并开始检测')
            self.summary_label.setProperty('cardSub', True)
            self.summary_label.setWordWrap(True)
            layout.addWidget(self.summary_label)
            button_row = QHBoxLayout()
            button_row.addStretch(1)
            self.detect_button = QPushButton('开始检测')
            self.detect_button.clicked.connect(self.run_detection)
            button_row.addWidget(self.detect_button)
            self.move_button = QPushButton('移动重复件')
            self.move_button.setEnabled(False)
            self.move_button.clicked.connect(self.run_move)
            button_row.addWidget(self.move_button)
            layout.addLayout(button_row)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(160)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)
            self.handle_input_changed()

        def clear_result(self, message: str):
            self.current_result = None
            self.summary_label.setText(message)
            self.move_button.setEnabled(False)

        def handle_input_changed(self):
            folder_path = self.folder_edit.text().strip()
            if folder_path:
                save_setting(self.settings, 'same/input_dir', folder_path)
            errors = validate_same_form(folder_path)
            if errors:
                self.clear_result(errors[0])
                return
            self.clear_result('点击开始检测')

        def handle_recursive_changed(self):
            save_setting(self.settings, 'same/recursive', '1' if self.recursive_checkbox.isChecked() else '0')
            self.handle_input_changed()

        def choose_folder(self):
            path = QFileDialog.getExistingDirectory(self, '选择需要检测的文件夹', self.folder_edit.text() or str(ROOT))
            if not path:
                return
            self.folder_edit.setText(path)
            save_setting(self.settings, 'same/input_dir', path)
            self.handle_input_changed()

        def set_result(self, result: dict[str, object]):
            self.current_result = result
            self.summary_label.setText(format_same_summary(result))
            self.move_button.setEnabled(int(result.get('duplicate_file_count', 0) or 0) > 0)

        def set_detection_busy(self, busy: bool):
            self.is_detecting = busy
            self.folder_edit.setEnabled(not busy)
            self.choose_button.setEnabled(not busy)
            self.recursive_checkbox.setEnabled(not busy)
            self.detect_button.setEnabled(not busy)
            self.detect_button.setText('检测中...' if busy else '开始检测')
            if busy:
                self.move_button.setEnabled(False)
            elif self.current_result is not None:
                self.move_button.setEnabled(int(self.current_result.get('duplicate_file_count', 0) or 0) > 0)

        def cleanup_detection_worker(self):
            if self.worker_thread is not None:
                self.worker_thread.quit()
                self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None

        def handle_detection_finished(self, result: dict[str, object]):
            self.cleanup_detection_worker()
            self.set_detection_busy(False)
            self.set_result(result)
            self.log.appendPlainText(f'检测目录: {result["root"]}')
            self.log.appendPlainText(format_same_summary(result))
            groups = result.get('groups', [])
            if isinstance(groups, list) and groups:
                for index, group in enumerate(groups, start=1):
                    keeper = Path(group['keeper']).relative_to(result['root'])
                    duplicates = [str(Path(item).relative_to(result['root'])) for item in group.get('duplicates', [])]
                    self.log.appendPlainText(
                        f'GROUP {index} 保留 {keeper} | 移动 {len(duplicates)} 个: {", ".join(duplicates)}'
                    )
            else:
                self.log.appendPlainText('未发现可移动的重复文件')
            show_themed_success(self, '完成', ['重复文件检测完成'])

        def handle_detection_error(self, message: str):
            self.cleanup_detection_worker()
            self.set_detection_busy(False)
            self.log.appendPlainText(f'ERROR {message}')
            self.summary_label.setText('检测失败，请查看日志')
            show_themed_error(self, '检测失败', message)

        def run_detection(self):
            if self.is_detecting:
                return
            folder_path = self.folder_edit.text().strip()
            errors = validate_same_form(folder_path)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            recursive = self.recursive_checkbox.isChecked()
            save_setting(self.settings, 'same/input_dir', folder_path)
            save_setting(self.settings, 'same/recursive', '1' if recursive else '0')
            same_module = get_same_module()
            self.log.appendPlainText(f'开始检测: {folder_path}')
            self.summary_label.setText('正在检测，请稍候...')
            self.set_detection_busy(True)
            self.worker = SameDetectionWorker(same_module, folder_path, recursive)
            self.worker.finished.connect(self.handle_detection_finished)
            self.worker.failed.connect(self.handle_detection_error)
            if QThread is None:
                self.worker.run()
                return
            self.worker_thread = QThread(self)
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.start()

        def run_move(self):
            if not self.current_result or int(self.current_result.get('duplicate_file_count', 0) or 0) <= 0:
                show_themed_warning(self, '提示', '当前没有可移动的重复文件')
                return
            same_module = get_same_module()
            root_path = Path(self.current_result['root']).resolve()
            recursive = bool(self.current_result.get('recursive'))
            try:
                results = same_module.move_duplicates(root_path, self.current_result)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '移动失败', str(exc))
                return
            moved_count = 0
            renamed_count = 0
            failed_count = 0
            for item in results:
                source_relative = Path(item['source']).relative_to(root_path)
                target_relative = Path(item['target_path']).relative_to(root_path)
                if item.get('success'):
                    moved_count += 1
                    if item.get('renamed'):
                        renamed_count += 1
                        self.log.appendPlainText(f'RENAME {source_relative} -> {target_relative}')
                    else:
                        self.log.appendPlainText(f'OK {source_relative} -> {target_relative}')
                else:
                    failed_count += 1
                    self.log.appendPlainText(f'ERROR {source_relative} -> {target_relative}: {item["error"]}')
            refreshed = same_module.find_duplicate_groups(root_path, recursive)
            self.set_result(refreshed)
            self.log.appendPlainText(format_same_summary(refreshed))
            show_themed_success(
                self,
                '完成',
                [
                    f'已移动 {moved_count} 个重复文件',
                    f'已重命名 {renamed_count} 个文件',
                    f'失败 {failed_count} 个文件',
                ],
            )

    return SameTab
