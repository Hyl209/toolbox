from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(tool: str, task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-timestamp-csv-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", tool, "--input", str(input_path)],
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


def test_timestamp_tools_convert_both_directions_and_current_time() -> None:
    to_datetime = last_event(
        run_plugin(
            "plugin:timestamp_tools",
            {
                "task_id": "ts-to-datetime",
                "action": "to_datetime",
                "payload": {"text": "1704067200", "tz_offset": "+08:00", "unit": "seconds"},
            },
        )
    )
    assert to_datetime["type"] == "result"
    assert to_datetime["data"]["datetime"] == "2024-01-01 08:00:00"
    assert to_datetime["data"]["unit"] == "seconds"

    to_timestamp = last_event(
        run_plugin(
            "plugin:timestamp_tools",
            {
                "task_id": "ts-to-timestamp",
                "action": "to_timestamp",
                "payload": {"text": "2024-01-01 08:00:00", "tz_offset": "+08:00"},
            },
        )
    )
    assert to_timestamp["type"] == "result"
    assert to_timestamp["data"]["seconds"] == 1704067200
    assert to_timestamp["data"]["milliseconds"] == 1704067200000

    current = last_event(
        run_plugin(
            "plugin:timestamp_tools",
            {
                "task_id": "ts-current",
                "action": "current_time",
                "payload": {"tz_offset": "UTC"},
            },
        )
    )
    assert current["type"] == "result"
    assert isinstance(current["data"]["seconds"], int)
    assert isinstance(current["data"]["milliseconds"], int)
    assert current["data"]["iso"].endswith("+00:00")


def test_timestamp_tools_reject_invalid_payload_and_action() -> None:
    bad_payload = last_event(
        run_plugin(
            "plugin:timestamp_tools",
            {"task_id": "ts-bad", "action": "to_datetime", "payload": {"text": "not-a-number"}},
        )
    )
    assert bad_payload["type"] == "error"
    assert bad_payload["code"] == "INVALID_PAYLOAD"

    bad_action = last_event(
        run_plugin(
            "plugin:timestamp_tools",
            {"task_id": "ts-action", "action": "missing", "payload": {}},
        )
    )
    assert bad_action["type"] == "error"
    assert bad_action["code"] == "UNKNOWN_ACTION"


def test_csv_tools_format_tsv_json_and_summary() -> None:
    source = 'name,score\n"Alice, A",10\nBob,9'
    formatted = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-format", "action": "format", "payload": {"text": source, "delimiter": ","}},
        )
    )
    assert formatted["type"] == "result"
    assert formatted["data"]["text"] == 'name,score\n"Alice, A",10\nBob,9'

    tsv = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-tsv", "action": "to_tsv", "payload": {"text": source}},
        )
    )
    assert tsv["type"] == "result"
    assert tsv["data"]["text"] == "name\tscore\nAlice, A\t10\nBob\t9"

    as_json = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-json", "action": "to_json", "payload": {"text": source, "has_header": True}},
        )
    )
    assert as_json["type"] == "result"
    assert json.loads(as_json["data"]["text"]) == [
        {"name": "Alice, A", "score": "10"},
        {"name": "Bob", "score": "9"},
    ]

    summary = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-summary", "action": "summary", "payload": {"text": source}},
        )
    )
    assert summary["type"] == "result"
    assert summary["data"] == {"rows": 3, "columns": 2}


def test_csv_tools_support_no_header_json_and_reject_errors() -> None:
    no_header = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-no-header", "action": "to_json", "payload": {"text": "a,b\nc,d", "has_header": False}},
        )
    )
    assert no_header["type"] == "result"
    assert json.loads(no_header["data"]["text"]) == [["a", "b"], ["c", "d"]]

    bad_payload = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-bad", "action": "format", "payload": {"text": ""}},
        )
    )
    assert bad_payload["type"] == "error"
    assert bad_payload["code"] == "INVALID_PAYLOAD"

    bad_action = last_event(
        run_plugin(
            "plugin:csv_tools",
            {"task_id": "csv-action", "action": "missing", "payload": {"text": "a,b"}},
        )
    )
    assert bad_action["type"] == "error"
    assert bad_action["code"] == "UNKNOWN_ACTION"
