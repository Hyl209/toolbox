from __future__ import annotations

import re
from urllib.parse import urlparse

from .tab_formatters import parse_web_queue_entry, format_web_queue_line, build_web_queue_tasks


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


def _make_entry_class(deps):
    QFrame = deps.get('QFrame')
    QLabel = deps['QLabel']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QHBoxLayout = deps['QHBoxLayout']
    QVBoxLayout = deps['QVBoxLayout']
    Qt = deps.get('Qt')
    QEvent = deps.get('QEvent')

    class TaskEntryWidget(QFrame):
        def __init__(self, index, title, url, on_delete, on_rename, theme):
            super().__init__()
            self._on_rename = on_rename
            self._btn_w = 32
            self._entry_bg = ''
            self._entry_hover_bg = ''
            self._entry_border = ''
            if Qt is not None:
                self.setAttribute(Qt.WA_Hover)
            lay = QHBoxLayout(self)
            lay.setContentsMargins(12, 10, 8, 10)
            lay.setSpacing(10)
            self.index_badge = QLabel(f'{index:02d}')
            self.index_badge.setFixedSize(34, 26)
            if Qt is not None:
                lay.addWidget(self.index_badge, 0, Qt.AlignVCenter)
            else:
                lay.addWidget(self.index_badge)
            info = QVBoxLayout()
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
            title_row = QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(8)
            title_row.addWidget(self.title_edit)
            title_row.addWidget(self.scheme_badge)
            title_row.addStretch(1)
            meta_row = QHBoxLayout()
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
            if Qt is not None:
                self.del_btn.setCursor(Qt.PointingHandCursor)
            self.del_btn.clicked.connect(on_delete)
            if Qt is not None:
                lay.addWidget(self.del_btn, 0, Qt.AlignVCenter)
            else:
                lay.addWidget(self.del_btn)
            self.applyTheme(theme)
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
                if etype == QEvent.KeyPress and ev.key() == (Qt.Key_Return if Qt is not None else 16777220):
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
            min_w = self._btn_w + 10 + 4 + 6
            if sh.height() < min_h:
                sh.setHeight(min_h)
            if sh.width() < min_w:
                sh.setWidth(min_w)
            return sh

    return TaskEntryWidget


def _make_list_class(deps, TaskEntryWidget):
    QListWidget = deps['QListWidget']
    QListWidgetItem = deps['QListWidgetItem']
    Signal = deps.get('Signal')
    Qt = deps.get('Qt')

    class WebTaskListWidget(QListWidget):
        if Signal is not None:
            entryChanged = Signal()

        def __init__(self, owner, theme, placeholder):
            super().__init__()
            self._owner = owner
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
            role = self._role()
            lines = []
            for i in range(self.count()):
                item = self.item(i)
                lines.append(item.data(role))
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
            w = TaskEntryWidget(
                self.count() + 1, display_title, entry['url'],
                lambda _checked=False, item=item: self._deleteItem(item),
                lambda new_title: self._renameByWidget(w, new_title),
                self._theme,
            )
            w.setMinimumHeight(82)
            role = self._role()
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
            return Qt.UserRole if Qt is not None else 256

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
            owner = self._owner
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
                role = self._role()
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
            except AttributeError:
                pass  # Signal not available in test environment

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

    return WebTaskListWidget


def create_task_list_widget(deps, owner, theme, placeholder):
    TaskEntryWidget = _make_entry_class(deps)
    WebTaskListWidget = _make_list_class(deps, TaskEntryWidget)
    return WebTaskListWidget(owner, theme, placeholder)
