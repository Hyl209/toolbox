from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_plugin(task: dict) -> tuple[int, list[dict]]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-plugin-file-hasher-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "plugin:file_hasher", "--input", str(input_path)],
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


def write_sample(tmp_path: Path) -> Path:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"hello file hasher\n")
    return path


def expected_hashes(path: Path, algorithms: tuple[str, ...] = ("md5", "sha1", "sha256")) -> dict[str, str]:
    data = path.read_bytes()
    return {algorithm: hashlib.new(algorithm, data).hexdigest() for algorithm in algorithms}


def test_file_hasher_calculate_single_algorithm(tmp_path: Path) -> None:
    sample = write_sample(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "file-hasher-calc-single",
            "action": "calculate",
            "payload": {"path": str(sample), "algorithms": ["sha1"]},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["path"] == str(sample)
    assert event["data"]["size"] == sample.stat().st_size
    assert event["data"]["hashes"] == expected_hashes(sample, ("sha1",))


def test_file_hasher_calculate_defaults_to_all_algorithms(tmp_path: Path) -> None:
    sample = write_sample(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "file-hasher-calc-all",
            "action": "calculate",
            "payload": {"path": str(sample)},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["hashes"] == expected_hashes(sample)


def test_file_hasher_verify_auto_reports_match(tmp_path: Path) -> None:
    sample = write_sample(tmp_path)
    sha256 = expected_hashes(sample, ("sha256",))["sha256"]

    code, events = run_plugin(
        {
            "task_id": "file-hasher-verify-auto",
            "action": "verify",
            "payload": {"path": str(sample), "expected_checksum": sha256},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["path"] == str(sample)
    assert event["data"]["algorithm"] == "sha256"
    assert event["data"]["expected"] == sha256
    assert event["data"]["actual"] == sha256
    assert event["data"]["matched"] is True


def test_file_hasher_verify_explicit_algorithm_reports_mismatch(tmp_path: Path) -> None:
    sample = write_sample(tmp_path)

    code, events = run_plugin(
        {
            "task_id": "file-hasher-verify-md5",
            "action": "verify",
            "payload": {"path": str(sample), "expected_checksum": "0" * 32, "algorithm": "md5"},
        }
    )
    event = last_event(events)

    assert code == 0
    assert event["type"] == "result"
    assert event["data"]["path"] == str(sample)
    assert event["data"]["algorithm"] == "md5"
    assert event["data"]["matched"] is False


def test_file_hasher_rejects_bad_payload_and_unknown_action(tmp_path: Path) -> None:
    sample = write_sample(tmp_path)

    bad_payload_code, bad_payload_events = run_plugin(
        {
            "task_id": "file-hasher-bad-payload",
            "action": "calculate",
            "payload": {"path": str(sample), "algorithms": "sha256"},
        }
    )
    bad_action_code, bad_action_events = run_plugin(
        {
            "task_id": "file-hasher-bad-action",
            "action": "hash",
            "payload": {"path": str(sample)},
        }
    )

    assert bad_payload_code != 0
    assert last_event(bad_payload_events)["type"] == "error"
    assert last_event(bad_payload_events)["code"] == "INVALID_PAYLOAD"
    assert bad_action_code != 0
    assert last_event(bad_action_events)["type"] == "error"
    assert last_event(bad_action_events)["code"] == "UNKNOWN_ACTION"


def test_file_hasher_missing_file_uses_converter_validation(tmp_path: Path) -> None:
    missing = tmp_path / "missing.bin"

    code, events = run_plugin(
        {
            "task_id": "file-hasher-missing",
            "action": "calculate",
            "payload": {"path": str(missing), "algorithms": ["sha256"]},
        }
    )
    event = last_event(events)

    assert code != 0
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
