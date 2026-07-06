from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_aiimage(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-aiimage-") as tmp:
        root = Path(tmp)
        input_path = root / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "aiimage", "--input", str(input_path)],
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


def test_aiimage_sidecar_load_config_returns_defaults_for_temp_settings() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-aiimage-settings-") as tmp:
        events = run_aiimage(
            {
                "task_id": "aiimage-001",
                "action": "load_config",
                "payload": {"settings_path": str(Path(tmp) / "hyl_toolbox.ini")},
            }
        )

    event = events[-1]
    assert event["type"] == "result"
    assert event["task_id"] == "aiimage-001"
    assert event["data"]["profiles"] == []
    assert event["data"]["default_size"] == "1024x1024"


def test_aiimage_sidecar_save_config_persists_profile_with_api_key_when_keyring_missing() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-aiimage-settings-") as tmp:
        settings_path = Path(tmp) / "hyl_toolbox.ini"
        events = run_aiimage(
            {
                "task_id": "aiimage-save-001",
                "action": "save_config",
                "payload": {
                    "settings_path": str(settings_path),
                    "selected_profile_id": "main",
                    "profiles": [
                        {
                            "id": "main",
                            "name": "Main",
                            "base_url": "https://example.test/v1",
                            "model": "gpt-image-2",
                            "api_key": "sk-test",
                        }
                    ],
                },
            }
        )

        loaded_events = run_aiimage(
            {
                "task_id": "aiimage-load-001",
                "action": "load_config",
                "payload": {"settings_path": str(settings_path)},
            }
        )

    event = events[-1]
    assert event["type"] == "result"
    assert event["task_id"] == "aiimage-save-001"
    assert event["data"]["selected_profile_id"] == "main"
    assert event["data"]["profiles"][0]["name"] == "Main"
    assert "api_key" not in event["data"]["profiles"][0]
    assert loaded_events[-1]["data"]["profiles"][0]["id"] == "main"


def test_aiimage_sidecar_load_delete_and_clear_history_actions() -> None:
    from sidecar.history_store import append_history

    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-aiimage-history-") as tmp:
        settings_path = Path(tmp) / "hyl_toolbox.ini"
        append_history("aiimage", {"id": "hist-1", "prompt": "cat"}, settings_path=settings_path)
        append_history("aiimage", {"id": "hist-2", "prompt": "dog"}, settings_path=settings_path)

        loaded_events = run_aiimage(
            {
                "task_id": "aiimage-history-load",
                "action": "load_history",
                "payload": {"settings_path": str(settings_path)},
            }
        )
        deleted_events = run_aiimage(
            {
                "task_id": "aiimage-history-delete",
                "action": "delete_history",
                "payload": {"settings_path": str(settings_path), "id": "hist-1"},
            }
        )
        cleared_events = run_aiimage(
            {
                "task_id": "aiimage-history-clear",
                "action": "clear_history",
                "payload": {"settings_path": str(settings_path)},
            }
        )

    assert [item["id"] for item in loaded_events[-1]["data"]["items"]] == ["hist-2", "hist-1"]
    assert [item["id"] for item in deleted_events[-1]["data"]["items"]] == ["hist-2"]
    assert cleared_events[-1]["data"]["items"] == []
