from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(tool: str, task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-") as tmp:
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


def test_json_tools_formats_minifies_and_validates_json() -> None:
    format_event = last_event(
        run_plugin(
            "plugin:json_tools",
            {
                "task_id": "json-format",
                "action": "format",
                "payload": {"text": '{"b":2,"a":1}', "indent": 4, "sort_keys": True},
            },
        )
    )
    assert format_event["type"] == "result"
    assert format_event["data"]["text"] == '{\n    "a": 1,\n    "b": 2\n}'

    minify_event = last_event(
        run_plugin(
            "plugin:json_tools",
            {
                "task_id": "json-minify",
                "action": "minify",
                "payload": {"text": '{\n  "a": 1,\n  "b": 2\n}'},
            },
        )
    )
    assert minify_event["type"] == "result"
    assert minify_event["data"]["text"] == '{"a":1,"b":2}'

    validate_event = last_event(
        run_plugin(
            "plugin:json_tools",
            {
                "task_id": "json-validate",
                "action": "validate",
                "payload": {"text": "[1,2,3]"},
            },
        )
    )
    assert validate_event["type"] == "result"
    assert validate_event["data"]["valid"] is True
    assert validate_event["data"]["type"] == "list"
    assert validate_event["data"]["items"] == 3


def test_json_tools_rejects_invalid_json() -> None:
    event = last_event(
        run_plugin(
            "plugin:json_tools",
            {
                "task_id": "json-invalid",
                "action": "format",
                "payload": {"text": '{"a":'},
            },
        )
    )
    assert event["type"] == "error"
    assert event["task_id"] == "json-invalid"
    assert event["code"] == "INVALID_PAYLOAD"


def test_uuid_tools_generate_normalize_validate_and_describe() -> None:
    generate_event = last_event(
        run_plugin(
            "plugin:uuid_tools",
            {
                "task_id": "uuid-generate",
                "action": "generate",
                "payload": {"count": 2, "uppercase": True, "hyphenated": False},
            },
        )
    )
    assert generate_event["type"] == "result"
    generated = generate_event["data"]["items"]
    assert len(generated) == 2
    assert all(len(item) == 32 and item == item.upper() and "-" not in item for item in generated)

    normalize_event = last_event(
        run_plugin(
            "plugin:uuid_tools",
            {
                "task_id": "uuid-normalize",
                "action": "normalize",
                "payload": {"text": "550E8400E29B41D4A716446655440000", "hyphenated": True},
            },
        )
    )
    assert normalize_event["type"] == "result"
    assert normalize_event["data"]["text"] == "550e8400-e29b-41d4-a716-446655440000"

    validate_event = last_event(
        run_plugin(
            "plugin:uuid_tools",
            {
                "task_id": "uuid-validate",
                "action": "validate",
                "payload": {"text": "not-a-uuid"},
            },
        )
    )
    assert validate_event["type"] == "result"
    assert validate_event["data"]["valid"] is False

    describe_event = last_event(
        run_plugin(
            "plugin:uuid_tools",
            {
                "task_id": "uuid-describe",
                "action": "describe",
                "payload": {"text": "550e8400-e29b-41d4-a716-446655440000"},
            },
        )
    )
    assert describe_event["type"] == "result"
    assert describe_event["data"]["canonical"] == "550e8400-e29b-41d4-a716-446655440000"
    assert describe_event["data"]["version"] == 4


def test_uuid_tools_rejects_bad_count() -> None:
    event = last_event(
        run_plugin(
            "plugin:uuid_tools",
            {
                "task_id": "uuid-bad-count",
                "action": "generate",
                "payload": {"count": 501},
            },
        )
    )
    assert event["type"] == "error"
    assert event["task_id"] == "uuid-bad-count"
    assert event["code"] == "INVALID_PAYLOAD"
