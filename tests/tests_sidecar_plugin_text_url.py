from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(tool: str, task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-text-url-") as tmp:
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


def test_text_tools_clean_dedupe_sort_and_transform_case() -> None:
    clean_event = last_event(
        run_plugin(
            "plugin:text_tools",
            {
                "task_id": "text-clean",
                "action": "clean_lines",
                "payload": {"text": "  Alpha  \n\n beta \r\n", "trim": True, "drop_empty": True},
            },
        )
    )
    assert clean_event["type"] == "result"
    assert clean_event["data"]["text"] == "Alpha\nbeta"

    dedupe_event = last_event(
        run_plugin(
            "plugin:text_tools",
            {
                "task_id": "text-dedupe",
                "action": "dedupe_lines",
                "payload": {"text": "Alpha\nalpha\nBeta", "case_sensitive": False, "trim": True},
            },
        )
    )
    assert dedupe_event["type"] == "result"
    assert dedupe_event["data"]["text"] == "Alpha\nBeta"

    sort_event = last_event(
        run_plugin(
            "plugin:text_tools",
            {
                "task_id": "text-sort",
                "action": "sort_lines",
                "payload": {"text": "b\nA\nc", "case_sensitive": False, "reverse": True},
            },
        )
    )
    assert sort_event["type"] == "result"
    assert sort_event["data"]["text"] == "c\nb\nA"

    case_event = last_event(
        run_plugin(
            "plugin:text_tools",
            {
                "task_id": "text-case",
                "action": "transform_case",
                "payload": {"text": "hello hyl", "mode": "title"},
            },
        )
    )
    assert case_event["type"] == "result"
    assert case_event["data"]["text"] == "Hello Hyl"


def test_url_tools_encode_decode_query_and_summarize() -> None:
    encode_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {"task_id": "url-encode", "action": "encode", "payload": {"text": "a b/中文", "safe": "/"}},
        )
    )
    assert encode_event["type"] == "result"
    assert encode_event["data"]["text"] == "a%20b/%E4%B8%AD%E6%96%87"

    decode_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {"task_id": "url-decode", "action": "decode", "payload": {"text": "a%20b/%E4%B8%AD%E6%96%87"}},
        )
    )
    assert decode_event["type"] == "result"
    assert decode_event["data"]["text"] == "a b/中文"

    parse_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {
                "task_id": "url-parse",
                "action": "parse_query",
                "payload": {"text": "https://example.com/search?q=hyl&empty="},
            },
        )
    )
    assert parse_event["type"] == "result"
    assert parse_event["data"]["pairs"] == [["q", "hyl"], ["empty", ""]]

    format_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {"task_id": "url-format", "action": "format_query", "payload": {"text": "?q=hyl&page=1"}},
        )
    )
    assert format_event["type"] == "result"
    assert "q    = hyl" in format_event["data"]["text"]
    assert "page = 1" in format_event["data"]["text"]

    build_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {
                "task_id": "url-build",
                "action": "build_query",
                "payload": {"pairs": [["q", "hyl tools"], ["page", "1"]]},
            },
        )
    )
    assert build_event["type"] == "result"
    assert build_event["data"]["text"] == "q=hyl+tools&page=1"

    summarize_event = last_event(
        run_plugin(
            "plugin:url_tools",
            {
                "task_id": "url-summary",
                "action": "summarize",
                "payload": {"text": "https://example.com/a/b?q=1#top"},
            },
        )
    )
    assert summarize_event["type"] == "result"
    assert summarize_event["data"]["host"] == "example.com"
    assert summarize_event["data"]["path"] == "/a/b"
    assert summarize_event["data"]["query"] == "q=1"
