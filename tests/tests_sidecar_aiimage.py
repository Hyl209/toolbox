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
