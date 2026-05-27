from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .animation import animate_fade, fade_out_and_close

_SOUND_PATH = Path(__file__).resolve().parent.parent.parent / 'sound.mp3'


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
    dialog = ThemedMessageDialog(parent, title, lines, button_text)
    dialog.exec()


def show_themed_warning(parent, title: str, message: str):
    lines = [line for line in message.splitlines() if line.strip()] or [message]
    show_themed_message(parent, title, lines, '完成')


_active_audio_players: list = []


def show_themed_success(parent, title: str, lines: list[str]):
    if QMediaPlayer is not None and _SOUND_PATH.exists():
        try:
            player = QMediaPlayer()
            audio = QAudioOutput()
            player.setAudioOutput(audio)
            player.setSource(QUrl.fromLocalFile(str(_SOUND_PATH.resolve())))
            player.play()
            # Prevent GC while audio is playing
            _active_audio_players.append((player, audio))
            player.mediaStatusChanged.connect(
                lambda status: _active_audio_players.clear()
                if status == QMediaPlayer.MediaStatus.EndOfMedia else None
            )
        except Exception:
            pass
    show_themed_message(parent, title, lines, '完成')


def show_themed_error(parent, title: str, message: str):
    lines = [line for line in message.splitlines() if line.strip()] or [message]
    show_themed_message(parent, title, lines, '完成')
