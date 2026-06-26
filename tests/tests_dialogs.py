from __future__ import annotations

from toolbox_app.widgets import dialogs


def test_show_themed_success_wraps_plain_string(monkeypatch):
    captured = {}

    def fake_show(parent, title, lines, button_text='完成'):
        captured['title'] = title
        captured['lines'] = lines
        captured['button_text'] = button_text

    monkeypatch.setattr(dialogs, 'show_themed_message', fake_show)
    monkeypatch.setattr(dialogs, 'QMediaPlayer', None)

    dialogs.show_themed_success(None, '完成', '已完成 1 个下载')

    assert captured == {
        'title': '完成',
        'lines': ['已完成 1 个下载'],
        'button_text': '完成',
    }
