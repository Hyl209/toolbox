from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_base64(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-base64-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "base64", "--input", str(input_path)],
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


def test_base64_encodes_text() -> None:
    events = run_base64(
        {"task_id": "base64-001", "action": "encode_text", "payload": {"text": "hello"}},
    )

    event = last_event(events)
    assert event["type"] == "result"
    assert event["task_id"] == "base64-001"
    assert event["data"]["text"] == "aGVsbG8="


def test_base64_decodes_text() -> None:
    events = run_base64(
        {"task_id": "base64-002", "action": "decode_text", "payload": {"text": "aGVsbG8="}},
    )

    event = last_event(events)
    assert event["type"] == "result"
    assert event["task_id"] == "base64-002"
    assert event["data"]["text"] == "hello"


def test_base64_requires_payload_text() -> None:
    events = run_base64(
        {"task_id": "base64-003", "action": "encode_text", "payload": {}},
    )

    event = last_event(events)
    assert event["type"] == "error"
    assert event["task_id"] == "base64-003"
    assert event["code"] == "INVALID_PAYLOAD"


def test_base64_rejects_unknown_action() -> None:
    events = run_base64(
        {"task_id": "base64-004", "action": "rot13", "payload": {"text": "hello"}},
    )

    event = last_event(events)
    assert event["type"] == "error"
    assert event["task_id"] == "base64-004"
    assert event["code"] == "UNKNOWN_ACTION"


def test_base64_encodes_file_and_saves_text() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-base64-file-") as tmp:
        root = Path(tmp)
        source = root / "sample.txt"
        output_dir = root / "out"
        source.write_text("hello", encoding="utf-8")

        events = run_base64(
            {
                "task_id": "base64-005",
                "action": "encode_file",
                "payload": {
                    "file_path": str(source),
                    "output_dir": str(output_dir),
                    "output_name": "sample-base64",
                    "data_url": True,
                },
            },
        )

        event = last_event(events)
        saved_path = Path(event["data"]["output_path"])
        assert event["type"] == "result"
        assert event["data"]["text"] == "data:text/plain;base64,aGVsbG8="
        assert saved_path.name == "sample-base64.txt"
        assert saved_path.read_text(encoding="utf-8") == event["data"]["text"]


def test_base64_decodes_text_to_file() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-base64-file-") as tmp:
        output_dir = Path(tmp) / "out"

        events = run_base64(
            {
                "task_id": "base64-006",
                "action": "decode_file",
                "payload": {
                    "text": "data:text/plain;base64,aGVsbG8=",
                    "output_dir": str(output_dir),
                    "output_name": "restored",
                },
            },
        )

        event = last_event(events)
        output_path = Path(event["data"]["output_path"])
        assert event["type"] == "result"
        assert output_path.name == "restored.txt"
        assert output_path.read_text(encoding="utf-8") == "hello"
