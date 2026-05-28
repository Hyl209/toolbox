from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .tab_constants import *
from .tab_formatters import *
from .tab_formatters import _guess_source_kind
from .tab_workers import build_worker_classes
from . import tab_panels


def validate_video_downloader_form(
    task_text: str,
    output_dir: str,
    api_id: str,
    api_hash: str,
    phone: str,
    recent_limit: str,
    download_all_messages: bool = False,
    date_from: str = '',
    date_to: str = '',
    telegram_include_videos: bool = True,
    telegram_include_photos: bool = False,
    web_candidate_index: str = '',
    web_download_all_candidates: bool = False,
    source_mode: str = 'mixed',
    get_video_downloader_module=None,
    module=None,
) -> list[str]:
    if module is None and get_video_downloader_module is None:
        errors: list[str] = []
        if not (task_text or '').strip():
            errors.append('请先输入下载链接')
        if not (output_dir or '').strip():
            errors.append('请选择输出目录')
        return errors
    if module is None:
        module = get_video_downloader_module()
    errors: list[str] = []
    mode_errors = validate_source_mode_urls(module.parse_task_lines(task_text), source_mode)
    errors.extend(mode_errors)
    try:
        indices = module.normalize_positive_indices(web_candidate_index, '网页候选序号')
        mode = module._parse_candidate_mode(web_candidate_index)[0]
        if mode in ('before', 'after') and indices and len(indices) != 1:
            errors.append('before/after 只需填写一个序号，如 before3 或 after5')
    except ValueError as exc:
        errors.append(str(exc))
    if mode_errors:
        if not (output_dir or '').strip():
            errors.append('请选择输出目录')
        return errors
    if web_download_all_candidates and str(web_candidate_index).strip():
        errors.append('勾选"网页全部候选"时，不需要再填写候选序号')
    session_file = Path(__file__).resolve().with_name(module.SESSION_FILE_NAME)
    config = module.TelegramConfig(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        session_file=session_file,
    )
    errors.extend(module.validate_download_request(
        task_text,
        output_dir,
        config,
        recent_limit=recent_limit,
        telegram_download_all_messages=download_all_messages,
        date_from=date_from,
        date_to=date_to,
        telegram_include_videos=telegram_include_videos,
        telegram_include_photos=telegram_include_photos,
    ))
    return errors


def build_video_downloader_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QScrollArea = deps['QScrollArea']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']
    QFileDialog = deps['QFileDialog']
    QApplication = deps['QApplication']
    QCheckBox = deps['QCheckBox']
    QComboBox = deps['QComboBox']
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
    style_combo_popup = deps['style_combo_popup']
    get_video_downloader_module = deps['get_video_downloader_module']
    ROOT = deps['ROOT']
    VIDEO_DOWNLOADER_DIR = deps['VIDEO_DOWNLOADER_DIR']

    from toolbox_app.utils import _FallbackSignal

    DownloadWorker, ScanWorker, ThumbnailWorker = build_worker_classes(QObject, QThread, Signal, _FallbackSignal)

    class VideoDownloaderTab(QWidget):
        def __init__(self, settings, source_mode: str = 'mixed'):
            super().__init__()
            self.settings = settings
            self.source_mode = normalize_source_mode(source_mode)
            self.mode_meta = MODE_META[self.source_mode]
            self.mode_settings_prefix = SETTINGS_PREFIX if self.source_mode == 'mixed' else f'{SETTINGS_PREFIX}/{self.source_mode}'
            self.is_running = False
            self.worker_thread = None
            self.worker = None
            self._init_instance_vars()

            textedit_style = build_video_textedit_style(build_global_scrollbar_style, self.current_theme)
            task_min_height = 110 if self.source_mode == 'web' else 150
            log_min_height = 110 if self.source_mode == 'web' else 150

            card, layout, card_root = self._build_root_container()

            if self.source_mode == 'telegram':
                self._build_telegram_login_section(layout)

            center_row = None
            if self.source_mode != 'web':
                center_row = QHBoxLayout()
                center_row.setSpacing(18)

            self._build_task_section(layout, center_row, textedit_style, task_min_height)

            if self.source_mode == 'telegram':
                self._build_telegram_options_section(center_row)
            elif self.source_mode == 'web':
                self._build_web_options_section(layout)

            self._build_log_section(layout, center_row, textedit_style, log_min_height)

            card_root.addWidget(card)
            if self.recent_count_edit is not None:
                self.handle_all_messages_changed()
            if self.web_candidate_index_edit is not None:
                self.handle_web_all_candidates_changed()
            self.refresh_backend_status()
            self.refresh_summary()

        def _init_instance_vars(self):
            self.scan_worker_thread = None
            self.scan_worker = None
            self.thumbnail_worker_thread = None
            self.thumbnail_worker = None
            self.api_id_edit = None
            self.api_hash_edit = None
            self.phone_edit = None
            self.code_edit = None
            self.send_code_button = None
            self.login_button = None
            self.check_status_button = None
            self.login_status_label = None
            self.backend_status_label = None
            self.refresh_status_button = None
            self.recent_count_edit = None
            self.all_messages_checkbox = None
            self.date_from_edit = None
            self.date_to_edit = None
            self.include_video_checkbox = None
            self.include_photo_checkbox = None
            self.web_candidate_index_edit = None
            self.web_candidate_exclude_checkbox = None
            self.web_candidate_before_checkbox = None
            self.web_candidate_after_checkbox = None
            self.web_all_candidates_checkbox = None
            self.concurrent_combo = None
            self.scan_button = None
            self.pause_button = None
            self.cancel_button = None
            self.reconnect_button = None
            self.web_scan_results: dict[str, dict[str, object]] = {}
            self.phone_code_hash = load_setting(self.settings, self._shared_setting_key('phone_code_hash'))
            self.current_theme = load_setting(self.settings, 'ui/theme', 'dark')
            self._last_cover_dir = load_setting(self.settings, self._mode_setting_key('cover_dir'), '')
            self.current_task_index = -1
            self.total_tasks = 0
            self.completed_tasks = 0
            self._last_log_is_progress = False
            self._token = None
            self.module = get_video_downloader_module()
            self.session_file = VIDEO_DOWNLOADER_DIR / self.module.SESSION_FILE_NAME

        def _build_root_container(self):
            return tab_panels.build_root_container(self, deps)

        def _build_telegram_login_section(self, layout):
            tab_panels.build_telegram_login_section(self, layout, deps)

        def _build_task_section(self, layout, center_row, textedit_style, task_min_height):
            tab_panels.build_task_section(self, layout, center_row, textedit_style, task_min_height, deps)

        def _build_telegram_options_section(self, center_row):
            tab_panels.build_telegram_options_section(self, center_row, deps)

        def _build_web_options_section(self, layout):
            tab_panels.build_web_options_section(self, layout, deps)

        def _build_log_section(self, layout, center_row, textedit_style, log_min_height):
            tab_panels.build_log_section(self, layout, center_row, textedit_style, log_min_height, deps)

        def _shared_setting_key(self, name: str) -> str:
            return f'{SETTINGS_PREFIX}/{name}'

        def _mode_setting_key(self, name: str) -> str:
            return f'{self.mode_settings_prefix}/{name}'

        def _concurrent_value(self) -> str:
            if self.concurrent_combo is None:
                return '1'
            idx = self.concurrent_combo.currentIndex()
            if idx == 0:
                return '0'
            return str(idx)

        @staticmethod
        def _widget_text(widget) -> str:
            return widget.text().strip() if widget is not None else ''

        @staticmethod
        def _is_checked(widget) -> bool:
            return bool(widget is not None and widget.isChecked())

        def save_form_settings(self):
            if self.api_id_edit is not None:
                save_setting(self.settings, self._shared_setting_key('api_id'), self._widget_text(self.api_id_edit))
            if self.api_hash_edit is not None:
                save_setting(self.settings, self._shared_setting_key('api_hash'), self._widget_text(self.api_hash_edit))
            if self.phone_edit is not None:
                save_setting(self.settings, self._shared_setting_key('phone'), self._widget_text(self.phone_edit))
            save_setting(self.settings, self._mode_setting_key('output_dir'), self._widget_text(self.output_edit))
            if self.recent_count_edit is not None:
                save_setting(self.settings, self._mode_setting_key('recent_limit'), self._widget_text(self.recent_count_edit) or DEFAULT_RECENT_LIMIT)
                save_setting(self.settings, self._mode_setting_key('all_messages'), '1' if self._is_checked(self.all_messages_checkbox) else '0')
                save_setting(self.settings, self._mode_setting_key('date_from'), self._widget_text(self.date_from_edit))
                save_setting(self.settings, self._mode_setting_key('date_to'), self._widget_text(self.date_to_edit))
                save_setting(self.settings, self._mode_setting_key('include_videos'), '1' if self._is_checked(self.include_video_checkbox) else '0')
                save_setting(self.settings, self._mode_setting_key('include_photos'), '1' if self._is_checked(self.include_photo_checkbox) else '0')
            if self.web_candidate_index_edit is not None:
                save_setting(self.settings, self._mode_setting_key('web_candidate_index'), self._widget_text(self.web_candidate_index_edit))
                save_setting(self.settings, self._mode_setting_key('web_candidate_exclude'), '1' if self._is_checked(self.web_candidate_exclude_checkbox) else '0')
                save_setting(self.settings, self._mode_setting_key('web_candidate_before'), '1' if self._is_checked(self.web_candidate_before_checkbox) else '0')
                save_setting(self.settings, self._mode_setting_key('web_candidate_after'), '1' if self._is_checked(self.web_candidate_after_checkbox) else '0')
                save_setting(self.settings, self._mode_setting_key('web_all_candidates'), '1' if self._is_checked(self.web_all_candidates_checkbox) else '0')
            save_setting(self.settings, self._mode_setting_key('overwrite'), '1' if self._is_checked(self.overwrite_checkbox) else '0')
            save_setting(self.settings, self._mode_setting_key('concurrent'), self._concurrent_value() if self.concurrent_combo is not None else '1')
            save_setting(self.settings, self._shared_setting_key('phone_code_hash'), self.phone_code_hash)

        def append_log(self, text: str):
            if not text:
                return
            if text.startswith('正在下载'):
                if self._last_log_is_progress:
                    cursor = self.log.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.insertText(text)
                    if QApplication is not None:
                        QApplication.processEvents()
                    return
                self._last_log_is_progress = True
            else:
                self._last_log_is_progress = False
            self.log.appendPlainText(text)
            if QApplication is not None:
                QApplication.processEvents()

        def set_busy(self, busy: bool):
            self.is_running = busy
            widgets = [
                self.api_id_edit,
                self.api_hash_edit,
                self.phone_edit,
                self.code_edit,
                self.task_edit,
                self.recent_count_edit,
                self.all_messages_checkbox,
                self.date_from_edit,
                self.date_to_edit,
                self.include_video_checkbox,
                self.include_photo_checkbox,
                self.web_candidate_index_edit,
                self.web_candidate_exclude_checkbox,
                self.web_candidate_before_checkbox,
                self.web_candidate_after_checkbox,
                self.web_all_candidates_checkbox,
                self.output_edit,
                self.overwrite_checkbox,
                self.concurrent_combo,
                self.choose_button,
                self.scan_button,
                self.cover_button,
                self.send_code_button,
                self.login_button,
                self.check_status_button,
                self.refresh_status_button,
            ]
            for widget in widgets:
                if widget is not None:
                    widget.setEnabled(not busy)
            self.run_button.setVisible(not busy)
            if self.pause_button is not None:
                self.pause_button.setVisible(busy)
                self.pause_button.setText('暂停')
            if self.cancel_button is not None:
                self.cancel_button.setVisible(busy)
            if self.reconnect_button is not None:
                self.reconnect_button.setVisible(busy)
            if QApplication is not None:
                QApplication.processEvents()

        def handle_all_messages_changed(self):
            if self.recent_count_edit is None or self.all_messages_checkbox is None:
                return
            self.recent_count_edit.setEnabled(not self.all_messages_checkbox.isChecked())
            self.save_form_settings()

        def toggle_pause(self):
            if self._token is None:
                return
            if self._token.pause.is_set():
                self._token.pause.clear()
                if self.pause_button is not None:
                    self.pause_button.setText('暂停')
            else:
                self._token.pause.set()
                if self.pause_button is not None:
                    self.pause_button.setText('继续')

        def cancel_download(self):
            if self._token is not None:
                self._token.cancel.set()

        def reconnect_download(self):
            if self._token is not None:
                self._token.reconnect.set()
                self.append_log('正在重连...')

        def handle_download_cancelled(self):
            self.append_log('下载已取消')
            self.progress_label.setText('下载已取消')
            self.cleanup_worker()
            self.set_busy(False)

        def _resolve_candidate_mode(self) -> str:
            if self._is_checked(self.web_candidate_exclude_checkbox):
                return 'exclude'
            if self._is_checked(self.web_candidate_before_checkbox):
                return 'before'
            if self._is_checked(self.web_candidate_after_checkbox):
                return 'after'
            return self.module._parse_candidate_mode(self._widget_text(self.web_candidate_index_edit))[0]

        def _uncheck_mode_checkboxes(self, keep: str = ''):
            if keep != 'exclude' and self.web_candidate_exclude_checkbox is not None:
                self.web_candidate_exclude_checkbox.setChecked(False)
            if keep != 'before' and self.web_candidate_before_checkbox is not None:
                self.web_candidate_before_checkbox.setChecked(False)
            if keep != 'after' and self.web_candidate_after_checkbox is not None:
                self.web_candidate_after_checkbox.setChecked(False)

        def handle_exclude_checked(self):
            if self.web_candidate_exclude_checkbox is not None and self.web_candidate_exclude_checkbox.isChecked():
                self._uncheck_mode_checkboxes('exclude')
            self.save_form_settings()

        def handle_before_checked(self):
            if self.web_candidate_before_checkbox is not None and self.web_candidate_before_checkbox.isChecked():
                self._uncheck_mode_checkboxes('before')
            self.save_form_settings()

        def handle_after_checked(self):
            if self.web_candidate_after_checkbox is not None and self.web_candidate_after_checkbox.isChecked():
                self._uncheck_mode_checkboxes('after')
            self.save_form_settings()

        def handle_web_all_candidates_changed(self):
            if self.web_candidate_index_edit is None or self.web_all_candidates_checkbox is None:
                return
            enabled = not self.web_all_candidates_checkbox.isChecked()
            self.web_candidate_index_edit.setEnabled(enabled)
            if self.web_candidate_exclude_checkbox is not None:
                self.web_candidate_exclude_checkbox.setEnabled(enabled)
            if self.web_candidate_before_checkbox is not None:
                self.web_candidate_before_checkbox.setEnabled(enabled)
            if self.web_candidate_after_checkbox is not None:
                self.web_candidate_after_checkbox.setEnabled(enabled)
            self.save_form_settings()

        def reset_progress_ui(self, total_tasks: int):
            self.total_tasks = max(0, total_tasks)
            self.completed_tasks = 0
            self.current_task_index = -1
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_label.setText(f'准备开始，共 {self.total_tasks} 个任务')
            self._update_task_counter()

        def _update_task_counter(self):
            if self.total_tasks > 0:
                current = self.current_task_index + 1 if self.current_task_index >= 0 else 0
                self.task_counter_label.setText(f'任务进度: {self.completed_tasks} 完成 / {current} 进行中 / {self.total_tasks} 总计')
            else:
                self.task_counter_label.setText('')

        def update_progress_percent(self, current_percent: float | int):
            if self.total_tasks <= 0:
                self.progress_bar.setMaximum(0)
                return
            current = max(0.0, min(100.0, float(current_percent)))
            overall = ((self.completed_tasks + current / 100.0) / self.total_tasks) * 100.0
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(max(0, min(100, int(overall))))

        def handle_worker_progress(self, message: str):
            parsed = parse_progress_marker(message)
            if parsed is not None:
                kind, payload = parsed
                if kind == 'task_start':
                    self.current_task_index = int(payload.get('index', '0') or 0)
                    self.total_tasks = int(payload.get('total', str(self.total_tasks)) or self.total_tasks or 0)
                    url = payload.get('url', '')
                    self.progress_label.setText(f'处理中 {self.current_task_index + 1}/{self.total_tasks}: {url}')
                    self._update_task_counter()
                elif kind == 'task_done':
                    self.completed_tasks = int(payload.get('completed', str(self.completed_tasks)) or self.completed_tasks)
                    self.total_tasks = int(payload.get('total', str(self.total_tasks)) or self.total_tasks or 0)
                    self.update_progress_percent(0)
                    self.progress_label.setText(f'已完成 {self.completed_tasks}/{self.total_tasks} 个任务')
                    self._update_task_counter()
                elif kind == 'tg_scan':
                    scanned = int(payload.get('scanned', '0') or 0)
                    matched = int(payload.get('matched', '0') or 0)
                    prefix = f'处理中 {self.current_task_index + 1}/{self.total_tasks}' if self.total_tasks > 0 and self.current_task_index >= 0 else '扫描中'
                    self.progress_label.setText(f'{prefix}: 已扫描 {scanned} 条，命中 {matched} 个媒体')
                elif kind == 'file':
                    name = payload.get('name', '')
                    index = payload.get('index', '0')
                    total = payload.get('total', '0')
                    prefix = f'处理中 {self.current_task_index + 1}/{self.total_tasks}' if self.total_tasks > 0 and self.current_task_index >= 0 else '处理中 '
                    if total and total != '0':
                        self.progress_label.setText(f'{prefix}: 当前文件 {name} ({index}/{total})')
                    else:
                        self.progress_label.setText(f'{prefix}: 当前文件 {name}')
                elif kind == 'web_percent':
                    try:
                        self.update_progress_percent(float(payload.get('percent', '0') or 0))
                    except (TypeError, ValueError):
                        pass
                elif kind == 'web_aria2':
                    name = payload.get('name', '')
                    percent = payload.get('percent', '')
                    speed = payload.get('speed', '')
                    eta = payload.get('eta', '')
                    try:
                        self.update_progress_percent(float(percent))
                    except (TypeError, ValueError):
                        pass
                    details = []
                    if speed:
                        details.append(speed)
                    if eta:
                        details.append(f'ETA {eta}')
                    prefix = f'处理中 {self.current_task_index + 1}/{self.total_tasks}' if self.total_tasks > 0 and self.current_task_index >= 0 else '处理中'
                    self.progress_label.setText(f'{prefix}: {name} {" | ".join(details)}')
                elif kind in {'web_status', 'tg_media'}:
                    percent = 0.0
                    try:
                        percent = float(payload.get('percent', '0') or 0)
                        self.update_progress_percent(percent)
                    except (TypeError, ValueError):
                        pass
                    name = payload.get('name', '')
                    speed = payload.get('speed', '')
                    eta = payload.get('eta', '')
                    details = [f'{percent:.1f}%']
                    if speed:
                        details.append(speed)
                    if eta:
                        details.append(f'ETA {eta}')
                    prefix = f'处理中 {self.current_task_index + 1}/{self.total_tasks}' if self.total_tasks > 0 and self.current_task_index >= 0 else '处理中'
                    self.progress_label.setText(f'{prefix}: {name} {" | ".join(details)}')
                return
            self.append_log(message)
            if '网页下载中' in message:
                percent_text = message.rsplit(' ', 1)[-1].replace('%', '').strip()
                try:
                    self.update_progress_percent(float(percent_text))
                except ValueError:
                    pass

        def finalize_download(self, results: list[dict[str, object]]):
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)
            summary_lines = summarize_download_results(results)
            for item in results:
                if not item.get('success'):
                    summary_lines.append(f'失败: {item.get("source_url")} -> {item.get("error")}')
            show_themed_success(self, '完成', summary_lines[:6])
            self.append_log('----')
            for line in summary_lines:
                self.append_log(line)
            self.progress_label.setText(f'下载完成，成功 {summary_lines[1].split(": ", 1)[-1]}，失败 {summary_lines[2].split(": ", 1)[-1]}')
            self.cleanup_worker()
            self.set_busy(False)

        def handle_worker_error(self, message: str):
            self.append_log(f'错误：{message}')
            self.progress_label.setText('下载失败')
            self.cleanup_worker()
            self.set_busy(False)
            show_themed_error(self, '下载失败', message)

        def cleanup_worker(self):
            if self.worker_thread is not None:
                self.worker_thread.quit()
                self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None

        def build_config(self):
            return self.module.TelegramConfig(
                api_id=self._widget_text(self.api_id_edit),
                api_hash=self._widget_text(self.api_hash_edit),
                phone=self._widget_text(self.phone_edit),
                session_file=self.session_file,
            )

        def refresh_backend_status(self):
            if self.backend_status_label is None:
                return
            self.backend_status_label.setText(format_backend_status(self.module.probe_download_backends()))

        def apply_theme(self, theme_name: str):
            self.current_theme = theme_name if theme_name in {'dark', 'light'} else 'dark'
            style = build_video_textedit_style(build_global_scrollbar_style, self.current_theme)
            apply_video_textedit_surface(self.task_edit, style, self.current_theme)
            apply_video_textedit_surface(self.log, style, self.current_theme)
            if self.concurrent_combo is not None:
                style_combo_popup(self.concurrent_combo, self.current_theme)

        def handle_task_text_changed(self):
            if self.source_mode == 'web':
                self.web_scan_results = {}
            self.refresh_summary()

        def refresh_summary(self):
            urls = self.module.parse_task_lines(self.task_edit.toPlainText())
            if self.source_mode == 'web':
                self.summary_label.setText(format_web_task_summary(urls, self.web_scan_results))
                return
            self.summary_label.setText(build_source_mode_summary(urls, self.source_mode))

        def scan_web_candidates(self):
            if self.source_mode != 'web':
                return
            urls = self.module.parse_task_lines(self.task_edit.toPlainText())
            web_urls = [url for url in urls if _guess_source_kind(url) == 'web']
            if not web_urls:
                show_themed_warning(self, '提示', '请先输入网页链接')
                return
            self.web_scan_results = {}
            self.refresh_summary()
            self.progress_label.setText(f'正在扫描候选 0/{len(web_urls)}')
            self.append_log(f'开始扫描候选，共 {len(web_urls)} 个网页链接')
            self.set_busy(True)
            self.scan_worker = ScanWorker(self.module, web_urls)
            self.scan_worker.progress.connect(self.handle_scan_progress)
            self.scan_worker.finished.connect(self.finalize_scan)
            self.scan_worker.failed.connect(self.handle_scan_error)
            if QThread is None:
                self.scan_worker.run()
                return
            self.scan_worker_thread = QThread(self)
            self.scan_worker.moveToThread(self.scan_worker_thread)
            self.scan_worker_thread.started.connect(self.scan_worker.run)
            self.scan_worker_thread.start()

        def handle_scan_progress(self, message: str):
            parsed = parse_progress_marker(message)
            if parsed is None:
                self.append_log(message)
                return
            kind, payload = parsed
            if kind == 'web_scan_start':
                index = int(payload.get('index', '0') or 0)
                total = int(payload.get('total', '0') or 0)
                url = payload.get('url', '')
                self.progress_label.setText(f'正在扫描候选 {index}/{total}: {url}')
            elif kind == 'web_scan_done':
                index = int(payload.get('index', '0') or 0)
                total = int(payload.get('total', '0') or 0)
                count = int(payload.get('count', '0') or 0)
                url = payload.get('url', '')
                self.append_log(f'候选扫描 {index}/{total}: {count} 个 -> {url}')
                self.progress_label.setText(f'已扫描 {index}/{total}，当前页候选 {count} 个')

        def finalize_scan(self, results: list[dict[str, object]]):
            self.web_scan_results = {str(item.get('source_url') or ''): item for item in results if str(item.get('source_url') or '')}
            self.refresh_summary()
            success_count = sum(1 for item in results if item.get('success'))
            candidate_count = sum(int(item.get('candidate_count', 0) or 0) for item in results if item.get('success'))
            self.append_log(f'候选扫描完成：成功 {success_count} 个链接，找到 {candidate_count} 个候选')
            self.progress_label.setText(f'候选扫描完成，共找到 {candidate_count} 个候选')
            self.cleanup_scan_worker()
            self.set_busy(False)

        def handle_scan_error(self, message: str):
            self.append_log(f'错误：{message}')
            self.progress_label.setText('候选扫描失败')
            self.cleanup_scan_worker()
            self.set_busy(False)
            show_themed_error(self, '候选扫描失败', message)

        def cleanup_scan_worker(self):
            if self.scan_worker_thread is not None:
                self.scan_worker_thread.quit()
                self.scan_worker_thread.wait()
            self.scan_worker_thread = None
            self.scan_worker = None

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择视频输出目录', self.output_edit.text() or str(ROOT))
            if not path:
                return
            self.output_edit.setText(path)
            self.save_form_settings()

        def send_code(self):
            if self.source_mode != 'telegram':
                return
            self.save_form_settings()
            config = self.build_config()
            login_errors: list[str] = []
            if not str(config.api_id).strip():
                login_errors.append('请输入 Telegram API ID')
            if not str(config.api_hash).strip():
                login_errors.append('请输入 Telegram API Hash')
            if not str(config.phone).strip():
                login_errors.append('请输入 Telegram 手机号')
            if login_errors:
                show_themed_warning(self, '提示', '\n'.join(login_errors))
                return
            try:
                result = self.module.begin_telegram_login(config)
                self.phone_code_hash = str(result.get('phone_code_hash', '') or '')
                self.save_form_settings()
                message = str(result.get('message', ''))
                self.login_status_label.setText(message)
                self.append_log(message)
            except Exception as exc:
                self.append_log(f'错误：{exc}')
                show_themed_error(self, '发送验证码失败', str(exc))

        def complete_login(self):
            if self.source_mode != 'telegram':
                return
            self.save_form_settings()
            try:
                result = self.module.complete_telegram_login(self.build_config(), self.code_edit.text().strip(), self.phone_code_hash)
                self.login_status_label.setText(str(result.get('message', 'Telegram 登录成功')))
                self.append_log(str(result.get('message', 'Telegram 登录成功')))
                self.phone_code_hash = ''
                self.code_edit.clear()
                self.save_form_settings()
                show_themed_success(self, '完成', ['Telegram 登录成功'])
            except Exception as exc:
                self.append_log(f'错误：{exc}')
                show_themed_error(self, '登录失败', str(exc))

        def check_login_status(self):
            if self.source_mode != 'telegram':
                return
            self.save_form_settings()
            try:
                result = self.module.check_telegram_authorization(self.build_config())
                message = str(result.get('message', ''))
                self.login_status_label.setText(message)
                self.append_log(message)
            except Exception as exc:
                self.append_log(f'错误：{exc}')
                show_themed_error(self, '状态检查失败', str(exc))

        def embed_thumbnail_clicked(self):
            """Open file dialog to select videos, then embed thumbnail using URL from task area."""
            module = self.module
            # Get source URL from task edit
            urls = module.parse_task_lines(self.task_edit.toPlainText())
            if not urls:
                show_themed_warning(self, '提示', '请先在任务区输入视频源链接')
                return
            source_url = urls[0]
            # Ask for candidate index if user typed one in web_candidate_index_edit
            raw_idx = self._widget_text(self.web_candidate_index_edit) if self.web_candidate_index_edit else ''
            candidate_index = None
            if raw_idx.strip():
                try:
                    candidate_index = int(raw_idx.strip())
                except ValueError:
                    pass
            # Select video files - remember last used directory
            start_dir = self._last_cover_dir or self._widget_text(self.output_edit) or ''
            files, _ = QFileDialog.getOpenFileNames(self, '选择要补封面的视频', start_dir, '视频文件 (*.mp4 *.mkv *.webm *.mov)')
            if not files:
                return
            # Save directory for next time
            self._last_cover_dir = str(Path(files[0]).parent)
            save_setting(self.settings, self._mode_setting_key('cover_dir'), self._last_cover_dir)
            self.set_busy(True)
            self.log.clear()
            self.append_log(f'补封面: 共 {len(files)} 个文件，源链接: {source_url}')
            self.reset_progress_ui(len(files))
            self.thumbnail_worker = ThumbnailWorker(module, files, source_url, candidate_index=candidate_index)
            self.thumbnail_worker.progress.connect(self.handle_thumbnail_progress)
            self.thumbnail_worker.finished.connect(self.finalize_thumbnail)
            self.thumbnail_worker.failed.connect(self.handle_thumbnail_error)
            if QThread is None:
                self.thumbnail_worker.run()
                return
            self.thumbnail_worker_thread = QThread(self)
            self.thumbnail_worker.moveToThread(self.thumbnail_worker_thread)
            self.thumbnail_worker_thread.started.connect(self.thumbnail_worker.run)
            self.thumbnail_worker_thread.start()

        def handle_thumbnail_progress(self, message: str):
            self.append_log(message)
            # Update progress bar based on "补封面 N/M" pattern
            if message.startswith('补封面 ') and '/' in message:
                try:
                    parts = message.split(' ')[1].split('/')
                    current = int(parts[0])
                    total = int(parts[1])
                    self.progress_bar.setValue(int((current - 1) / total * 100))
                    self.progress_label.setText(message)
                except (ValueError, IndexError):
                    pass

        def finalize_thumbnail(self, results: list[dict[str, object]]):
            self.progress_bar.setValue(100)
            success_count = sum(1 for r in results if r.get('success'))
            fail_count = len(results) - success_count
            for r in results:
                name = Path(r.get('_path', '')).name
                if r.get('success'):
                    self.append_log(f'  ✓ {name}')
                else:
                    self.append_log(f'  ✗ {name}: {r.get("error")}')
            self.progress_label.setText(f'补封面完成: 成功 {success_count}, 失败 {fail_count}')
            self.append_log(f'----\n补封面完成: 成功 {success_count}, 失败 {fail_count}')
            show_themed_success(self, '完成', [f'成功: {success_count}', f'失败: {fail_count}'])
            self.cleanup_thumbnail_worker()
            self.set_busy(False)

        def handle_thumbnail_error(self, message: str):
            self.append_log(f'错误：{message}')
            self.progress_label.setText('补封面失败')
            self.cleanup_thumbnail_worker()
            self.set_busy(False)
            show_themed_error(self, '补封面失败', message)

        def cleanup_thumbnail_worker(self):
            if self.thumbnail_worker_thread is not None:
                self.thumbnail_worker_thread.quit()
                self.thumbnail_worker_thread.wait()
            self.thumbnail_worker_thread = None
            self.thumbnail_worker = None

        def run_download(self):
            self.save_form_settings()
            module = self.module
            web_all_candidates = self._is_checked(self.web_all_candidates_checkbox)
            web_candidate_text = '' if web_all_candidates else self._widget_text(self.web_candidate_index_edit)
            errors = validate_video_downloader_form(
                self.task_edit.toPlainText(),
                self.output_edit.text().strip(),
                self._widget_text(self.api_id_edit),
                self._widget_text(self.api_hash_edit),
                self._widget_text(self.phone_edit),
                self._widget_text(self.recent_count_edit),
                download_all_messages=self._is_checked(self.all_messages_checkbox),
                date_from=self._widget_text(self.date_from_edit),
                date_to=self._widget_text(self.date_to_edit),
                telegram_include_videos=self._is_checked(self.include_video_checkbox) or self.source_mode != 'telegram',
                telegram_include_photos=self._is_checked(self.include_photo_checkbox),
                web_candidate_index=web_candidate_text,
                web_download_all_candidates=web_all_candidates,
                source_mode=self.source_mode,
                module=module,
            )
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return

            tasks = filter_tasks_for_source_mode(
                module.build_download_tasks(module.parse_task_lines(self.task_edit.toPlainText())),
                self.source_mode,
            )
            options = module.DownloadOptions(
                overwrite=self.overwrite_checkbox.isChecked(),
                max_concurrent_downloads=int(self._concurrent_value()) if self.concurrent_combo is not None else 1,
                telegram_recent_limit=module.normalize_recent_limit(
                    self._widget_text(self.recent_count_edit),
                    default=int(DEFAULT_RECENT_LIMIT),
                ),
                telegram_download_all_messages=self._is_checked(self.all_messages_checkbox),
                telegram_date_from=module.parse_iso_date(self._widget_text(self.date_from_edit), '开始日期'),
                telegram_date_to=module.parse_iso_date(self._widget_text(self.date_to_edit), '结束日期'),
                telegram_include_videos=self._is_checked(self.include_video_checkbox) or self.source_mode != 'telegram',
                telegram_include_photos=self._is_checked(self.include_photo_checkbox),
                web_candidate_indices=module.normalize_positive_indices(web_candidate_text, '网页候选序号'),
                web_candidate_mode=self._resolve_candidate_mode(),
                web_download_all_candidates=web_all_candidates,
            )
            if web_all_candidates:
                options = replace(options, web_candidate_indices=None)
            self.set_busy(True)
            self.log.clear()
            self._last_log_is_progress = False
            if options.web_download_all_candidates:
                tasks = module._expand_web_all_candidates(tasks, self.append_log)
            self.reset_progress_ui(len(tasks))
            self._token = module.Token()
            self.worker = DownloadWorker(module, tasks, self.output_edit.text().strip(), self.build_config(), options, token=self._token)
            self.worker.progress.connect(self.handle_worker_progress)
            self.worker.finished.connect(self.finalize_download)
            self.worker.failed.connect(self.handle_worker_error)
            self.worker.cancelled.connect(self.handle_download_cancelled)
            if QThread is None:
                self.worker.run()
                return
            self.worker_thread = QThread(self)
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.start()

    return VideoDownloaderTab
