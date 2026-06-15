from __future__ import annotations

import re
from urllib.parse import urlparse

from .tab_constants import (
    DEFAULT_RECENT_LIMIT, DATE_FROM_PLACEHOLDER, DATE_TO_PLACEHOLDER,
    WEB_SOURCE_PLACEHOLDER, OUTPUT_PLACEHOLDER, SUMMARY_EMPTY_TEXT,
    RUN_BUTTON_TEXT, SEND_CODE_BUTTON_TEXT, LOGIN_BUTTON_TEXT, STATUS_BUTTON_TEXT,
    apply_video_textedit_surface, compact_card_layout,
)
from .tab_formatters import build_web_queue_tasks, parse_web_queue_entry, format_web_queue_line


def _compact_task_path(url):
    parsed = urlparse(str(url or ''))
    path = (parsed.path or '').strip('/')
    if not path:
        return '/'
    parts = [part for part in path.split('/') if part]
    compact = '/'.join(parts[-2:]) if len(parts) > 1 else parts[0]
    return compact if len(compact) <= 46 else compact[:43] + '...'


def _task_url_meta(url):
    parsed = urlparse(str(url or ''))
    host = parsed.netloc or parsed.path.split('/')[0] or 'unknown source'
    scheme = (parsed.scheme or 'link').upper()
    return host, scheme, _compact_task_path(url)


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
    QWidget = deps['QWidget']

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

    # Collapsible credential section
    self._login_collapsed = True
    self._login_collapse_button = QPushButton('▸ Telegram 登录')
    self._login_collapse_button.setStyleSheet(
        'QPushButton { border: none; text-align: left; padding: 4px 0; font-weight: bold; }'
        'QPushButton:hover { color: #7ea6d9; }'
    )
    self._login_content = QWidget()
    _login_content_layout = QHBoxLayout(self._login_content)
    _login_content_layout.setContentsMargins(0, 0, 0, 0)
    _login_content_layout.setSpacing(18)

    credential_card, credential_layout = make_card('凭据')
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

    _login_content_layout.addWidget(credential_card, 3)
    _login_content_layout.addWidget(status_card, 2)
    self._login_content.setVisible(False)

    def _toggle_login():
        self._login_collapsed = not self._login_collapsed
        self._login_content.setVisible(not self._login_collapsed)
        self._login_collapse_button.setText('▾ Telegram 登录' if not self._login_collapsed else '▸ Telegram 登录')

    self._login_collapse_button.clicked.connect(_toggle_login)
    layout.addWidget(self._login_collapse_button)
    layout.addWidget(self._login_content)


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
    compact_card_layout(task_layout, 16 if self.source_mode == 'web' else 18, 10 if self.source_mode == 'web' else 12)
    if self.source_mode == 'web':
        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText(WEB_SOURCE_PLACEHOLDER)
        self.source_edit.setMinimumHeight(120)
        self.source_edit.setMaximumHeight(160)
        apply_video_textedit_surface(self.source_edit, textedit_style, self.current_theme)
        self.source_edit.textChanged.connect(self.handle_web_source_text_changed)
        task_layout.addWidget(QLabel('网页链接'))
        task_layout.addWidget(self.source_edit)

        # -- WebTaskListWidget: interactive task list with hover highlight and × delete --
        QListWidget = deps['QListWidget']
        QListWidgetItem = deps['QListWidgetItem']
        QFrame = deps.get('QFrame')
        Signal = deps.get('Signal')

        _current_theme = self.current_theme
        class _TaskEntryWidget(QFrame):
            def __init__(self, index, title, url, on_delete, on_rename):
                super().__init__()
                self._on_rename = on_rename
                self._btn_w = 32
                self._entry_bg = ''
                self._entry_hover_bg = ''
                self._entry_border = ''
                self.setAttribute(deps['Qt'].WA_Hover) if 'Qt' in deps else None
                lay = deps['QHBoxLayout'](self)
                lay.setContentsMargins(12, 10, 8, 10)
                lay.setSpacing(10)
                self.index_badge = QLabel(f'{index:02d}')
                self.index_badge.setFixedSize(34, 26)
                lay.addWidget(self.index_badge, 0, deps['Qt'].AlignVCenter) if 'Qt' in deps else lay.addWidget(self.index_badge)
                info = deps['QVBoxLayout']()
                info.setSpacing(5)
                self.title_edit = QLineEdit(title)
                self.title_edit.setReadOnly(True)
                self.title_edit.setMinimumHeight(24)
                self.title_edit.setMinimumWidth(56)
                self.title_edit.installEventFilter(self)
                self.title_edit.textChanged.connect(self._syncTitleEditWidth)
                host, scheme, path = _task_url_meta(url)
                self.host_label = QLabel(host)
                self.host_label.setProperty('cardSub', True)
                self.host_label.setWordWrap(False)
                self.scheme_badge = QLabel(scheme)
                self.scheme_badge.setFixedSize(48, 20)
                self.path_label = QLabel(path)
                self.path_label.setProperty('cardSub', True)
                self.path_label.setWordWrap(False)
                self.url_label = QLabel(url)
                self.url_label.setProperty('cardSub', True)
                self.url_label.setWordWrap(True)
                title_row = deps['QHBoxLayout']()
                title_row.setContentsMargins(0, 0, 0, 0)
                title_row.setSpacing(8)
                title_row.addWidget(self.title_edit)
                title_row.addWidget(self.scheme_badge)
                title_row.addStretch(1)
                meta_row = deps['QHBoxLayout']()
                meta_row.setContentsMargins(0, 0, 0, 0)
                meta_row.setSpacing(8)
                meta_row.addWidget(self.host_label)
                meta_row.addWidget(self.path_label)
                meta_row.addStretch(1)
                info.addLayout(title_row)
                info.addLayout(meta_row)
                info.addWidget(self.url_label)
                lay.addLayout(info, 1)
                self.del_btn = QPushButton('\u00d7')
                self.del_btn.setToolTip('删除任务')
                self.del_btn.setAccessibleName('删除任务')
                self.del_btn.setFixedSize(self._btn_w, self._btn_w)
                self.del_btn.setCursor(deps['Qt'].PointingHandCursor) if 'Qt' in deps else None
                self.del_btn.clicked.connect(on_delete)
                lay.addWidget(self.del_btn, 0, deps['Qt'].AlignVCenter) if 'Qt' in deps else lay.addWidget(self.del_btn)
                self.applyTheme(_current_theme)
                self._syncTitleEditWidth()

            def applyTheme(self, theme):
                self._entry_bg = 'rgba(63, 70, 82, 0.58)' if theme == 'dark' else 'rgba(255, 255, 255, 0.72)'
                self._entry_hover_bg = 'rgba(78, 88, 104, 0.78)' if theme == 'dark' else 'rgba(247, 250, 255, 0.95)'
                self._entry_border = 'rgba(255, 255, 255, 0.08)' if theme == 'dark' else 'rgba(190, 202, 218, 0.56)'
                badge_bg = 'rgba(255, 255, 255, 0.035)' if theme == 'dark' else 'rgba(255, 255, 255, 0.34)'
                badge_border = 'rgba(255, 255, 255, 0.06)' if theme == 'dark' else 'rgba(120, 132, 150, 0.16)'
                badge_fg = 'rgba(220, 226, 236, 0.50)' if theme == 'dark' else 'rgba(71, 82, 98, 0.48)'
                scheme_bg = 'rgba(126, 166, 217, 0.18)' if theme == 'dark' else 'rgba(77, 134, 217, 0.11)'
                scheme_fg = '#a9c7f1' if theme == 'dark' else '#3468aa'
                meta_fg = 'rgba(220, 226, 236, 0.68)' if theme == 'dark' else 'rgba(71, 82, 98, 0.70)'
                url_fg = 'rgba(190, 198, 210, 0.48)' if theme == 'dark' else 'rgba(96, 108, 124, 0.52)'
                del_bg = 'rgba(255, 255, 255, 0.035)' if theme == 'dark' else 'rgba(120, 132, 150, 0.06)'
                del_fg = 'rgba(220, 226, 236, 0.42)' if theme == 'dark' else 'rgba(71, 82, 98, 0.42)'
                del_hover_bg = 'rgba(255, 95, 86, 0.18)' if theme == 'dark' else 'rgba(255, 95, 86, 0.14)'
                del_hover_fg = '#ff8f86' if theme == 'dark' else '#bf3b32'
                title_hint_bg = 'rgba(255, 255, 255, 0.05)' if theme == 'dark' else 'rgba(255, 255, 255, 0.32)'
                title_focus_bg = 'rgba(255, 255, 255, 0.08)' if theme == 'dark' else 'rgba(255, 255, 255, 0.48)'
                title_border = 'rgba(126, 166, 217, 0.28)' if theme == 'dark' else 'rgba(86, 132, 190, 0.24)'
                title_focus_border = 'rgba(126, 166, 217, 0.72)' if theme == 'dark' else 'rgba(77, 134, 217, 0.58)'
                title_selection = 'rgba(116, 165, 230, 0.45)' if theme == 'dark' else 'rgba(77, 134, 217, 0.18)'
                self.setStyleSheet(
                    f'QFrame {{ background: {self._entry_bg}; border: 1px solid {self._entry_border}; border-radius: 12px; }}'
                )
                self.index_badge.setStyleSheet(
                    'QLabel {'
                    f' background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border};'
                    ' border-radius:13px; font-size:11px; font-weight:600;'
                    " font-family:'Segoe UI','Arial',sans-serif;"
                    ' qproperty-alignment: AlignCenter;'
                    '}'
                )
                self.title_edit.setStyleSheet(
                    'QLineEdit {'
                    ' background:transparent; border:1px solid transparent; border-radius:5px;'
                    f' color:inherit; font-weight:bold; padding:1px 4px;'
                    f' selection-background-color:{title_selection};'
                    '}'
                    f'QLineEdit:hover {{ background:{title_hint_bg}; border-color:{title_border}; }}'
                    f'QLineEdit:focus {{ background:{title_focus_bg}; border-color:{title_focus_border}; }}'
                    'QLineEdit[readOnly="true"] { background:transparent; border-color:transparent; }'
                    f'QLineEdit[readOnly="true"]:hover {{ background:{title_hint_bg}; border-color:{title_border}; }}'
                )
                self.scheme_badge.setStyleSheet(
                    'QLabel {'
                    f' background:{scheme_bg}; color:{scheme_fg}; border:1px solid {title_border};'
                    ' border-radius:10px; font-size:10px; font-weight:700;'
                    " font-family:'Segoe UI','Arial',sans-serif;"
                    ' qproperty-alignment: AlignCenter;'
                    '}'
                )
                meta_style = (
                    f'QLabel {{ background:transparent; border:none; color:{meta_fg};'
                    " font-family:'Segoe UI','Arial',sans-serif; font-size:12px; }}"
                )
                self.host_label.setStyleSheet(meta_style)
                self.path_label.setStyleSheet(meta_style)
                self.url_label.setStyleSheet(
                    f'QLabel {{ background:transparent; border:none; color:{url_fg};'
                    " font-family:'Segoe UI','Arial',sans-serif; font-size:11px; }}"
                )
                self.del_btn.setStyleSheet(
                    'QPushButton {'
                    f' background:{del_bg}; border:none; border-radius:{self._btn_w // 2}px;'
                    f' font-size:16px; font-weight:500; color:{del_fg};'
                    " font-family:'Segoe UI','Arial',sans-serif; padding:0px 0px 2px 0px;"
                    '}'
                    f'QPushButton:hover {{ background:{del_hover_bg}; color:{del_hover_fg}; }}'
                )

            def _syncTitleEditWidth(self):
                metrics = self.title_edit.fontMetrics()
                text = self.title_edit.text() or ' '
                try:
                    text_w = metrics.horizontalAdvance(text)
                except AttributeError:
                    text_w = metrics.width(text)
                max_w = self.width() - self._btn_w - 48
                if max_w < 120:
                    max_w = 420
                self.title_edit.setFixedWidth(max(56, min(text_w + 18, max_w, 420)))

            def eventFilter(self, obj, ev):
                QEvent = deps.get('QEvent')
                if QEvent is None:
                    return super().eventFilter(obj, ev)
                if obj is self.title_edit:
                    etype = ev.type()
                    if etype == QEvent.MouseButtonDblClick:
                        self.title_edit.setReadOnly(False)
                        self.title_edit.selectAll()
                        self.title_edit.setFocus()
                        return True
                    if etype == QEvent.FocusOut:
                        if not self.title_edit.isReadOnly():
                            self.title_edit.setReadOnly(True)
                            self._on_rename(self.title_edit.text())
                        return True
                    if etype == QEvent.KeyPress and ev.key() == (deps['Qt'].Key_Return if 'Qt' in deps else 16777220):
                        self.title_edit.setReadOnly(True)
                        self._on_rename(self.title_edit.text())
                        return True
                return super().eventFilter(obj, ev)

            def enterEvent(self, ev):
                self.setStyleSheet(
                    f'QFrame {{ background: {self._entry_hover_bg}; border: 1px solid {self._entry_border}; border-radius: 12px; }}'
                )
                super().enterEvent(ev)

            def leaveEvent(self, ev):
                self.setStyleSheet(
                    f'QFrame {{ background: {self._entry_bg}; border: 1px solid {self._entry_border}; border-radius: 12px; }}'
                )
                super().leaveEvent(ev)

            def resizeEvent(self, ev):
                super().resizeEvent(ev)
                self._syncTitleEditWidth()

            def sizeHint(self):
                sh = super().sizeHint()
                min_h = 82
                min_w = self._btn_w + 10 + 4 + 6  # btn + margins + spacing
                if sh.height() < min_h:
                    sh.setHeight(min_h)
                if sh.width() < min_w:
                    sh.setWidth(min_w)
                return sh

        owner = self

        class WebTaskListWidget(QListWidget):
            if Signal is not None:
                entryChanged = Signal()

            def __init__(self, theme, placeholder):
                super().__init__()
                self._theme = theme
                bg = 'rgba(44, 50, 59, 0.88)' if theme == 'dark' else 'rgba(255, 255, 255, 0.76)'
                border = 'rgba(70, 80, 92, 0.5)' if theme == 'dark' else 'rgba(216, 222, 230, 0.6)'
                sb_thumb = 'rgba(100,110,130,0.55)' if theme == 'dark' else 'rgba(160,170,190,0.45)'
                sb_hover = 'rgba(120,130,150,0.7)' if theme == 'dark' else 'rgba(130,140,160,0.6)'
                self.setStyleSheet(
                    f'QListWidget {{ background: {bg}; border: 1px solid {border}; border-radius: 16px; padding: 4px; }}'
                    f'QListWidget::item {{ background: transparent; border: none; padding: 0px; margin: 0px; }}'
                    f'QListWidget::item:selected {{ background: transparent; }}'
                    f'QScrollBar {{ background: transparent; width: 8px; border-radius: 4px; }}'
                    f'QScrollBar::handle:vertical {{ background: {sb_thumb}; min-height: 30px; border-radius: 4px; }}'
                    f'QScrollBar::handle:vertical:hover {{ background: {sb_hover}; }}'
                    f'QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: transparent; }}'
                )
                if self.viewport():
                    self.viewport().setAutoFillBackground(False)
                    self.viewport().setStyleSheet(f'background: {bg};')
                self.setMinimumHeight(150)
                self.setMaximumHeight(300)
                self.setSelectionMode(QListWidget.NoSelection)
                self.setHorizontalScrollMode(QListWidget.ScrollPerPixel)
                self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.viewport().setContentsMargins(0, 0, 0, 0)
                self._placeholder = placeholder
                self._entry_count = 0

            def text(self):
                lines = []
                for i in range(self.count()):
                    item = self.item(i)
                    lines.append(item.data(deps['Qt'].UserRole) if 'Qt' in deps else item.data(256))
                return '\n'.join(lines)

            def setText(self, text):
                self.clear()
                for line in str(text).splitlines():
                    self.addEntry(line)

            def toPlainText(self):
                return self.text()

            def setPlainText(self, text):
                self.setText(text)

            def clear(self):
                super().clear()
                self._entry_count = 0

            def addEntry(self, line):
                entry = parse_web_queue_entry(str(line))
                if not entry:
                    return
                display_title = entry.get('title', entry['url'])
                item = QListWidgetItem()
                w = _TaskEntryWidget(
                    self.count() + 1, display_title, entry['url'],
                    lambda _checked=False, item=item: self._deleteItem(item),
                    lambda new_title: self._renameByWidget(w, new_title),
                )
                w.setMinimumHeight(82)
                role = deps['Qt'].UserRole if 'Qt' in deps else 256
                item.setData(role, format_web_queue_line(self.count() + 1, entry['title'], entry['url']))
                self.addItem(item)
                self.setItemWidget(item, w)
                self._fitItemSize(item, w)
                self._entry_count = self.count()

            def _fitItemSize(self, item, widget):
                QSize = deps.get('QSize')
                if QSize is None:
                    return
                vp_w = self.viewport().width()
                if vp_w < 100:
                    vp_w = 600
                item.setSizeHint(QSize(vp_w, 82))
                widget.setFixedWidth(vp_w)

            def resizeEvent(self, ev):
                super().resizeEvent(ev)
                for i in range(self.count()):
                    item = self.item(i)
                    w = self.itemWidget(item)
                    if w:
                        self._fitItemSize(item, w)

            def _role(self):
                return deps['Qt'].UserRole if 'Qt' in deps else 256

            def _lines(self):
                role = self._role()
                return [str(self.item(i).data(role) or '') for i in range(self.count())]

            def _apply_queue_tasks(self, tasks):
                role = self._role()
                for i, task in enumerate(tasks[:self.count()]):
                    item = self.item(i)
                    title = str(task.get('title') or '')
                    url = str(task.get('url') or '')
                    item.setData(role, format_web_queue_line(i + 1, title, url))
                    widget = self.itemWidget(item)
                    if hasattr(widget, 'title_edit'):
                        widget.title_edit.setText(title)
                    if hasattr(widget, 'index_badge') and hasattr(widget.index_badge, 'setText'):
                        widget.index_badge.setText(f'{i + 1:02d}')

            def _renameByWidget(self, widget, new_title):
                for i in range(self.count()):
                    if self.itemWidget(self.item(i)) is widget:
                        role = self._role()
                        old = str(self.item(i).data(role) or '')
                        entry = parse_web_queue_entry(old)
                        url = entry.get('url') or old
                        new_title = str(new_title or '').strip()
                        if not new_title:
                            if hasattr(widget, 'title_edit'):
                                widget.title_edit.setText(entry.get('title') or url)
                            return
                        lines = self._lines()
                        lines[i] = format_web_queue_line(i + 1, new_title, url)
                        tasks = build_web_queue_tasks(lines, getattr(owner, 'web_candidate_sources', {}))
                        self._apply_queue_tasks(tasks)
                        self._emitChanged()
                        break

            def _deleteItem(self, item):
                row = self.row(item)
                if row >= 0:
                    self.takeItem(row)
                self._renumber()
                self._emitChanged()

            def removeCompleted(self, results):
                success_urls = {str(r.get('source_url') or '') for r in results if r.get('success')}
                if not success_urls:
                    return
                for i in range(self.count() - 1, -1, -1):
                    item = self.item(i)
                    role = deps['Qt'].UserRole if 'Qt' in deps else 256
                    line = str(item.data(role) or '')
                    entry = parse_web_queue_entry(line)
                    if entry.get('url') in success_urls:
                        self.takeItem(i)
                self._renumber()
                self._emitChanged()

            def _renumber(self):
                role = self._role()
                for i in range(self.count()):
                    item = self.item(i)
                    old = str(item.data(role) or '')
                    cleaned = re.sub(r'^\d+[.、．]\s*', '', old)
                    item.setData(role, f'{i + 1}.{cleaned}')
                    widget = self.itemWidget(item)
                    if hasattr(widget, 'index_badge'):
                        widget.index_badge.setText(f'{i + 1:02d}')

            def _emitChanged(self):
                try:
                    self.entryChanged.emit()
                except Exception:
                    pass

            def applyTheme(self, theme):
                self._theme = theme
                bg = 'rgba(44, 50, 59, 0.88)' if theme == 'dark' else 'rgba(255, 255, 255, 0.76)'
                border = 'rgba(70, 80, 92, 0.5)' if theme == 'dark' else 'rgba(216, 222, 230, 0.6)'
                sb_thumb = 'rgba(100,110,130,0.55)' if theme == 'dark' else 'rgba(160,170,190,0.45)'
                sb_hover = 'rgba(120,130,150,0.7)' if theme == 'dark' else 'rgba(130,140,160,0.6)'
                self.setStyleSheet(
                    f'QListWidget {{ background: {bg}; border: 1px solid {border}; border-radius: 16px; padding: 4px; }}'
                    f'QListWidget::item {{ background: transparent; border: none; padding: 0px; margin: 0px; }}'
                    f'QListWidget::item:selected {{ background: transparent; }}'
                    f'QScrollBar {{ background: transparent; width: 8px; border-radius: 4px; }}'
                    f'QScrollBar::handle:vertical {{ background: {sb_thumb}; min-height: 30px; border-radius: 4px; }}'
                    f'QScrollBar::handle:vertical:hover {{ background: {sb_hover}; }}'
                    f'QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: transparent; }}'
                )
                if self.viewport():
                    self.viewport().setStyleSheet(f'background: {bg};')
                for i in range(self.count()):
                    w = self.itemWidget(self.item(i))
                    if hasattr(w, 'applyTheme'):
                        w.applyTheme(theme)

        self.task_edit = WebTaskListWidget(self.current_theme, self.mode_meta['task_placeholder'])
        self.task_edit.entryChanged.connect(self.handle_task_text_changed)
        task_layout.addWidget(QLabel('任务区'))
        task_layout.addWidget(self.task_edit)

        self.summary_label = QLabel(SUMMARY_EMPTY_TEXT)
        self.summary_label.setProperty('cardSub', True)
        self.summary_label.setWordWrap(True)
        task_layout.addWidget(self.summary_label)
    else:
        task_layout.addWidget(QLabel('任务链接'))
        self.task_edit = QPlainTextEdit()
        self.task_edit.setPlaceholderText(self.mode_meta['task_placeholder'])
        self.task_edit.setMinimumHeight(task_min_height)
        apply_video_textedit_surface(self.task_edit, textedit_style, self.current_theme)
        self.task_edit.textChanged.connect(self.handle_task_text_changed)

        self.summary_label = QLabel(SUMMARY_EMPTY_TEXT)
        self.summary_label.setProperty('cardSub', True)
        self.summary_label.setWordWrap(True)
        task_layout.addWidget(self.summary_label)
        task_layout.addWidget(self.task_edit)

    output_row = QHBoxLayout()
    output_row.setSpacing(8)
    self.output_edit = QLineEdit(load_setting(settings, self._mode_setting_key('output_dir')))
    self.output_edit.setPlaceholderText(OUTPUT_PLACEHOLDER)
    self.output_edit.editingFinished.connect(self.save_form_settings)
    self.choose_button = QPushButton('选择路径')
    self.choose_button.clicked.connect(self.choose_output_dir)
    output_row.addWidget(self.output_edit)
    output_row.addWidget(self.choose_button)
    task_layout.addLayout(output_row)

    proxy_row_widget, proxy_row = make_transparent_row()
    proxy_row.setSpacing(8)
    saved_proxy_host = load_setting(settings, self._mode_setting_key('proxy_host'), '')
    saved_proxy_port = load_setting(settings, self._mode_setting_key('proxy_port'), '')
    if not saved_proxy_host and not saved_proxy_port:
        saved_proxy_host, saved_proxy_port = self.module.split_proxy_url(load_setting(settings, self._mode_setting_key('proxy_url'), ''))
    proxy_row.addWidget(QLabel('代理主机'))
    self.proxy_host_edit = QLineEdit(saved_proxy_host or '127.0.0.1')
    self.proxy_host_edit.setPlaceholderText('127.0.0.1')
    self.proxy_host_edit.setMaximumWidth(180)
    self.proxy_host_edit.editingFinished.connect(self.save_form_settings)
    proxy_row.addWidget(self.proxy_host_edit)
    proxy_row.addWidget(QLabel('端口'))
    self.proxy_port_edit = QLineEdit(saved_proxy_port)
    self.proxy_port_edit.setPlaceholderText('可选')
    self.proxy_port_edit.setMaximumWidth(96)
    self.proxy_port_edit.editingFinished.connect(self.save_form_settings)
    proxy_row.addWidget(self.proxy_port_edit)
    proxy_row.addStretch(1)
    task_layout.addWidget(proxy_row_widget)

    common_row_widget, common_row = make_transparent_row()
    common_row.setSpacing(8)
    self.overwrite_checkbox = QCheckBox('覆盖同名文件')
    self.overwrite_checkbox.setChecked(load_setting(settings, self._mode_setting_key('overwrite'), '0') == '1')
    self.overwrite_checkbox.clicked.connect(self.save_form_settings)
    common_row.addWidget(self.overwrite_checkbox)
    if self.source_mode == 'web':
        self.output_subdir_checkbox = QCheckBox('按命名建文件夹')
        self.output_subdir_checkbox.setChecked(load_setting(settings, self._mode_setting_key('output_subdir_by_title'), '0') == '1')
        self.output_subdir_checkbox.clicked.connect(self.save_form_settings)
        common_row.addWidget(self.output_subdir_checkbox)
    common_row.addWidget(QLabel('同时下载'))
    self.concurrent_combo = QComboBox()
    self.concurrent_combo.addItems(['自动', '1', '2', '3', '4', '5'])
    saved_concurrent = load_setting(settings, self._mode_setting_key('concurrent'), '1')
    if saved_concurrent == '0':
        saved_index = 0
    else:
        saved_index = max(1, min(5, int(saved_concurrent or '1')))
    self.concurrent_combo.setCurrentIndex(saved_index)
    self.concurrent_combo.setMinimumWidth(120)
    self.concurrent_combo.setMaximumWidth(120)
    self.concurrent_combo.currentIndexChanged.connect(self.save_form_settings)
    style_combo_popup(self.concurrent_combo, self.current_theme)
    common_row.addWidget(self.concurrent_combo)
    common_row.addStretch(1)
    task_layout.addWidget(common_row_widget)

    action_row = QHBoxLayout()
    action_row.setSpacing(8)
    if self.source_mode == 'web':
        self.scan_button = QPushButton('识别并添加')
        self.scan_button.setToolTip('从网页链接中识别视频并自动添加到任务区')
        self.scan_button.clicked.connect(self.scan_web_candidates)
        action_row.addWidget(self.scan_button)
    self.cover_button = QPushButton('补封面')
    self.cover_button.setToolTip('给已下载的视频嵌入封面（需提供源链接）')
    self.cover_button.clicked.connect(self.embed_thumbnail_clicked)
    action_row.addWidget(self.cover_button)
    action_row.addStretch(1)
    self.run_button = QPushButton(RUN_BUTTON_TEXT)
    self.run_button.setMinimumWidth(110)
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


def build_log_section(self, layout, center_row, textedit_style, log_min_height, deps):
    make_card = deps['make_card']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']

    log_card_title = '日志' if self.source_mode == 'web' else '运行日志'
    log_card, log_layout = make_card(log_card_title)
    compact_card_layout(log_layout, 16, 10)
    self.log = QPlainTextEdit()
    self.log.setReadOnly(True)
    self.log.setMinimumHeight(log_min_height)
    apply_video_textedit_surface(self.log, textedit_style, self.current_theme)

    self.progress_label = QLabel('等待开始')
    self.progress_label.setProperty('cardSub', True)
    self.progress_label.setWordWrap(True)

    self.task_counter_label = QLabel('')
    self.task_counter_label.setProperty('cardSub', True)

    self.progress_bar = QProgressBar()
    self.progress_bar.setMinimum(0)
    self.progress_bar.setMaximum(100)
    self.progress_bar.setValue(0)
    log_layout.addWidget(self.log)
    log_layout.addWidget(self.progress_label)
    log_layout.addWidget(self.task_counter_label)
    log_layout.addWidget(self.progress_bar)
    if self.source_mode == 'web':
        layout.addWidget(log_card, 1)
    else:
        center_row.addWidget(log_card, 2)
        layout.addLayout(center_row)
