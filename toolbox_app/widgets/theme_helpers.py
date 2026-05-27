from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QComboBox, QFrame, QListView, QStyledItemDelegate


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
