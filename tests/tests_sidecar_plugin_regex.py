from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from sidecar.settings_bridge import build_settings_snapshot


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-regex-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "plugin:regex_tools", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    assert proc.stderr == ""
    lines = [line for line in proc.stdout.splitlines() if line]
    assert lines, "sidecar produced no stdout"
    return [json.loads(line) for line in lines]


def last_event(events: list[dict]) -> dict:
    return events[-1]


def write_regex_plugin(root: Path, *, enabled: bool = True) -> None:
    plugin_dir = root / "plugins" / "regex_tools"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "regex_tools",
                "version": "1.0.0",
                "description": "Regex tools",
                "author": "Hyl",
                "sidebar_label": "Regex Tools",
                "entry": "plugin.py:RegexToolsPlugin",
                "type": "gui",
                "enabled": enabled,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_regex_extract_returns_matches_and_text_with_int_group() -> None:
    event = last_event(
        run_plugin(
            {
                "task_id": "regex-extract",
                "action": "extract",
                "payload": {
                    "text": "Alpha: 123\nbeta: 456",
                    "pattern": r"(\w+):\s+(\d+)",
                    "group": 2,
                    "ignore_case": True,
                    "multiline": True,
                },
            }
        )
    )

    assert event["type"] == "result"
    assert event["data"]["matches"] == ["123", "456"]
    assert event["data"]["text"] == "123\n456"


def test_regex_extract_supports_named_group() -> None:
    event = last_event(
        run_plugin(
            {
                "task_id": "regex-extract-name",
                "action": "extract",
                "payload": {
                    "text": "id=abc-123\nid=def-456",
                    "pattern": r"id=(?P<slug>[a-z]+-\d+)",
                    "group": "slug",
                },
            }
        )
    )

    assert event["type"] == "result"
    assert event["data"]["matches"] == ["abc-123", "def-456"]
    assert event["data"]["text"] == "abc-123\ndef-456"


def test_regex_replace_returns_replaced_text() -> None:
    event = last_event(
        run_plugin(
            {
                "task_id": "regex-replace",
                "action": "replace",
                "payload": {
                    "text": "Order 123, order 456",
                    "pattern": r"order\s+(\d+)",
                    "replacement": r"ticket-\1",
                    "ignore_case": True,
                },
            }
        )
    )

    assert event["type"] == "result"
    assert event["data"]["text"] == "ticket-123, ticket-456"


def test_regex_summary_returns_count_dict() -> None:
    event = last_event(
        run_plugin(
            {
                "task_id": "regex-summary",
                "action": "summary",
                "payload": {"text": "cat dog cat", "pattern": r"\b\w{3}\b"},
            }
        )
    )

    assert event["type"] == "result"
    assert event["data"]["summary"] == {"matches": 3, "unique": 2}


def test_settings_marks_regex_ready_but_respects_disabled_sources(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=regex_tools\n", encoding="utf-8")
    write_regex_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    regex_plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:regex_tools")

    assert regex_plugin["supported_in_tauri"] is True
    assert regex_plugin["status"] == "ready"
    assert regex_plugin["enabled"] is False

    settings_path.write_text("[plugins]\ndisabled=\n", encoding="utf-8")
    write_regex_plugin(tmp_path, enabled=False)
    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    regex_plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:regex_tools")

    assert regex_plugin["supported_in_tauri"] is True
    assert regex_plugin["status"] == "ready"
    assert regex_plugin["enabled"] is False
