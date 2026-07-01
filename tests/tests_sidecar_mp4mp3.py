from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_mp4mp3(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-mp4mp3-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "mp4mp3", "--input", str(input_path)],
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


def test_mp4mp3_probe_reports_ffmpeg_status() -> None:
    events = run_mp4mp3({"task_id": "mp4mp3-001", "action": "probe", "payload": {}})

    event = events[-1]
    assert event["type"] == "result"
    assert isinstance(event["data"]["available"], bool)
    assert isinstance(event["data"]["message"], str)


def test_mp4mp3_lists_mp4_files_recursively() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-mp4mp3-files-") as tmp:
        root = Path(tmp)
        (root / "a.mp4").write_bytes(b"mp4")
        (root / "ignore.txt").write_text("ignore", encoding="utf-8")
        nested = root / "nested"
        nested.mkdir()
        (nested / "b.MP4").write_bytes(b"mp4")

        events = run_mp4mp3(
            {
                "task_id": "mp4mp3-002",
                "action": "list",
                "payload": {"paths": [str(root)]},
            },
        )

    event = events[-1]
    assert event["type"] == "result"
    assert [item["name"] for item in event["data"]["files"]] == ["a.mp4", "b.MP4"]


def test_mp4mp3_convert_uses_legacy_converter(monkeypatch) -> None:
    from sidecar.tools import mp4mp3_tool

    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-mp4mp3-files-") as tmp:
        root = Path(tmp)
        source = root / "clip.mp4"
        output_dir = root / "out"
        source.write_bytes(b"mp4")

        def fake_convert_mp4_to_mp3(input_path: Path, output_path: Path, overwrite: bool = True) -> Path:
            assert input_path == source.resolve()
            assert output_path == output_dir.resolve() / "clip.mp3"
            assert overwrite is False
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"mp3")
            return output_path

        fake_module = SimpleNamespace(
            ensure_ffmpeg=lambda: "ffmpeg",
            convert_mp4_to_mp3=fake_convert_mp4_to_mp3,
        )
        monkeypatch.setattr(mp4mp3_tool, "_load_converter_module", lambda: fake_module)

        result = mp4mp3_tool.run_mp4mp3(
            {
                "task_id": "mp4mp3-003",
                "action": "convert",
                "payload": {
                    "paths": [str(source)],
                    "output_dir": str(output_dir),
                    "overwrite": False,
                },
            },
        )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 0
    assert result["data"]["results"][0]["source"] == str(source.resolve())
    assert result["data"]["results"][0]["output"].endswith("clip.mp3")


def test_mp4mp3_convert_requires_output_dir() -> None:
    events = run_mp4mp3(
        {
            "task_id": "mp4mp3-004",
            "action": "convert",
            "payload": {"paths": ["clip.mp4"]},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
