from __future__ import annotations

import threading
from pathlib import Path


def build_direct_downloader_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QCheckBox = deps['QCheckBox']
    QFileDialog = deps['QFileDialog']
    QScrollArea = deps.get('QScrollArea')
    QObject = deps['QObject']
    QThread = deps['QThread']
    Signal = deps['Signal']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    get_direct_downloader_module = deps['get_direct_downloader_module']
    ROOT = deps['ROOT']

    module = get_direct_downloader_module()

    class DownloadWorker(QObject):
        log = Signal(str)
        progress = Signal(str)
        done = Signal(list)
        error = Signal(str)

        def __init__(self, requests, options):
            super().__init__()
            self.requests = requests
            self.options = options
            self._stop_event = threading.Event()
            self._process = None

        def cancel(self):
            self._stop_event.set()
            if self._process and self._process.poll() is None:
                self._process.terminate()

        def set_process(self, process):
            self._process = process

        def run(self):
            try:
                results = module.iter_download_requests(
                    self.requests,
                    self.options,
                    self.handle_output,
                    ROOT,
                    self.set_process,
                    self._stop_event.is_set,
                )
                self.done.emit(results)
            except Exception as exc:
                self.error.emit(str(exc))

        def handle_output(self, text: str):
            if module.is_aria2_progress_text(text):
                self.progress.emit(text)
            else:
                self.log.emit(text)

    class DirectDownloaderTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.worker_thread = None
            self.worker = None

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)
            content_host = QWidget()
            content_host.setStyleSheet('background: transparent;')
            if QScrollArea is not None:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setStyleSheet(
                    'QScrollArea {border: none; background: transparent;} '
                    'QScrollArea > QWidget > QWidget {background: transparent;} '
                    + build_global_scrollbar_style()
                )
                scroll.setWidget(content_host)
                root.addWidget(scroll)
            else:
                root.addWidget(content_host)

            content_root = QVBoxLayout(content_host)
            content_root.setContentsMargins(0, 0, 0, 0)
            content_root.setSpacing(0)
            card, layout = make_card('直链下载', '粘贴 LinkSwift 等工具提取出的真实直链，用 aria2 多连接下载')

            layout.addWidget(QLabel('直链'))
            self.url_edit = QPlainTextEdit()
            self.url_edit.setPlaceholderText('每行一个 http/https 链接')
            self.url_edit.setMinimumHeight(150)
            self.url_edit.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.url_edit)

            output_row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'directdownloader/output_dir', str(Path.home() / 'Downloads')))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.output_edit)
            output_row.addWidget(choose_btn)
            layout.addLayout(output_row)

            name_row = QHBoxLayout()
            name_row.addWidget(QLabel('文件名'))
            self.output_name_edit = QLineEdit()
            self.output_name_edit.setPlaceholderText('单个链接可选；多个链接请留空')
            name_row.addWidget(self.output_name_edit)
            layout.addLayout(name_row)

            option_row_widget, option_row = make_transparent_row()
            option_row.addWidget(QLabel('连接数'))
            self.connections_edit = QLineEdit(load_setting(settings, 'directdownloader/connections', '16'))
            self.connections_edit.setFixedWidth(72)
            option_row.addWidget(self.connections_edit)
            self.overwrite_checkbox = QCheckBox('覆盖同名文件')
            self.overwrite_checkbox.setChecked(load_setting(settings, 'directdownloader/overwrite', '0') == '1')
            option_row.addWidget(self.overwrite_checkbox)
            self.output_subdir_checkbox = QCheckBox('按文件名建文件夹')
            self.output_subdir_checkbox.setChecked(load_setting(settings, 'directdownloader/output_subdir_by_filename', '0') == '1')
            option_row.addWidget(self.output_subdir_checkbox)
            option_row.addStretch(1)
            layout.addWidget(option_row_widget)

            proxy_row_widget, proxy_row = make_transparent_row()
            proxy_row.addWidget(QLabel('代理'))
            host, port = module.split_proxy_url(load_setting(settings, 'directdownloader/proxy_url', ''))
            self.proxy_host_edit = QLineEdit(host)
            self.proxy_host_edit.setPlaceholderText('127.0.0.1')
            self.proxy_port_edit = QLineEdit(port)
            self.proxy_port_edit.setPlaceholderText('端口')
            self.proxy_port_edit.setFixedWidth(86)
            proxy_row.addWidget(self.proxy_host_edit)
            proxy_row.addWidget(self.proxy_port_edit)
            layout.addWidget(proxy_row_widget)

            header_row = QHBoxLayout()
            header_row.addWidget(QLabel('Referer'))
            self.referer_edit = QLineEdit(load_setting(settings, 'directdownloader/referer', ''))
            self.referer_edit.setPlaceholderText('需要防盗链时填写')
            header_row.addWidget(self.referer_edit)
            layout.addLayout(header_row)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(170)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            self._log_lines: list[str] = []
            self._progress_text = ''

            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.run_button = QPushButton('开始下载')
            self.run_button.clicked.connect(self.start_download)
            action_row.addWidget(self.run_button)
            self.stop_button = QPushButton('停止')
            self.stop_button.setEnabled(False)
            self.stop_button.clicked.connect(self.stop_download)
            action_row.addWidget(self.stop_button)
            layout.addLayout(action_row)
            content_root.addWidget(card)

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)

        def set_busy(self, busy: bool):
            self.run_button.setEnabled(not busy)
            self.stop_button.setEnabled(busy)
            self.run_button.setText('下载中...' if busy else '开始下载')

        def save_form(self):
            proxy_url = module.build_proxy_url(self.proxy_host_edit.text(), self.proxy_port_edit.text())
            save_setting(self.settings, 'directdownloader/output_dir', self.output_edit.text().strip())
            save_setting(self.settings, 'directdownloader/connections', self.connections_edit.text().strip() or '16')
            save_setting(self.settings, 'directdownloader/proxy_url', proxy_url)
            save_setting(self.settings, 'directdownloader/referer', self.referer_edit.text().strip())
            save_setting(self.settings, 'directdownloader/overwrite', '1' if self.overwrite_checkbox.isChecked() else '0')
            save_setting(
                self.settings,
                'directdownloader/output_subdir_by_filename',
                '1' if self.output_subdir_checkbox.isChecked() else '0',
            )

        def build_options(self):
            return module.DirectDownloadOptions(
                output_dir=self.output_edit.text().strip(),
                output_name=self.output_name_edit.text().strip(),
                proxy_url=module.build_proxy_url(self.proxy_host_edit.text(), self.proxy_port_edit.text()),
                connections=int(self.connections_edit.text().strip() or '16'),
                referer=self.referer_edit.text().strip(),
                overwrite=self.overwrite_checkbox.isChecked(),
                output_subdir_by_filename=self.output_subdir_checkbox.isChecked(),
            )

        def start_download(self):
            if self.worker_thread:
                return
            errors = module.validate_download_form(
                self.url_edit.toPlainText(),
                self.output_edit.text(),
                self.connections_edit.text(),
                self.output_name_edit.text(),
            )
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            requests = module.parse_download_requests(self.url_edit.toPlainText())
            self.save_form()
            self.log.clear()
            self.set_busy(True)
            self.worker_thread = QThread(self)
            self.worker = DownloadWorker(requests, self.build_options())
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.log.connect(self.append_log)
            self.worker.progress.connect(self.update_progress_log)
            self.worker.done.connect(self.handle_done)
            self.worker.error.connect(self.handle_error)
            self.worker.done.connect(self.cleanup_worker)
            self.worker.error.connect(self.cleanup_worker)
            self.worker_thread.start()

        def stop_download(self):
            if self.worker:
                self.append_log('正在停止下载...')
                self.worker.cancel()

        def refresh_log_view(self):
            text = '\n'.join([*self._log_lines, self._progress_text] if self._progress_text else self._log_lines)
            self.log.setPlainText(text)
            scrollbar = self.log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        def append_log(self, text: str):
            cleaned = str(text or '').strip()
            if not cleaned:
                return
            self._log_lines.append(cleaned)
            self.refresh_log_view()

        def update_progress_log(self, text: str):
            self._progress_text = str(text or '').strip()
            self.refresh_log_view()

        def handle_done(self, results):
            failed = [item for item in results if not item.get('success')]
            if failed:
                show_themed_error(self, '下载失败', f'{len(failed)} 个链接失败，详情见日志')
                return
            show_themed_success(self, '完成', [f'已完成 {len(results)} 个下载'])

        def handle_error(self, message: str):
            self.append_log(f'ERROR {message}')
            show_themed_error(self, '下载失败', message)

        def cleanup_worker(self, *_args):
            if not self.worker_thread:
                return
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None
            self.set_busy(False)

    return DirectDownloaderTab
