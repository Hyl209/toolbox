from __future__ import annotations

from .tab_constants import (
    DEFAULT_RECENT_LIMIT, DATE_FROM_PLACEHOLDER, DATE_TO_PLACEHOLDER,
    WEB_INDEX_PLACEHOLDER, OUTPUT_PLACEHOLDER, SUMMARY_EMPTY_TEXT,
    RUN_BUTTON_TEXT, SEND_CODE_BUTTON_TEXT, LOGIN_BUTTON_TEXT, STATUS_BUTTON_TEXT,
    apply_video_textedit_surface, compact_card_layout,
)


def build_root_container(self, deps):
    QVBoxLayout = deps['QVBoxLayout']
    QWidget = deps['QWidget']
    QScrollArea = deps['QScrollArea']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    make_card = deps['make_card']

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
    return card, layout, card_root


def build_telegram_login_section(self, layout, deps):
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    load_setting = deps['load_setting']
    QLabel = deps['QLabel']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QHBoxLayout = deps['QHBoxLayout']

    settings = self.settings
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
    self.phone_edit.setPlaceholderText('+861****0000')
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


def build_task_section(self, layout, center_row, textedit_style, task_min_height, deps):
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    load_setting = deps['load_setting']
    style_combo_popup = deps['style_combo_popup']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QHBoxLayout = deps['QHBoxLayout']
    QCheckBox = deps['QCheckBox']
    QComboBox = deps['QComboBox']

    settings = self.settings
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
    self.cover_button = QPushButton('补封面')
    self.cover_button.setToolTip('给已下载的视频嵌入封面（需提供源链接）')
    self.cover_button.clicked.connect(self.embed_thumbnail_clicked)
    action_row.addWidget(self.cover_button)
    action_row.addStretch(1)
    self.run_button = QPushButton(RUN_BUTTON_TEXT)
    self.run_button.clicked.connect(self.run_download)
    action_row.addWidget(self.run_button)
    self.pause_button = QPushButton('暂停')
    self.pause_button.clicked.connect(self.toggle_pause)
    self.pause_button.setVisible(False)
    action_row.addWidget(self.pause_button)
    self.cancel_button = QPushButton('取消')
    self.cancel_button.clicked.connect(self.cancel_download)
    self.cancel_button.setVisible(False)
    action_row.addWidget(self.cancel_button)
    self.reconnect_button = QPushButton('重连')
    self.reconnect_button.clicked.connect(self.reconnect_download)
    self.reconnect_button.setVisible(False)
    action_row.addWidget(self.reconnect_button)
    task_layout.addLayout(action_row)
    if self.source_mode == 'web':
        layout.addWidget(task_card, 1)
    else:
        center_row.addWidget(task_card, 3)


def build_telegram_options_section(self, center_row, deps):
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    load_setting = deps['load_setting']
    QLabel = deps['QLabel']
    QLineEdit = deps['QLineEdit']
    QCheckBox = deps['QCheckBox']

    settings = self.settings
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


def build_web_options_section(self, layout, deps):
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    load_setting = deps['load_setting']
    QLineEdit = deps['QLineEdit']
    QCheckBox = deps['QCheckBox']

    settings = self.settings
    web_card, web_layout = make_card('选项')
    compact_card_layout(web_layout)
    web_row_widget, web_row = make_transparent_row()
    web_row.setSpacing(10)
    self.web_candidate_index_edit = QLineEdit(load_setting(settings, self._mode_setting_key('web_candidate_index')))
    self.web_candidate_index_edit.setPlaceholderText(WEB_INDEX_PLACEHOLDER)
    self.web_candidate_index_edit.setMaximumWidth(160)
    self.web_candidate_index_edit.editingFinished.connect(self.save_form_settings)
    web_row.addWidget(self.web_candidate_index_edit)
    self.web_candidate_exclude_checkbox = QCheckBox('跳过')
    self.web_candidate_exclude_checkbox.setChecked(load_setting(settings, self._mode_setting_key('web_candidate_exclude'), '0') == '1')
    self.web_candidate_exclude_checkbox.clicked.connect(self.handle_exclude_checked)
    web_row.addWidget(self.web_candidate_exclude_checkbox)
    self.web_candidate_before_checkbox = QCheckBox('之前')
    self.web_candidate_before_checkbox.setChecked(load_setting(settings, self._mode_setting_key('web_candidate_before'), '0') == '1')
    self.web_candidate_before_checkbox.clicked.connect(self.handle_before_checked)
    web_row.addWidget(self.web_candidate_before_checkbox)
    self.web_candidate_after_checkbox = QCheckBox('之后')
    self.web_candidate_after_checkbox.setChecked(load_setting(settings, self._mode_setting_key('web_candidate_after'), '0') == '1')
    self.web_candidate_after_checkbox.clicked.connect(self.handle_after_checked)
    web_row.addWidget(self.web_candidate_after_checkbox)
    self.web_all_candidates_checkbox = QCheckBox('全部候选')
    self.web_all_candidates_checkbox.setChecked(load_setting(settings, self._mode_setting_key('web_all_candidates'), '0') == '1')
    self.web_all_candidates_checkbox.clicked.connect(self.handle_web_all_candidates_changed)
    web_row.addWidget(self.web_all_candidates_checkbox)
    web_row.addStretch(1)
    web_layout.addWidget(web_row_widget)
    layout.addWidget(web_card, 1)


def build_log_section(self, layout, center_row, textedit_style, log_min_height, deps):
    make_card = deps['make_card']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']

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

    self.task_counter_label = QLabel('')
    self.task_counter_label.setProperty('cardSub', True)
    log_layout.addWidget(self.task_counter_label)

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
