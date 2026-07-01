from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"
IMAGE = "图片"
AUDIO = "音频"
DOCUMENT = "文档"


def run_filesorter(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-filesorter-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "filesorter", "--input", str(input_path)],
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


def test_filesorter_preview_summarizes_selected_categories_without_moving() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-filesorter-files-") as tmp:
        root = Path(tmp)
        (root / "photo.png").write_bytes(b"png")
        (root / "song.mp3").write_bytes(b"mp3")
        (root / "note.txt").write_text("note", encoding="utf-8")

        events = run_filesorter(
            {
                "task_id": "filesorter-001",
                "action": "preview",
                "payload": {
                    "folder_path": str(root),
                    "mode": "category",
                    "selected_categories": [IMAGE, AUDIO],
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["mode"] == "category"
        assert event["data"]["total_files"] == 3
        assert event["data"]["selected_total_files"] == 2
        assert event["data"]["category_counts"][IMAGE] == 1
        assert event["data"]["category_counts"][AUDIO] == 1
        assert [item["name"] for item in event["data"]["files"]] == ["note.txt", "photo.png", "song.mp3"]
        assert (root / "photo.png").exists()
        assert not (root / IMAGE).exists()


def test_filesorter_sort_moves_only_selected_category() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-filesorter-files-") as tmp:
        root = Path(tmp)
        (root / "photo.png").write_bytes(b"png")
        (root / "note.txt").write_text("note", encoding="utf-8")

        events = run_filesorter(
            {
                "task_id": "filesorter-002",
                "action": "sort",
                "payload": {
                    "folder_path": str(root),
                    "mode": "category",
                    "selected_categories": [IMAGE],
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["success_count"] == 1
        assert event["data"]["fail_count"] == 0
        assert event["data"]["results"][0]["source_name"] == "photo.png"
        assert event["data"]["results"][0]["group_label"] == IMAGE
        assert (root / IMAGE / "photo.png").exists()
        assert (root / "note.txt").exists()


def test_filesorter_rejects_missing_folder_path() -> None:
    events = run_filesorter(
        {
            "task_id": "filesorter-003",
            "action": "preview",
            "payload": {"selected_categories": [IMAGE]},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"


def test_filesorter_rejects_nonexistent_folder() -> None:
    events = run_filesorter(
        {
            "task_id": "filesorter-004",
            "action": "preview",
            "payload": {"folder_path": "Z:/definitely-missing-hyl-folder"},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
