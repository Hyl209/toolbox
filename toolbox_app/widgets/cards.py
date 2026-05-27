from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


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
