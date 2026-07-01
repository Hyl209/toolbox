from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_directdownloader(task: dict) -> tuple[int, list[dict], str]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-directdownloader-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "directdownloader", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line]
    return proc.returncode, lines, proc.stderr


def last_event(task: dict) -> dict:
    code, events, stderr = run_directdownloader(task)
    assert stderr == ""
    assert events, "sidecar produced no stdout"
    if events[-1]["type"] != "error":
        assert code == 0
    return events[-1]


def test_directdownloader_probe_returns_shape_even_without_aria2() -> None:
    event = last_event({"task_id": "direct-probe-001", "action": "probe", "payload": {}})

    assert event["type"] == "result"
    assert isinstance(event["data"]["available"], bool)
    assert isinstance(event["data"]["path"], str)
    assert event["data"]["default_connections"] == 16


def test_directdownloader_parse_plain_url_and_aria2_command() -> None:
    event = last_event(
        {
            "task_id": "direct-parse-001",
            "action": "parse",
            "payload": {
                "url_text": "https://cdn.example.com/plain.zip\n"
                "aria2c \"https://cdn.example.com/cmd.rar\" --out \"cmd.rar\" "
                "--header \"Cookie:a=b\" --referer \"https://pan.example.com/\""
            },
        }
    )

    assert event["type"] == "result"
    assert [(item["url"], item["output_name"]) for item in event["data"]["requests"]] == [
        ("https://cdn.example.com/plain.zip", ""),
        ("https://cdn.example.com/cmd.rar", "cmd.rar"),
    ]
    command_request = event["data"]["requests"][1]
    assert command_request["extra_headers"] == ["Cookie:a=b"]
    assert command_request["referer"] == "https://pan.example.com/"
    assert command_request["guess_filename"] == "cmd.rar"


def test_directdownloader_validate_rejects_shared_output_name_for_multiple_urls(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "direct-validate-001",
            "action": "validate",
            "payload": {
                "url_text": "https://a.test/a.zip\nhttps://b.test/b.zip",
                "output_dir": str(tmp_path),
                "connections": 16,
                "output_name": "pack.zip",
            },
        }
    )

    assert event["type"] == "result"
    assert event["data"]["valid"] is False
    assert event["data"]["errors"]


def test_directdownloader_build_commands_includes_download_options(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "direct-build-001",
            "action": "build_commands",
            "payload": {
                "url_text": "https://cdn.example.com/archive.zip",
                "output_dir": str(tmp_path),
                "output_name": "archive.zip",
                "connections": 8,
                "proxy_host": "127.0.0.1",
                "proxy_port": "7890",
                "referer": "https://pan.example.com/",
                "extra_headers": ["User-Agent:Test"],
                "overwrite": True,
                "output_subdir_by_filename": True,
            },
        }
    )

    assert event["type"] == "result"
    item = event["data"]["commands"][0]
    command = item["command"]
    assert command[-1] == "https://cdn.example.com/archive.zip"
    assert command[command.index("-x") : command.index("-x") + 2] == ["-x", "8"]
    assert command[command.index("-s") : command.index("-s") + 2] == ["-s", "8"]
    assert command[command.index("-o") : command.index("-o") + 2] == ["-o", "archive.zip"]
    assert command[command.index("-d") : command.index("-d") + 2] == ["-d", str(tmp_path / "archive")]
    assert "--all-proxy=http://127.0.0.1:7890" in command
    assert "--referer=https://pan.example.com/" in command
    assert "--header=User-Agent:Test" in command


def test_directdownloader_unknown_action_returns_error() -> None:
    event = last_event({"task_id": "direct-bogus-001", "action": "bogus", "payload": {}})

    assert event["type"] == "error"
    assert event["code"] == "UNKNOWN_ACTION"


def test_directdownloader_rejects_invalid_payload() -> None:
    event = last_event({"task_id": "direct-invalid-001", "action": "parse", "payload": []})

    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"


def test_directdownloader_downloads_from_local_http_without_ansi_logs(tmp_path: Path) -> None:
    probe = last_event({"task_id": "direct-probe-download", "action": "probe", "payload": {}})
    if not probe["data"]["available"]:
        pytest.skip("aria2c is not available")

    serve_dir = tmp_path / "serve"
    output_dir = tmp_path / "out"
    serve_dir.mkdir()
    output_dir.mkdir()
    (serve_dir / "hello.txt").write_text("hello direct download", encoding="utf-8")

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(serve_dir)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        event = last_event(
            {
                "task_id": "direct-download-local",
                "action": "download",
                "payload": {
                    "url_text": f"http://127.0.0.1:{port}/hello.txt",
                    "output_dir": str(output_dir),
                    "connections": 1,
                    "overwrite": True,
                },
            }
        )
    finally:
        server.shutdown()
        server.server_close()

    assert event["type"] == "result"
    assert (output_dir / "hello.txt").read_text(encoding="utf-8") == "hello direct download"
    assert event["data"]["success_count"] == 1
    text = json.dumps(event["data"], ensure_ascii=False)
    assert "\x1b[" not in text
