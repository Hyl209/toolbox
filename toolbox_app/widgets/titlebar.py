from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


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
        color = '#f5f7fa' if getattr(self.window(), 'current_theme', 'light') == 'dark' else '#4d5866'
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
        self._host_window = window
        self.setProperty('dragBar', True)
        self.setFixedHeight(34)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 20, 0)
        layout.setSpacing(8)
        self.title_label = QLabel('')
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label, 1)
        self._host_window.window_controls_layout = QHBoxLayout()
        self._host_window.window_controls_layout.setContentsMargins(0, 0, 0, 0)
        self._host_window.window_controls_layout.setSpacing(10)
        self._host_window.min_button = WindowControlButton('min', '最小化', self)
        self._host_window.max_button = WindowControlButton('max', '最大化', self)
        self._host_window.close_button = WindowControlButton('close', '关闭', self)
        self._host_window.min_button.clicked.connect(self._host_window.showMinimized)
        self._host_window.max_button.clicked.connect(self._host_window.toggle_max_restore)
        self._host_window.close_button.clicked.connect(self._host_window.close)
        self._host_window.window_controls_layout.addWidget(self._host_window.min_button)
        self._host_window.window_controls_layout.addWidget(self._host_window.max_button)
        self._host_window.window_controls_layout.addWidget(self._host_window.close_button)
        layout.addLayout(self._host_window.window_controls_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._host_window.start_window_drag(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._host_window.update_window_drag(event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._host_window.stop_window_drag()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._host_window.toggle_max_restore()
        super().mouseDoubleClickEvent(event)
