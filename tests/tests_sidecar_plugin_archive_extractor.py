from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(task: dict) -> tuple[int, list[dict]]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-archive-extractor-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "plugin:archive_extractor", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    assert proc.stderr == ""
    lines = [line for line in proc.stdout.splitlines() if line]
    assert lines, "sidecar produced no stdout"
    return proc.returncode, [json.loads(line) for line in lines]


def last_event(events: list[dict]) -> dict:
    return events[-1]


def make_zip(tmp_path: Path) -> Path:
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("alpha.txt", "alpha")
        zf.writestr("nested/beta.txt", "beta")
    return archive


def make_tar(tmp_path: Path) -> Path:
    source = tmp_path / "tar-source"
    source.mkdir()
    (source / "alpha.txt").write_text("alpha", encoding="utf-8")
    nested = source / "nested"
    nested.mkdir()
    (nested / "beta.txt").write_text("beta", encoding="utf-8")
    archive = tmp_path / "sample.tar"
    with tarfile.open(archive, "w") as tf:
        tf.add(source / "alpha.txt", arcname="alpha.txt")
        tf.add(nested / "beta.txt", arcname="nested/beta.txt")
    return archive


def test_archive_extractor_detects_zip(tmp_path: Path) -> None:
    archive = make_zip(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "archive-detect-zip",
            "action": "detect",
            "payload": {"archive_path": str(archive)},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"] == {
        "archive_path": str(archive),
        "archive_type": "zip",
        "supported": True,
    }


def test_archive_extractor_detects_tar(tmp_path: Path) -> None:
    archive = make_tar(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "archive-detect-tar",
            "action": "detect",
            "payload": {"archive_path": str(archive)},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["archive_path"] == str(archive)
    assert event["data"]["archive_type"] == "tar"
    assert event["data"]["supported"] is True


def test_archive_extractor_extracts_zip(tmp_path: Path) -> None:
    archive = make_zip(tmp_path)
    output_dir = tmp_path / "zip-out"

    code, events = run_plugin(
        {
            "task_id": "archive-extract-zip",
            "action": "extract",
            "payload": {"archive_path": str(archive), "output_dir": str(output_dir)},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["archive_type"] == "zip"
    assert event["data"]["extracted_count"] == 2
    assert event["data"]["files"] == ["alpha.txt", "nested/beta.txt"]
    assert (output_dir / "alpha.txt").read_text(encoding="utf-8") == "alpha"
    assert (output_dir / "nested" / "beta.txt").read_text(encoding="utf-8") == "beta"


def test_archive_extractor_extracts_tar(tmp_path: Path) -> None:
    archive = make_tar(tmp_path)
    output_dir = tmp_path / "tar-out"

    code, events = run_plugin(
        {
            "task_id": "archive-extract-tar",
            "action": "extract",
            "payload": {"archive_path": str(archive), "output_dir": str(output_dir)},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["archive_type"] == "tar"
    assert event["data"]["extracted_count"] == 2
    assert event["data"]["files"] == ["alpha.txt", "nested/beta.txt"]


def test_archive_extractor_rejects_invalid_and_missing_archives(tmp_path: Path) -> None:
    invalid = tmp_path / "not-archive.txt"
    invalid.write_text("not an archive", encoding="utf-8")
    missing = tmp_path / "missing.zip"

    invalid_code, invalid_events = run_plugin(
        {
            "task_id": "archive-extract-invalid",
            "action": "extract",
            "payload": {"archive_path": str(invalid), "output_dir": str(tmp_path / "invalid-out")},
        }
    )
    missing_code, missing_events = run_plugin(
        {
            "task_id": "archive-extract-missing",
            "action": "extract",
            "payload": {"archive_path": str(missing), "output_dir": str(tmp_path / "missing-out")},
        }
    )

    assert invalid_code != 0
    assert last_event(invalid_events)["type"] == "error"
    assert last_event(invalid_events)["code"] == "INVALID_PAYLOAD"
    assert missing_code != 0
    assert last_event(missing_events)["type"] == "error"
    assert last_event(missing_events)["code"] == "INVALID_PAYLOAD"


def test_archive_extractor_rejects_bad_action(tmp_path: Path) -> None:
    archive = make_zip(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "archive-bad-action",
            "action": "compress",
            "payload": {"archive_path": str(archive)},
        }
    )
    event = last_event(events)

    assert code != 0
    assert event["type"] == "error"
    assert event["code"] == "UNKNOWN_ACTION"
