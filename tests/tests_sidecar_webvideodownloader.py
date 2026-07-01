from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"



@contextlib.contextmanager
def local_http_server(root: Path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}"
        finally:
            server.shutdown()
            thread.join(timeout=5)


def run_webvideo(task: dict) -> tuple[int, list[dict], str]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-webvideo-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "webvideodownloader", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line]
    return proc.returncode, lines, proc.stderr


def last_event(task: dict) -> dict:
    code, events, stderr = run_webvideo(task)
    assert stderr == ""
    assert events, "sidecar produced no stdout"
    if events[-1]["type"] != "error":
        assert code == 0
    return events[-1]


def test_webvideodownloader_probe_returns_backend_map() -> None:
    event = last_event({"task_id": "web-probe-001", "action": "probe", "payload": {}})

    assert event["type"] == "result"
    assert {"telethon", "yt_dlp", "aria2c", "ffmpeg"}.issubset(event["data"]["backends"])
    assert isinstance(event["data"]["backends"]["yt_dlp"]["available"], bool)


def test_webvideodownloader_manifest_marks_ready() -> None:
    from sidecar.tool_manifest import build_manifest, load_tool_definitions

    item = next(tool for tool in build_manifest(load_tool_definitions()) if tool["id"] == "webvideodownloader")

    assert item["supported_in_tauri"] is True
    assert item["status"] == "ready"


def test_webvideodownloader_parse_builds_tasks_and_counts() -> None:
    event = last_event(
        {
            "task_id": "web-parse-001",
            "action": "parse",
            "payload": {"text": "https://example.com/a\nhttps://example.com/a\nhttps://example.com/b"},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["urls"] == ["https://example.com/a", "https://example.com/b"]
    assert event["data"]["url_count"] == 2
    assert event["data"]["task_count"] == 2
    assert event["data"]["tasks"][0]["source_kind"] == "web"


def test_webvideodownloader_parse_reports_invalid_share_text_without_internal_error() -> None:
    event = last_event(
        {
            "task_id": "web-parse-mixed",
            "action": "parse",
            "payload": {"text": "hello\nhttps://example.com/a"},
        }
    )

    assert event["type"] == "result"
    assert event["task_id"] == "web-parse-mixed"
    assert event["data"]["urls"] == ["hello", "https://example.com/a"]
    assert event["data"]["tasks"] == []
    assert event["data"]["errors"] == ["\u65e0\u6548\u94fe\u63a5: hello"]


def test_webvideodownloader_validate_good_request(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "web-validate-good",
            "action": "validate",
            "payload": {"urls": ["https://example.com/video"], "output_dir": str(tmp_path), "options": {}},
        }
    )

    assert event["type"] == "result"
    assert event["data"] == {"valid": True, "errors": []}


def test_webvideodownloader_validate_bad_request() -> None:
    event = last_event(
        {
            "task_id": "web-validate-bad",
            "action": "validate",
            "payload": {"text": "", "output_dir": "", "options": {}},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["valid"] is False
    assert len(event["data"]["errors"]) >= 2


def test_webvideodownloader_inspect_batch_monkeypatch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from sidecar.tools import webvideodownloader_tool as tool

    def fake_batch(urls, progress_cb=None, options=None):
        assert urls == ["https://example.com/a"]
        assert options.proxy_url == "http://127.0.0.1:7890"
        if progress_cb:
            progress_cb("scan ok")
        return [
            {
                "source_url": "https://example.com/a",
                "success": True,
                "candidate_count": 1,
                "candidates": ["https://cdn.example.com/a.mp4"],
                "source": "fake",
                "error": "",
            }
        ]

    module = tool._load_converter_module()
    monkeypatch.setattr(module, "inspect_web_media_batch", fake_batch)

    result = tool.run_webvideodownloader(
        {
            "task_id": "web-inspect-001",
            "action": "inspect",
            "payload": {"urls": ["https://example.com/a"], "options": {"proxy_url": "http://127.0.0.1:7890"}},
        }
    )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 0
    assert result["data"]["results"][0]["candidates"] == ["https://cdn.example.com/a.mp4"]
    assert result["data"]["logs"] == ["scan ok"]


def test_webvideodownloader_inspect_mixed_share_text_reports_input_errors() -> None:
    event = last_event(
        {
            "task_id": "web-inspect-mixed",
            "action": "inspect",
            "payload": {"text": "hello\nhttps://example.com/a"},
        }
    )

    assert event["type"] == "result"
    assert event["task_id"] == "web-inspect-mixed"
    assert event["data"]["results"] == []
    assert event["data"]["success_count"] == 0
    assert event["data"]["fail_count"] == 0
    assert event["data"]["errors"] == ["\u65e0\u6548\u94fe\u63a5: hello"]



def test_webvideodownloader_download_batch_monkeypatch_passes_legacy_arguments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from sidecar.tools import webvideodownloader_tool as tool

    captured: dict[str, object] = {}

    def fake_download_batch(tasks, output_dir, telegram_config=None, options=None, progress_cb=None):
        task_list = list(tasks)
        captured["tasks"] = task_list
        captured["output_dir"] = output_dir
        captured["telegram_config"] = telegram_config
        captured["options"] = options
        if progress_cb:
            progress_cb("download started")
        return [
            {
                "source_url": task_list[0].source_url,
                "source_kind": task_list[0].source_kind,
                "success": True,
                "error": "",
                "files": [str(tmp_path / "sample.mp4")],
            }
        ]

    module = tool._load_converter_module()
    monkeypatch.setattr(module, "download_batch", fake_download_batch)

    result = tool.run_webvideodownloader(
        {
            "task_id": "web-download-001",
            "action": "download",
            "payload": {
                "urls": ["https://example.com/a"],
                "output_dir": str(tmp_path),
                "options": {"proxy_host": "127.0.0.1", "proxy_port": "7890", "overwrite": True},
            },
        }
    )

    assert result["ok"] is True
    assert captured["output_dir"] == str(tmp_path)
    assert captured["telegram_config"] is None
    assert len(captured["tasks"]) == 1
    assert captured["tasks"][0].source_url == "https://example.com/a"
    assert captured["tasks"][0].source_kind == "web"
    assert captured["options"].proxy_url == "http://127.0.0.1:7890"
    assert captured["options"].overwrite is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 0
    assert result["data"]["files"] == [str(tmp_path / "sample.mp4")]
    assert result["data"]["logs"] == ["download started"]


def test_webvideodownloader_download_local_html_video(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    site = tmp_path / "site"
    media = site / "media"
    output = tmp_path / "downloads"
    media.mkdir(parents=True)
    expected = b"fake mp4 bytes from local server"
    (media / "sample.mp4").write_bytes(expected)
    (site / "index.html").write_text('<html><body><video src="/media/sample.mp4"></video></body></html>', encoding="utf-8")
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    (stub_dir / "yt_dlp.py").write_text(
        """import re\nfrom pathlib import Path\nfrom urllib.parse import urljoin\nfrom urllib.request import urlopen\n\nclass YoutubeDL:\n    def __init__(self, opts):\n        self.opts = opts\n    def __enter__(self):\n        return self\n    def __exit__(self, exc_type, exc, tb):\n        return False\n    def extract_info(self, url, download=False):\n        if not download:\n            return {'title': 'sample', 'id': 'local'}\n        html = urlopen(url, timeout=10).read().decode('utf-8')\n        match = re.search(r'<video[^>]+src=[\\"\\']([^\\"\\']+)', html)\n        media_url = urljoin(url, match.group(1) if match else '/media/sample.mp4')\n        data = urlopen(media_url, timeout=10).read()\n        outtmpl = self.opts['outtmpl']\n        path = Path(outtmpl.replace('%(ext)s', 'mp4'))\n        path.parent.mkdir(parents=True, exist_ok=True)\n        path.write_bytes(data)\n        return {'title': 'sample', 'id': 'local'}\n""",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(stub_dir) + os.pathsep + os.environ.get("PYTHONPATH", ""))

    with local_http_server(site) as base_url:
        event = last_event(
            {
                "task_id": "web-download-local",
                "action": "download",
                "payload": {"url": f"{base_url}/index.html", "output_dir": str(output), "options": {}},
            }
        )

    assert event["type"] == "result"
    assert event["data"]["success_count"] == 1
    assert event["data"]["fail_count"] == 0
    assert len(event["data"]["files"]) == 1
    downloaded = Path(event["data"]["files"][0])
    assert downloaded.exists()
    assert downloaded.read_bytes() == expected


def test_webvideodownloader_download_mixed_telegram_returns_structured_error(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "web-download-mixed",
            "action": "download",
            "payload": {"text": "https://example.com/a\nhttps://t.me/channel/1", "output_dir": str(tmp_path)},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["results"] == []
    assert event["data"]["success_count"] == 0
    assert event["data"]["fail_count"] == 0
    assert event["data"]["errors"]
    assert "only web URLs are supported" in event["data"]["errors"][0]


def test_webvideodownloader_unknown_action_returns_error() -> None:
    event = last_event({"task_id": "web-bogus-001", "action": "bogus", "payload": {}})

    assert event["type"] == "error"
    assert event["code"] == "UNKNOWN_ACTION"


def test_webvideodownloader_rejects_missing_payload() -> None:
    event = last_event({"task_id": "web-invalid-001", "action": "parse"})

    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
