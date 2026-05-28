from __future__ import annotations

from ._shared import TELEGRAM_HOSTS  # noqa: F401 — single source of truth

SETTINGS_PREFIX = 'video_downloader'
TITLE = '视频下载'
SUBTITLE = '批量下载 Telegram 和网页视频'
TASK_PLACEHOLDER = '每行一个链接'
OUTPUT_PLACEHOLDER = '选择视频输出目录'
DEFAULT_RECENT_LIMIT = '500'
DATE_FROM_PLACEHOLDER = '开始日期 YYYY-MM-DD'
DATE_TO_PLACEHOLDER = '结束日期 YYYY-MM-DD'
WEB_INDEX_PLACEHOLDER = '如 3 或 3,4,6，no3 排除，留空则自动'
SUMMARY_EMPTY_TEXT = '请先输入下载链接'
RUN_BUTTON_TEXT = '开始下载'
RUNNING_BUTTON_TEXT = '下载中...'
SEND_CODE_BUTTON_TEXT = '发送验证码'
LOGIN_BUTTON_TEXT = '完成登录'
STATUS_BUTTON_TEXT = '检查状态'
TELEGRAM_ONLY_ERROR = '当前页仅支持 Telegram 链接，请移到“网页视频下载”页签处理网页链接'
WEB_ONLY_ERROR = '当前页仅支持网页视频链接，请移到“TG下载”页签处理 Telegram 链接'

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
