from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_batchrename(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-batchrename-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "batchrename", "--input", str(input_path)],
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


def test_batchrename_preview_builds_plan_without_renaming() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-batchrename-files-") as tmp:
        root = Path(tmp)
        (root / "b.txt").write_text("b", encoding="utf-8")
        (root / "a.txt").write_text("a", encoding="utf-8")

        events = run_batchrename(
            {
                "task_id": "batchrename-001",
                "action": "preview",
                "payload": {
                    "folder_path": str(root),
                    "prefix": "Doc",
                    "group_mode": "all",
                    "sort_mode": "name",
                    "sort_order": "asc",
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["total_files"] == 2
        assert [item["source_name"] for item in event["data"]["plan"]] == ["a.txt", "b.txt"]
        assert [item["target_name"] for item in event["data"]["plan"]] == ["Doc_001.txt", "Doc_002.txt"]
        assert (root / "a.txt").exists()
        assert (root / "b.txt").exists()


def test_batchrename_apply_renames_files_and_reports_results() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-batchrename-files-") as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("a", encoding="utf-8")
        (root / "b.txt").write_text("b", encoding="utf-8")

        events = run_batchrename(
            {
                "task_id": "batchrename-002",
                "action": "rename",
                "payload": {
                    "folder_path": str(root),
                    "prefix": "Renamed",
                    "group_mode": "all",
                    "sort_mode": "name",
                    "sort_order": "asc",
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["success_count"] == 2
        assert event["data"]["fail_count"] == 0
        assert [item["target_name"] for item in event["data"]["results"]] == ["Renamed_001.txt", "Renamed_002.txt"]
        assert (root / "Renamed_001.txt").read_text(encoding="utf-8") == "a"
        assert (root / "Renamed_002.txt").read_text(encoding="utf-8") == "b"
        assert not (root / "a.txt").exists()


def test_batchrename_rejects_invalid_prefix() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-batchrename-files-") as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("a", encoding="utf-8")
        events = run_batchrename(
            {
                "task_id": "batchrename-003",
                "action": "preview",
                "payload": {
                    "folder_path": str(root),
                    "prefix": "bad/name",
                    "group_mode": "all",
                    "sort_mode": "name",
                    "sort_order": "asc",
                },
            },
        )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"


def test_batchrename_requires_folder_path() -> None:
    events = run_batchrename(
        {
            "task_id": "batchrename-004",
            "action": "preview",
            "payload": {"prefix": "Doc"},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
