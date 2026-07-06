from __future__ import annotations

import json
from pathlib import Path


def test_history_store_persists_newest_items_and_trims_to_limit(tmp_path: Path) -> None:
    from sidecar.history_store import append_history, load_history

    settings_path = tmp_path / "hyl_toolbox.ini"
    for index in range(105):
        append_history("aiimage", {"id": f"item-{index}", "created_at": f"2026-01-01T00:00:{index:02d}"}, settings_path=settings_path)

    items = load_history("aiimage", settings_path=settings_path)

    assert len(items) == 100
    assert items[0]["id"] == "item-104"
    assert items[-1]["id"] == "item-5"


def test_history_store_delete_and_clear_are_persistent(tmp_path: Path) -> None:
    from sidecar.history_store import append_history, clear_history, delete_history, load_history

    settings_path = tmp_path / "hyl_toolbox.ini"
    append_history("directdownloader", {"id": "keep"}, settings_path=settings_path)
    append_history("directdownloader", {"id": "remove"}, settings_path=settings_path)

    assert delete_history("directdownloader", "remove", settings_path=settings_path) is True
    assert [item["id"] for item in load_history("directdownloader", settings_path=settings_path)] == ["keep"]

    clear_history("directdownloader", settings_path=settings_path)
    assert load_history("directdownloader", settings_path=settings_path) == []


def test_history_store_scrubs_sensitive_fields_before_writing(tmp_path: Path) -> None:
    from sidecar.history_store import append_history, history_path

    settings_path = tmp_path / "hyl_toolbox.ini"
    append_history(
        "tgdownloader",
        {
            "id": "tg-1",
            "credentials": {
                "api_id": "12345",
                "api_hash": "hash-secret",
                "phone": "+10000000000",
                "phone_code_hash": "code-hash",
            },
            "password": "pw",
            "code": "12345",
            "files": ["E:/out/a.mp4"],
        },
        settings_path=settings_path,
    )

    text = history_path(settings_path).read_text(encoding="utf-8")

    assert "hash-secret" not in text
    assert "code-hash" not in text
    assert '"password"' not in text
    assert '"code"' not in text
    assert json.loads(text)["tgdownloader"][0]["credentials"] == {"api_id": "12345", "phone": "+10000000000"}
