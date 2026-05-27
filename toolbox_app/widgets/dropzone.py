from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileIconProvider,
    QFrame,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .animation import pulse_widget


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
