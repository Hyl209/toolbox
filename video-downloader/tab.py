from __future__ import annotations

from pathlib import Path


SETTINGS_PREFIX = 'video_downloader'
TITLE = '视频下载'
SUBTITLE = '批量下载 Telegram 和网页视频'
TASK_PLACEHOLDER = '每行一个链接'
OUTPUT_PLACEHOLDER = '选择输出文件夹'
DEFAULT_RECENT_LIMIT = '500'
DATE_FROM_PLACEHOLDER = '开始日期 YYYY-MM-DD'
DATE_TO_PLACEHOLDER = '结束日期 YYYY-MM-DD'
WEB_INDEX_PLACEHOLDER = '候选序号，如 3 或 3,4,6，留空则自动'
SUMMARY_EMPTY_TEXT = '请先输入下载链接'
RUN_BUTTON_TEXT = '开始下载'
RUNNING_BUTTON_TEXT = '下载中...'
SEND_CODE_BUTTON_TEXT = '发送验证码'
LOGIN_BUTTON_TEXT = '完成登录'
STATUS_BUTTON_TEXT = '检查状态'
TELEGRAM_ONLY_ERROR = '\u5f53\u524d\u9875\u4ec5\u652f\u6301 Telegram \u94fe\u63a5\uff0c\u8bf7\u79fb\u5230\u201c\u7f51\u9875\u89c6\u9891\u4e0b\u8f7d\u201d\u9875\u7b7e\u5904\u7406\u7f51\u9875\u94fe\u63a5'
WEB_ONLY_ERROR = '\u5f53\u524d\u9875\u4ec5\u652f\u6301\u7f51\u9875\u89c6\u9891\u94fe\u63a5\uff0c\u8bf7\u79fb\u5230\u201cTG\u4e0b\u8f7d\u201d\u9875\u7b7e\u5904\u7406 Telegram \u94fe\u63a5'

MODE_META = {
    'mixed': {
        'title': TITLE,
        'subtitle': SUBTITLE,
        'task_placeholder': TASK_PLACEHOLDER,
    },
    'telegram': {
        'title': 'Telegram 下载',
        'subtitle': '批量下载 Telegram 消息、群组和频道中的媒体',
        'task_placeholder': '每行一个 Telegram 链接',
    },
    'web': {
        'title': '网页视频下载',
        'subtitle': '',
        'task_placeholder': '每行一个网页视频链接',
    },
}


def build_video_textedit_style(build_global_scrollbar_style, theme_name: str) -> str:
    if theme_name == 'light':
        background = 'rgba(255, 255, 255, 0.76)'
        border = '#d8dee6'
        focus_border = '#8fb4e8'
        color = '#1f252d'
        selection = '#d4e4ff'
    else:
        background = 'rgba(44, 50, 59, 0.88)'
        border = '#46505c'
        focus_border = '#7ea6d9'
        color = '#eef2f7'
        selection = '#6d94c8'
    return (
        build_global_scrollbar_style()
        + f'QPlainTextEdit {{background-color: {background}; border: 1px solid {border}; '
        + f'border-radius: 16px; padding: 12px 14px; color: {color}; selection-background-color: {selection};}} '
        + f'QPlainTextEdit:focus {{background-color: {background}; border: 1px solid {focus_border};}}'
    )


def apply_video_textedit_surface(widget, style: str, theme_name: str) -> None:
    background = 'rgba(255, 255, 255, 0.76)' if theme_name == 'light' else 'rgba(44, 50, 59, 0.88)'
    widget.setStyleSheet(style)
    if hasattr(widget, 'viewport') and widget.viewport() is not None:
        widget.viewport().setAutoFillBackground(False)
        widget.viewport().setStyleSheet(f'background-color: {background};')


def make_panel_transparent(widget) -> None:
    widget.setStyleSheet('background: transparent;')


def compact_card_layout(layout, margin: int = 18, spacing: int = 12) -> None:
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(spacing)


def normalize_source_mode(source_mode: str) -> str:
    cleaned = str(source_mode or '').strip().lower()
    return cleaned if cleaned in {'mixed', 'telegram', 'web'} else 'mixed'


def build_source_mode_summary(urls: list[str], source_mode: str, web_scan_results: dict[str, dict[str, object]] | None = None) -> str:
    mode = normalize_source_mode(source_mode)
    if not urls or mode == 'mixed':
        return format_video_task_summary(urls)
    if mode == 'telegram':
        summary = format_video_task_summary(urls)
        mismatched = [url for url in urls if _guess_source_kind(url) == 'web']
        if mismatched:
            return summary + f'当前页不匹配链接'
        return summary
    web_urls = [url for url in urls if _guess_source_kind(url) == 'web']
    mismatched = [url for url in urls if _guess_source_kind(url) != 'web']
    if mismatched:
        return format_web_task_summary(web_urls) + f'当前页不匹配链接'
    return format_web_task_summary(web_urls)


def validate_source_mode_urls(urls: list[str], source_mode: str) -> list[str]:
    mode = normalize_source_mode(source_mode)
    if mode == 'mixed' or not urls:
        return []
    if mode == 'telegram':
        return [TELEGRAM_ONLY_ERROR] if any(_guess_source_kind(url) == 'web' for url in urls) else []
    return [WEB_ONLY_ERROR] if any(_guess_source_kind(url) != 'web' for url in urls) else []


def filter_tasks_for_source_mode(tasks: list[object], source_mode: str) -> list[object]:
    mode = normalize_source_mode(source_mode)
    if mode == 'mixed':
        return tasks
    filtered: list[object] = []
    for task in tasks:
        kind = str(getattr(task, 'source_kind', ''))
        if mode == 'telegram' and kind.startswith('telegram'):
            filtered.append(task)
        elif mode == 'web' and kind == 'web':
            filtered.append(task)
    return filtered


def format_video_task_summary(urls: list[str]) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    telegram_message = 0
    telegram_chat = 0
    web = 0
    for url in urls:
        kind = _guess_source_kind(url)
        if kind == 'telegram_message':
            telegram_message += 1
        elif kind == 'telegram_chat':
            telegram_chat += 1
        else:
            web += 1
    lines = [
        f'任务总数: {len(urls)}',
        f'Telegram 消息: {telegram_message}',
        f'Telegram 群/频道: {telegram_chat}',
        f'网页视频任务: {web}',
    ]
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)


def format_web_task_summary(urls: list[str], web_scan_results: dict[str, dict[str, object]] | None = None) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    lines = [f'网页链接: {len(urls)}']
    if web_scan_results:
        lines.append('扫描结果:')
        for url in urls[:3]:
            result = web_scan_results.get(url)
            if not result:
                continue
            if result.get('success'):
                count = int(result.get('candidate_count', 0) or 0)
                lines.append(f'{count} 个候选: {url}')
            else:
                lines.append(f'扫描失败: {url}')
    else:
        lines.append('（未扫描候选）')
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)

def format_video_task_summary(urls: list[str]) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    telegram_message = 0
    telegram_chat = 0
    web = 0
    for url in urls:
        kind = _guess_source_kind(url)
        if kind == 'telegram_message':
            telegram_message += 1
        elif kind == 'telegram_chat':
            telegram_chat += 1
        else:
            web += 1
    lines = [
        f'任务总数: {len(urls)}',
        f'Telegram 消息: {telegram_message}',
        f'Telegram 群/频道: {telegram_chat}',
        f'网页视频任务: {web}',
    ]
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)


def format_web_task_summary(urls: list[str], web_scan_results: dict[str, dict[str, object]] | None = None) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    lines = [f'网页链接: {len(urls)}']
    if web_scan_results:
        lines.append('扫描结果:')
        for url in urls[:3]:
            result = web_scan_results.get(url)
            if not result:
                continue
            if result.get('success'):
                count = int(result.get('candidate_count', 0) or 0)
                lines.append(f'{count} 个候选: {url}')
            else:
                lines.append(f'扫描失败: {url}')
    else:
        lines.append('点击“扫描候选”可查看每个页面的候选视频')
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)

def format_backend_status(status: dict[str, dict[str, object]]) -> str:
    lines: list[str] = []
    for key in ('telethon', 'yt_dlp', 'ffmpeg'):
        item = status.get(key, {})
        available = bool(item.get('available'))
        label = str(item.get('label') or key)
        message = str(item.get('message') or '')
        prefix = '可用' if available else '缺失'
        lines.append(f'{prefix} {label}: {message}')
    return '\n'.join(lines)


def build_progress_marker(kind: str, **values: object) -> str:
    parts = [f'{key}={values[key]}' for key in sorted(values.keys())]
    return '__HYL_PROGRESS__|' + kind + ('|' + '|'.join(parts) if parts else '')


def parse_progress_marker(message: str) -> tuple[str, dict[str, str]] | None:
    text = str(message or '')
    if not text.startswith('__HYL_PROGRESS__|'):
        return None
    parts = text.split('|')
    if len(parts) < 2:
        return None
    kind = parts[1]
    payload: dict[str, str] = {}
    for item in parts[2:]:
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        payload[key] = value
    return kind, payload


def summarize_download_results(results: list[dict[str, object]]) -> list[str]:
    success_count = sum(1 for item in results if item.get('success'))
    failed_count = sum(1 for item in results if not item.get('success'))
    downloaded_count = sum(int(item.get('downloaded_count', 0) or 0) for item in results)
    return [
        f'任务总数: {len(results)}',
        f'成功任务: {success_count}',
        f'失败任务: {failed_count}',
        f'下载文件: {downloaded_count}',
    ]


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
        module.normalize_positive_indices(web_candidate_index, '网页候选序号')
    except ValueError as exc:
        errors.append(str(exc))
    if mode_errors:
        if not (output_dir or '').strip():
            errors.append('请选择输出目录')
        if web_download_all_candidates and str(web_candidate_index).strip():
            errors.append('勾选"网页全部候选"时，不需要再填写候选序号')
        return errors
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
    if web_download_all_candidates and str(web_candidate_index).strip():
        errors.append('勾选"网页全部候选"时，不需要再填写候选序号')
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

    class _FallbackSignal:
        def __init__(self):
            self._callbacks: list[object] = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for callback in list(self._callbacks):
                callback(*args)

    if QObject is not None and Signal is not None:
        class DownloadWorker(QObject):
            progress = Signal(str)
            finished = Signal(list)
            failed = Signal(str)

            def __init__(self, module, tasks, output_dir, telegram_config, options):
                super().__init__()
                self.module = module
                self.tasks = tasks
                self.output_dir = output_dir
                self.telegram_config = telegram_config
                self.options = options

            def run(self):
                try:
                    results = self.module.download_batch(
                        self.tasks,
                        self.output_dir,
                        self.telegram_config,
                        self.options,
                        progress_cb=self.progress.emit,
                    )
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ScanWorker(QObject):
            progress = Signal(str)
            finished = Signal(list)
            failed = Signal(str)

            def __init__(self, module, urls):
                super().__init__()
                self.module = module
                self.urls = urls

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))
    else:
        class DownloadWorker:
            def __init__(self, module, tasks, output_dir, telegram_config, options):
                self.module = module
                self.tasks = tasks
                self.output_dir = output_dir
                self.telegram_config = telegram_config
                self.options = options
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    results = self.module.download_batch(
                        self.tasks,
                        self.output_dir,
                        self.telegram_config,
                        self.options,
                        progress_cb=self.progress.emit,
                    )
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ScanWorker:
            def __init__(self, module, urls):
                self.module = module
                self.urls = urls
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

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
            self.scan_worker_thread = None
            self.scan_worker = None
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
            self.web_all_candidates_checkbox = None
            self.concurrent_combo = None
            self.scan_button = None
            self.web_scan_results: dict[str, dict[str, object]] = {}
            self.phone_code_hash = load_setting(settings, self._shared_setting_key('phone_code_hash'))
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.current_task_index = -1
            self.total_tasks = 0
            self.completed_tasks = 0
            self.module = get_video_downloader_module()
            self.session_file = VIDEO_DOWNLOADER_DIR / self.module.SESSION_FILE_NAME
            textedit_style = build_video_textedit_style(build_global_scrollbar_style, self.current_theme)
            task_min_height = 110 if self.source_mode == 'web' else 150
            log_min_height = 110 if self.source_mode == 'web' else 150

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

            card_root = QVBoxLayout(content_host)
            card_root.setContentsMargins(0, 0, 0, 0)
            card_root.setSpacing(0)
            card, layout = make_card(self.mode_meta['title'], self.mode_meta['subtitle'])

            if self.source_mode == 'telegram':
                status_card, status_layout = make_card('运行状态')
                compact_card_layout(status_layout)

                backend_title = QLabel('依赖状态')
                status_layout.addWidget(backend_title)
                self.login_status_label = QLabel('尚未检查 Telegram 登录状态')
                self.login_status_label.setProperty('cardSub', True)
                self.login_status_label.setWordWrap(True)
                self.login_status_label.setMinimumWidth(220)

                self.backend_status_label = QLabel('')
                self.backend_status_label.setProperty('cardSub', True)
                self.backend_status_label.setWordWrap(True)
                self.backend_status_label.setMinimumWidth(260)
                status_layout.addWidget(self.backend_status_label)

                status_title = QLabel('登录状态')
                status_layout.addWidget(status_title)
                status_layout.addWidget(self.login_status_label)
                self.refresh_status_button = QPushButton('刷新依赖状态')
                self.refresh_status_button.clicked.connect(self.refresh_backend_status)
                status_layout.addWidget(self.refresh_status_button)

                top_row_widget, top_row = make_transparent_row()
                top_row.setSpacing(18)

                credential_card, credential_layout = make_card('Telegram 登录')
                compact_card_layout(credential_layout)

                row1 = QHBoxLayout()
                row1.setSpacing(10)
                row1.addWidget(QLabel('API ID'))
                self.api_id_edit = QLineEdit(load_setting(settings, self._shared_setting_key('api_id')))
                row1.addWidget(self.api_id_edit)
                row1.addWidget(QLabel('API Hash'))
                self.api_hash_edit = QLineEdit(load_setting(settings, self._shared_setting_key('api_hash')))
                row1.addWidget(self.api_hash_edit)
                credential_layout.addLayout(row1)

                row2 = QHBoxLayout()
                row2.setSpacing(10)
                row2.addWidget(QLabel('手机号'))
                self.phone_edit = QLineEdit(load_setting(settings, self._shared_setting_key('phone')))
                self.phone_edit.setPlaceholderText('+8613800000000')
                row2.addWidget(self.phone_edit)
                row2.addWidget(QLabel('验证码'))
                self.code_edit = QLineEdit('')
                self.code_edit.setPlaceholderText('发送验证码后输入')
                row2.addWidget(self.code_edit)
                credential_layout.addLayout(row2)

                login_button_row = QHBoxLayout()
                login_button_row.setSpacing(10)
                self.send_code_button = QPushButton(SEND_CODE_BUTTON_TEXT)
                self.send_code_button.clicked.connect(self.send_code)
                login_button_row.addWidget(self.send_code_button)
                self.login_button = QPushButton(LOGIN_BUTTON_TEXT)
                self.login_button.clicked.connect(self.complete_login)
                login_button_row.addWidget(self.login_button)
                self.check_status_button = QPushButton(STATUS_BUTTON_TEXT)
                self.check_status_button.clicked.connect(self.check_login_status)
                login_button_row.addWidget(self.check_status_button)
                login_button_row.addStretch(1)
                credential_layout.addLayout(login_button_row)

                top_row.addWidget(credential_card, 3)
                top_row.addWidget(status_card, 2)
                layout.addWidget(top_row_widget)

            center_row = None
            if self.source_mode != 'web':
                center_row = QHBoxLayout()
                center_row.setSpacing(18)

            task_card_title = '链接' if self.source_mode == 'web' else '下载任务'
            task_card, task_layout = make_card(task_card_title)
            compact_card_layout(task_layout)
            if self.source_mode != 'web':
                task_layout.addWidget(QLabel('任务链接'))
            self.task_edit = QPlainTextEdit()
            self.task_edit.setPlaceholderText(self.mode_meta['task_placeholder'])
            self.task_edit.setMinimumHeight(task_min_height)
            apply_video_textedit_surface(self.task_edit, textedit_style, self.current_theme)
            self.task_edit.textChanged.connect(self.handle_task_text_changed)
            task_layout.addWidget(self.task_edit)

            self.summary_label = QLabel(SUMMARY_EMPTY_TEXT)
            self.summary_label.setProperty('cardSub', True)
            self.summary_label.setWordWrap(True)
            task_layout.addWidget(self.summary_label)

            output_row = QHBoxLayout()
            output_row.setSpacing(10)
            self.output_edit = QLineEdit(load_setting(settings, self._mode_setting_key('output_dir')))
            self.output_edit.setPlaceholderText(OUTPUT_PLACEHOLDER)
            self.output_edit.editingFinished.connect(self.save_form_settings)
            self.choose_button = QPushButton('选择路径')
            self.choose_button.clicked.connect(self.choose_output_dir)
            output_row.addWidget(self.output_edit)
            output_row.addWidget(self.choose_button)
            task_layout.addLayout(output_row)

            common_row_widget, common_row = make_transparent_row()
            common_row.setSpacing(10)
            self.overwrite_checkbox = QCheckBox('覆盖同名文件')
            self.overwrite_checkbox.setChecked(load_setting(settings, self._mode_setting_key('overwrite'), '0') == '1')
            self.overwrite_checkbox.clicked.connect(self.save_form_settings)
            common_row.addWidget(self.overwrite_checkbox)
            common_row.addWidget(QLabel('同时下载'))
            self.concurrent_combo = QComboBox()
            self.concurrent_combo.addItems(['自动', '1', '2', '3', '4', '5'])
            saved_concurrent = load_setting(settings, self._mode_setting_key('concurrent'), '1')
            if saved_concurrent == '0':
                saved_index = 0
            else:
                saved_index = max(1, min(5, int(saved_concurrent or '1')))
            self.concurrent_combo.setCurrentIndex(saved_index)
            self.concurrent_combo.setMaximumWidth(72)
            self.concurrent_combo.currentIndexChanged.connect(self.save_form_settings)
            style_combo_popup(self.concurrent_combo, self.current_theme)
            common_row.addWidget(self.concurrent_combo)
            common_row.addStretch(1)
            task_layout.addWidget(common_row_widget)

            action_row = QHBoxLayout()
            action_row.setSpacing(10)
            if self.source_mode == 'web':
                self.scan_button = QPushButton('扫描候选')
                self.scan_button.clicked.connect(self.scan_web_candidates)
                action_row.addWidget(self.scan_button)
            action_row.addStretch(1)
            self.run_button = QPushButton(RUN_BUTTON_TEXT)
            self.run_button.clicked.connect(self.run_download)
            action_row.addWidget(self.run_button)
            task_layout.addLayout(action_row)
            if self.source_mode == 'web':
                layout.addWidget(task_card, 1)
            else:
                center_row.addWidget(task_card, 3)

            if self.source_mode == 'telegram':
                telegram_card, telegram_layout = make_card('下载')
                compact_card_layout(telegram_layout)

                option_row_widget, option_row = make_transparent_row()
                option_row.setSpacing(10)
                option_row.addWidget(QLabel('最近消息条数'))
                self.recent_count_edit = QLineEdit(load_setting(settings, self._mode_setting_key('recent_limit'), DEFAULT_RECENT_LIMIT))
                self.recent_count_edit.setPlaceholderText(DEFAULT_RECENT_LIMIT)
                self.recent_count_edit.setMaximumWidth(92)
                self.recent_count_edit.editingFinished.connect(self.save_form_settings)
                option_row.addWidget(self.recent_count_edit)
                self.all_messages_checkbox = QCheckBox('全部消息')
                self.all_messages_checkbox.setChecked(load_setting(settings, self._mode_setting_key('all_messages'), '0') == '1')
                self.all_messages_checkbox.clicked.connect(self.handle_all_messages_changed)
                option_row.addWidget(self.all_messages_checkbox)
                option_row.addStretch(1)
                telegram_layout.addWidget(option_row_widget)

                date_row_widget, date_row = make_transparent_row()
                date_row.setSpacing(10)
                date_row.addWidget(QLabel('日期范围'))
                self.date_from_edit = QLineEdit(load_setting(settings, self._mode_setting_key('date_from')))
                self.date_from_edit.setPlaceholderText(DATE_FROM_PLACEHOLDER)
                self.date_from_edit.editingFinished.connect(self.save_form_settings)
                date_row.addWidget(self.date_from_edit)
                date_row.addWidget(QLabel('至'))
                self.date_to_edit = QLineEdit(load_setting(settings, self._mode_setting_key('date_to')))
                self.date_to_edit.setPlaceholderText(DATE_TO_PLACEHOLDER)
                self.date_to_edit.editingFinished.connect(self.save_form_settings)
                date_row.addWidget(self.date_to_edit)
                telegram_layout.addWidget(date_row_widget)

                media_row_widget, media_row = make_transparent_row()
                media_row.setSpacing(10)
                media_row.addWidget(QLabel('下载类型'))
                self.include_video_checkbox = QCheckBox('视频')
                self.include_video_checkbox.setChecked(load_setting(settings, self._mode_setting_key('include_videos'), '1') != '0')
                self.include_video_checkbox.clicked.connect(self.save_form_settings)
                media_row.addWidget(self.include_video_checkbox)
                self.include_photo_checkbox = QCheckBox('图片')
                self.include_photo_checkbox.setChecked(load_setting(settings, self._mode_setting_key('include_photos'), '0') == '1')
                self.include_photo_checkbox.clicked.connect(self.save_form_settings)
                media_row.addWidget(self.include_photo_checkbox)
                media_row.addStretch(1)
                telegram_layout.addWidget(media_row_widget)
                center_row.addWidget(telegram_card, 2)
            elif self.source_mode == 'web':
                web_card, web_layout = make_card('选项')
                compact_card_layout(web_layout)
                web_row_widget, web_row = make_transparent_row()
                web_row.setSpacing(10)
                self.web_candidate_index_edit = QLineEdit(load_setting(settings, self._mode_setting_key('web_candidate_index')))
                self.web_candidate_index_edit.setPlaceholderText(WEB_INDEX_PLACEHOLDER)
                self.web_candidate_index_edit.setMaximumWidth(180)
                self.web_candidate_index_edit.editingFinished.connect(self.save_form_settings)
                web_row.addWidget(self.web_candidate_index_edit)
                self.web_all_candidates_checkbox = QCheckBox('网页全部候选')
                self.web_all_candidates_checkbox.setChecked(load_setting(settings, self._mode_setting_key('web_all_candidates'), '0') == '1')
                self.web_all_candidates_checkbox.clicked.connect(self.handle_web_all_candidates_changed)
                web_row.addWidget(self.web_all_candidates_checkbox)
                web_row.addStretch(1)
                web_layout.addWidget(web_row_widget)
                layout.addWidget(web_card, 1)

            log_card_title = '日志' if self.source_mode == 'web' else '运行日志'
            log_card, log_layout = make_card(log_card_title)
            compact_card_layout(log_layout)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(log_min_height)
            apply_video_textedit_surface(self.log, textedit_style, self.current_theme)
            log_layout.addWidget(self.log)

            self.progress_label = QLabel('等待开始')
            self.progress_label.setProperty('cardSub', True)
            self.progress_label.setWordWrap(True)
            log_layout.addWidget(self.progress_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            log_layout.addWidget(self.progress_bar)
            if self.source_mode == 'web':
                layout.addWidget(log_card, 1)
            else:
                center_row.addWidget(log_card, 2)
                layout.addLayout(center_row)

            card_root.addWidget(card)
            if self.recent_count_edit is not None:
                self.handle_all_messages_changed()
            if self.web_candidate_index_edit is not None:
                self.handle_web_all_candidates_changed()
            self.refresh_backend_status()
            self.refresh_summary()

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
                save_setting(self.settings, self._mode_setting_key('web_all_candidates'), '1' if self._is_checked(self.web_all_candidates_checkbox) else '0')
            save_setting(self.settings, self._mode_setting_key('overwrite'), '1' if self._is_checked(self.overwrite_checkbox) else '0')
            save_setting(self.settings, self._mode_setting_key('concurrent'), self._concurrent_value() if self.concurrent_combo is not None else '1')
            save_setting(self.settings, self._shared_setting_key('phone_code_hash'), self.phone_code_hash)

        def append_log(self, text: str):
            if not text:
                return
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
                self.web_all_candidates_checkbox,
                self.output_edit,
                self.overwrite_checkbox,
                self.concurrent_combo,
                self.choose_button,
                self.scan_button,
                self.send_code_button,
                self.login_button,
                self.check_status_button,
                self.refresh_status_button,
            ]
            for widget in widgets:
                if widget is not None:
                    widget.setEnabled(not busy)
            self.run_button.setEnabled(not busy)
            self.run_button.setText(RUNNING_BUTTON_TEXT if busy else RUN_BUTTON_TEXT)
            if QApplication is not None:
                QApplication.processEvents()

        def handle_all_messages_changed(self):
            if self.recent_count_edit is None or self.all_messages_checkbox is None:
                return
            self.recent_count_edit.setEnabled(not self.all_messages_checkbox.isChecked())
            self.save_form_settings()

        def handle_web_all_candidates_changed(self):
            if self.web_candidate_index_edit is None or self.web_all_candidates_checkbox is None:
                return
            self.web_candidate_index_edit.setEnabled(not self.web_all_candidates_checkbox.isChecked())
            self.save_form_settings()

        def reset_progress_ui(self, total_tasks: int):
            self.total_tasks = max(0, total_tasks)
            self.completed_tasks = 0
            self.current_task_index = -1
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_label.setText(f'准备开始，共 {self.total_tasks} 个任务')

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
                elif kind == 'task_done':
                    self.completed_tasks = int(payload.get('completed', str(self.completed_tasks)) or self.completed_tasks)
                    self.total_tasks = int(payload.get('total', str(self.total_tasks)) or self.total_tasks or 0)
                    self.update_progress_percent(0)
                    self.progress_label.setText(f'已完成 {self.completed_tasks}/{self.total_tasks} 个任务')
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
                    self.update_progress_percent(float(payload.get('percent', '0') or 0))
                elif kind in {'web_status', 'tg_media'}:
                    percent = float(payload.get('percent', '0') or 0)
                    self.update_progress_percent(percent)
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

        def run_download(self):
            self.save_form_settings()
            module = self.module
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
                web_candidate_index=self._widget_text(self.web_candidate_index_edit),
                web_download_all_candidates=self._is_checked(self.web_all_candidates_checkbox),
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
                web_candidate_indices=module.normalize_positive_indices(self._widget_text(self.web_candidate_index_edit), '网页候选序号'),
                web_download_all_candidates=self._is_checked(self.web_all_candidates_checkbox),
            )
            self.set_busy(True)
            self.log.clear()
            self.reset_progress_ui(len(tasks))
            self.worker = DownloadWorker(module, tasks, self.output_edit.text().strip(), self.build_config(), options)
            self.worker.progress.connect(self.handle_worker_progress)
            self.worker.finished.connect(self.finalize_download)
            self.worker.failed.connect(self.handle_worker_error)
            if QThread is None:
                self.worker.run()
                return
            self.worker_thread = QThread(self)
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.start()

    return VideoDownloaderTab


def _guess_source_kind(url: str) -> str:
    text = str(url or '').strip().lower()
    if 't.me/' not in text and 'telegram.me/' not in text and 'telegram.dog/' not in text:
        return 'web'
    parts = [part for part in text.split('://', 1)[-1].split('/', 1)[-1].split('/') if part]
    if not parts:
        return 'telegram_chat'
    if parts[0] == 'c' and len(parts) >= 3 and parts[2].isdigit():
        return 'telegram_message'
    if len(parts) >= 2 and parts[1].isdigit():
        return 'telegram_message'
    return 'telegram_chat'
