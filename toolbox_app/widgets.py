from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEventLoop, QTimer, QPoint, QSize, QFileInfo
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QStackedWidget,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl


def make_card(title: str, subtitle: str = ''):
    frame = QFrame()
    frame.setProperty('card', True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(26, 24, 26, 24)
    layout.setSpacing(16)
    title_label = QLabel(title)
    title_label.setProperty('cardTitle', True)
    layout.addWidget(title_label)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setProperty('cardSub', True)
        layout.addWidget(sub)
    return frame, layout


def make_transparent_row():
    row = QWidget()
    row.setAttribute(Qt.WA_StyledBackground, True)
    row.setStyleSheet('background: transparent;')
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    return row, layout


class ComboItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        return QSize(max(hint.width(), 120), 34)


def style_combo_popup(combo: QComboBox, theme_name: str):
    if QListView is None:
        return
    popup_view = combo.view()
    if popup_view is None:
        return
    popup_view.setObjectName('comboPopupView')
    popup_view.setProperty('comboPopupTheme', theme_name)
    popup_view.viewport().setProperty('comboPopupTheme', theme_name)
    if theme_name == 'light':
        popup_style = (
            'QListView, QListView[comboPopupTheme="light"] {background-color: #eef1f5; color: #1f252d; '
            'border: 1px solid #d8dee6; border-radius: 0; outline: none; padding: 2px;} '
            'QListView::item {border-radius: 10px;} '
            'QListView::item:selected {background-color: #d4e4ff; color: #1f252d;} '
            'QWidget[comboPopupTheme="light"] {background-color: #eef1f5; color: #1f252d; border-radius: 0;}'
        )
    else:
        popup_style = (
            'QListView, QListView[comboPopupTheme="dark"] {background-color: #2a3038; color: #eef2f7; '
            'border: 1px solid #46505c; border-radius: 0; outline: none; padding: 2px;} '
            'QListView::item {border-radius: 10px;} '
            'QListView::item:selected {background-color: #6d94c8; color: #eef2f7;} '
            'QWidget[comboPopupTheme="dark"] {background-color: #2a3038; color: #eef2f7; border-radius: 0;}'
        )
    popup_view.setStyleSheet(popup_style)
    popup_view.setItemDelegate(ComboItemDelegate(popup_view))
    popup_view.setSpacing(2)
    popup_view.setFrameShape(QFrame.NoFrame)
    popup_view.viewport().setAutoFillBackground(False)


def animate_fade(widget: QWidget, start: float = 0.0, end: float = 1.0, duration: int = 180):
    if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(start)
    animation = QPropertyAnimation(effect, b'opacity', widget)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._fade_animation = animation
    return animation


def fade_out_and_close(widget: QWidget, duration: int = 160):
    if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
        widget.close()
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(1.0)
    animation = QPropertyAnimation(effect, b'opacity', widget)
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.finished.connect(widget.accept if hasattr(widget, 'accept') else widget.close)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._fade_close_animation = animation
    return animation


def resolve_theme_name(widget) -> str:
    current = widget
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        theme_name = getattr(current, 'current_theme', None)
        if theme_name in {'dark', 'light'}:
            return theme_name
        current = current.parentWidget() if hasattr(current, 'parentWidget') else None
    return 'light'


class ThemedMessageDialog(QDialog):
    def __init__(self, parent, title: str, lines: list[str], button_text: str = '完成'):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._closed_with_fade = False
        theme_name = resolve_theme_name(parent)
        if theme_name == 'dark':
            surface = '#232933'
            title_color = '#f4f7fb'
            text_color = '#d5dce6'
            button_bg = '#6f95c7'
            button_hover = '#7b9fd0'
            button_text_color = '#eef4fb'
            button_border = '#7ea4d3'
        else:
            surface = '#f7f9fc'
            title_color = '#243447'
            text_color = '#4e5968'
            button_bg = '#e4efff'
            button_hover = '#edf4ff'
            button_text_color = '#24415f'
            button_border = '#cfd9e8'
        self.setStyleSheet(
            f"QFrame[messageCard='true'] {{background-color: {surface}; border: none; border-radius: 0px;}}"
            f"QLabel[messageTitle='true'] {{color: {title_color}; font-size: 17px; font-weight: 600; background: transparent;}}"
            f"QLabel[messageLine='true'] {{color: {text_color}; font-size: 13px; font-weight: 500; background: transparent;}}"
            f"QPushButton[messageButton='true'] {{background-color: {button_bg}; color: {button_text_color}; border: 1px solid {button_border}; border-radius: 6px; padding: 8px 20px; min-width: 96px; font-weight: 600;}}"
            f"QPushButton[messageButton='true']:hover {{background-color: {button_hover};}}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setProperty('messageCard', True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        title_label = QLabel(title)
        title_label.setProperty('messageTitle', True)
        card_layout.addWidget(title_label)
        for line in lines:
            if not line:
                continue
            label = QLabel(line)
            label.setProperty('messageLine', True)
            label.setWordWrap(True)
            card_layout.addWidget(label)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        confirm_button = QPushButton(button_text)
        confirm_button.setProperty('messageButton', True)
        confirm_button.clicked.connect(self.close_with_fade)
        button_row.addWidget(confirm_button)
        button_row.addStretch(1)
        card_layout.addSpacing(2)
        card_layout.addLayout(button_row)
        root.addWidget(card)
        self.resize(352, card.sizeHint().height())
        animate_fade(self, 0.0, 1.0, 180)

    def close_with_fade(self):
        if self._closed_with_fade:
            return
        self._closed_with_fade = True
        fade_out_and_close(self, 160)


def show_themed_message(parent, title: str, lines: list[str], button_text: str = '完成'):
    theme_owner = parent
    while theme_owner is not None and not hasattr(theme_owner, 'current_theme'):
        theme_owner = theme_owner.parentWidget() if hasattr(theme_owner, 'parentWidget') else None
    if theme_owner is not None:
        theme_owner.setStyleSheet(get_theme_stylesheet(theme_owner.current_theme))
    dialog = ThemedMessageDialog(parent, title, lines, button_text)
    if QEventLoop is None or QTimer is None:
        dialog.exec()
        return
    loop = QEventLoop()
    dialog.finished.connect(loop.quit)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    loop.exec()


def show_themed_warning(parent, title: str, message: str):
    lines = [line for line in message.splitlines() if line.strip()] or [message]
    show_themed_message(parent, title, lines, '完成')


def show_themed_success(parent, title: str, lines: list[str]):
    if QMediaPlayer is not None and SOUND_PATH.exists():
        try:
            player = QMediaPlayer()
            audio = QAudioOutput()
            player.setAudioOutput(audio)
            player.setSource(QUrl.fromLocalFile(str(SOUND_PATH.resolve())))
            player.play()
        except Exception:
            pass
    show_themed_message(parent, title, lines, '完成')


def show_themed_error(parent, title: str, message: str):
    lines = [line for line in message.splitlines() if line.strip()] or [message]
    show_themed_message(parent, title, lines, '完成')


def animate_stack_switch(stack: QStackedWidget, index: int):
    current_index = stack.currentIndex()
    if index < 0 or index == current_index:
        return
    stack.setCurrentIndex(index)
    page = stack.currentWidget()
    if page is None:
        return
    if QPropertyAnimation is None:
        return
    end_pos = page.pos()
    offset = 100 if index > current_index else -100
    start_pos = QPoint(end_pos.x(), end_pos.y() + offset)
    page.move(start_pos)
    move = QPropertyAnimation(page, b'pos', page)
    move.setDuration(600)
    move.setStartValue(start_pos)
    move.setEndValue(end_pos)
    move.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade = animate_fade(page, 0.35, 1.0, 350)
    move.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    page._slide_animation = (move, fade)


def pulse_widget(widget: QWidget, duration: int = 150):
    if QPropertyAnimation is None:
        return None
    original = widget.geometry()
    grown = original.adjusted(-2, -2, 2, 2)
    grow = QPropertyAnimation(widget, b'geometry', widget)
    grow.setDuration(duration)
    grow.setStartValue(original)
    grow.setEndValue(grown)
    grow.setEasingCurve(QEasingCurve.Type.OutCubic)
    shrink = QPropertyAnimation(widget, b'geometry', widget)
    shrink.setDuration(duration)
    shrink.setStartValue(grown)
    shrink.setEndValue(original)
    shrink.setEasingCurve(QEasingCurve.Type.OutCubic)
    group = QParallelAnimationGroup(widget)
    grow.finished.connect(shrink.start)
    group.addAnimation(grow)
    group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
    widget._pulse_animation = (group, shrink)
    return group


class DropZoneCard(QFrame):
    _icon_provider = None

    def __init__(self, body_text: str, on_files_dropped=None):
        super().__init__()
        self.on_files_dropped = on_files_dropped
        self.empty_text = body_text
        self.setProperty('dropzone', True)
        self.setProperty('active', False)
        self.setAcceptDrops(True)
        self.setMinimumHeight(190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(120)
        self.preview_label.hide()
        self.header_label = QLabel(body_text)
        self.header_label.setProperty('dropBody', True)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setWordWrap(True)
        self.body_label = QLabel('')
        self.body_label.setProperty('cardSub', True)
        self.body_label.setAlignment(Qt.AlignCenter)
        self.body_label.setWordWrap(True)
        self.body_label.hide()
        self.content_widget = None
        self.top_spacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.bottom_spacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(self.top_spacer)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.header_label)
        layout.addWidget(self.body_label)
        layout.addItem(self.bottom_spacer)
        self._layout = layout

    @classmethod
    def _get_icon_provider(cls):
        if QFileIconProvider is None:
            return None
        if cls._icon_provider is None:
            cls._icon_provider = QFileIconProvider()
        return cls._icon_provider

    def _show_preview_pixmap(self, pixmap, header_text: str = '', body_text: str = ''):
        if pixmap is None or pixmap.isNull():
            self.set_body_text('\n\n'.join(part for part in [header_text, body_text] if part))
            return
        self.preview_label.setPixmap(pixmap)
        self.preview_label.show()
        self.header_label.setText(header_text or self.empty_text)
        self.header_label.show()
        self.body_label.setText(body_text)
        self.body_label.setVisible(bool(body_text))

    def set_body_text(self, text: str):
        header, _, body = text.partition('\n\n')
        header = header.strip() or self.empty_text
        body = body.strip()
        self.header_label.setText(header)
        self.header_label.show()
        self.body_label.setText(body)
        self.body_label.setVisible(bool(body))
        if text:
            self.preview_label.hide()
            self.preview_label.clear()

    def set_preview_image(self, path: str, header_text: str = '', body_text: str = ''):
        if QPixmap is None:
            self.set_body_text('\n\n'.join(part for part in [header_text or Path(path).name, body_text] if part))
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.set_body_text('\n\n'.join(part for part in [header_text or Path(path).name, body_text] if part))
            return
        scaled = pixmap.scaled(220, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._show_preview_pixmap(scaled, header_text, body_text)

    def set_preview_file_icon(self, path: str, header_text: str = '', body_text: str = ''):
        icon_provider = self._get_icon_provider()
        if icon_provider is None or QFileInfo is None or QPixmap is None:
            self.set_body_text('\n\n'.join(part for part in [header_text or Path(path).name, body_text] if part))
            return
        icon = icon_provider.icon(QFileInfo(path))
        pixmap = icon.pixmap(QSize(72, 72)) if not icon.isNull() else QPixmap()
        self._show_preview_pixmap(pixmap, header_text, body_text)

    def set_content_widget(self, widget):
        if self.content_widget is widget:
            return
        if self.content_widget is not None:
            self._layout.removeWidget(self.content_widget)
            self.content_widget.setParent(None)
        self.content_widget = widget
        if widget is not None:
            self._layout.insertWidget(4, widget)

    def set_content_mode(self, has_content: bool):
        self.top_spacer.changeSize(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum if has_content else QSizePolicy.Policy.Expanding)
        self.bottom_spacer.changeSize(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum if has_content else QSizePolicy.Policy.Expanding)
        self.header_label.setVisible(not has_content)
        self.body_label.setVisible(False if has_content else bool(self.body_label.text().strip()))
        self.preview_label.setVisible(False if has_content else not self.preview_label.pixmap().isNull() if self.preview_label.pixmap() is not None else False)
        if self.content_widget is not None:
            self.content_widget.setVisible(has_content)
        self._layout.invalidate()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setProperty('active', True)
            self.style().unpolish(self)
            self.style().polish(self)
            pulse_widget(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty('active', False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event):
        self.setProperty('active', False)
        self.style().unpolish(self)
        self.style().polish(self)
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if self.on_files_dropped:
            self.on_files_dropped(paths)
        event.acceptProposedAction()


class WindowControlButton(QPushButton):
    def __init__(self, control_type: str, tooltip: str, parent=None):
        super().__init__('', parent)
        self.control_type = control_type
        self.setToolTip(tooltip)
        self.setProperty('windowControl', True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(24, 24)
        self.setFlat(True)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = '#f5f7fa' if self.window().current_theme == 'dark' else '#4d5866'
        pen = QPen(color)
        pen.setWidthF(1.8)
        painter.setPen(pen)
        if self.control_type == 'min':
            painter.drawLine(6, 12, 18, 12)
        elif self.control_type == 'max':
            painter.drawRect(6, 6, 12, 12)
        elif self.control_type == 'restore':
            painter.drawRect(8, 6, 8, 8)
            painter.drawLine(10, 6, 18, 6)
            painter.drawLine(18, 6, 18, 14)
            painter.drawLine(10, 8, 18, 8)
            painter.drawLine(6, 10, 14, 10)
            painter.drawLine(6, 10, 6, 18)
            painter.drawLine(6, 18, 14, 18)
        else:
            painter.drawLine(7, 7, 17, 17)
            painter.drawLine(17, 7, 7, 17)
        painter.end()


class DragTitleBar(QFrame):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setProperty('dragBar', True)
        self.setFixedHeight(34)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 20, 0)
        layout.setSpacing(8)
        self.title_label = QLabel('')
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label, 1)
        self.window.window_controls_layout = QHBoxLayout()
        self.window.window_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.window.window_controls_layout.setSpacing(10)
        self.window.min_button = WindowControlButton('min', '最小化', self)
        self.window.max_button = WindowControlButton('max', '最大化', self)
        self.window.close_button = WindowControlButton('close', '关闭', self)
        self.window.min_button.clicked.connect(self.window.showMinimized)
        self.window.max_button.clicked.connect(self.window.toggle_max_restore)
        self.window.close_button.clicked.connect(self.window.close)
        self.window.window_controls_layout.addWidget(self.window.min_button)
        self.window.window_controls_layout.addWidget(self.window.max_button)
        self.window.window_controls_layout.addWidget(self.window.close_button)
        layout.addLayout(self.window.window_controls_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window.start_window_drag(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.window.update_window_drag(event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.window.stop_window_drag()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window.toggle_max_restore()
        super().mouseDoubleClickEvent(event)


def build_base_tool_tab_class(QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                               QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
                               DropZoneCard, load_setting, save_setting, make_card,
                               build_global_scrollbar_style, ROOT, settings_prefix: str):
    """Return a BaseToolTab class with common UI helpers for tool tabs.

    Args:
        settings_prefix: The INI section prefix, e.g. 'mp4mp3', 'imageconvert'.
    """

    class BaseToolTab(QWidget):
        _settings_prefix = settings_prefix

        def init_output_dir_row(self, layout, placeholder='选择输出目录', setting_suffix='output_dir'):
            """Create output directory row with choose button. Attaches self.output_edit and self._choose_btn."""
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(self.settings, f'{self._settings_prefix}/{setting_suffix}'))
            self.output_edit.setPlaceholderText(placeholder)
            self._choose_btn = QPushButton('选择路径')
            self._choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(self._choose_btn)
            layout.addLayout(row)

        def init_log_widget(self, layout, min_height=140):
            """Create read-only log widget. Attaches self.log."""
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(min_height)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)

        def init_progress_widget(self, layout):
            """Create progress bar. Attaches self.progress."""
            self.progress = QProgressBar()
            layout.addWidget(self.progress)

        def choose_output_dir(self):
            """Open directory dialog and save selection."""
            path = QFileDialog.getExistingDirectory(
                self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, f'{self._settings_prefix}/output_dir', path)

    return BaseToolTab
