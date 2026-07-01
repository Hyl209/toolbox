from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_same(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-same-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "same", "--input", str(input_path)],
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


def test_same_scan_finds_exact_duplicate_group_without_moving() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-same-files-") as tmp:
        root = Path(tmp)
        (root / "a.bin").write_bytes(b"same-bytes")
        (root / "b.dat").write_bytes(b"same-bytes")
        (root / "c.bin").write_bytes(b"different")

        events = run_same(
            {
                "task_id": "same-001",
                "action": "scan",
                "payload": {"folder_path": str(root), "recursive": False, "target_dir_name": "dups"},
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["scanned_files"] == 3
        assert event["data"]["duplicate_group_count"] == 1
        assert event["data"]["duplicate_file_count"] == 1
        group = event["data"]["groups"][0]
        assert Path(group["keeper"]).name == "a.bin"
        assert [Path(item).name for item in group["duplicates"]] == ["b.dat"]
        assert (root / "b.dat").exists()
        assert not (root / "dups").exists()


def test_same_move_uses_scan_result_and_moves_duplicates() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-same-files-") as tmp:
        root = Path(tmp)
        (root / "a.bin").write_bytes(b"same-bytes")
        (root / "b.dat").write_bytes(b"same-bytes")

        scan = run_same(
            {
                "task_id": "same-002-scan",
                "action": "scan",
                "payload": {"folder_path": str(root), "recursive": False, "target_dir_name": "dups"},
            },
        )[-1]["data"]
        events = run_same(
            {
                "task_id": "same-002-move",
                "action": "move",
                "payload": {"folder_path": str(root), "scan_result": scan},
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        assert event["data"]["success_count"] == 1
        assert event["data"]["fail_count"] == 0
        assert Path(event["data"]["results"][0]["target_path"]).name == "b.dat"
        assert not (root / "b.dat").exists()
        assert (root / "dups" / "b.dat").read_bytes() == b"same-bytes"


def test_same_scan_honors_recursive_flag() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-same-files-") as tmp:
        root = Path(tmp)
        nested = root / "nested"
        nested.mkdir()
        (root / "a.bin").write_bytes(b"same-bytes")
        (nested / "b.bin").write_bytes(b"same-bytes")

        top_level = run_same(
            {
                "task_id": "same-003-a",
                "action": "scan",
                "payload": {"folder_path": str(root), "recursive": False, "target_dir_name": "dups"},
            },
        )[-1]
        recursive = run_same(
            {
                "task_id": "same-003-b",
                "action": "scan",
                "payload": {"folder_path": str(root), "recursive": True, "target_dir_name": "dups"},
            },
        )[-1]

        assert top_level["data"]["duplicate_group_count"] == 0
        assert recursive["data"]["duplicate_group_count"] == 1


def test_same_requires_folder_path() -> None:
    events = run_same({"task_id": "same-004", "action": "scan", "payload": {}})

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
