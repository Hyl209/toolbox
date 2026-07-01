from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def run_zipandpng(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-zipandpng-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "zipandpng", "--input", str(input_path)],
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


def test_zipandpng_disguises_payload_and_reports_embedded_info() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-zipandpng-files-") as tmp:
        root = Path(tmp)
        cover = root / "cover.png"
        payload = root / "secret.txt"
        output_dir = root / "out"
        cover.write_bytes(PNG_1X1)
        payload.write_text("secret payload", encoding="utf-8")

        events = run_zipandpng(
            {
                "task_id": "zipandpng-001",
                "action": "disguise",
                "payload": {
                    "cover_path": str(cover),
                    "payload_path": str(payload),
                    "output_dir": str(output_dir),
                    "output_name": "hidden",
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        output_path = Path(event["data"]["output_path"])
        assert output_path.name == "hidden.png"
        assert output_path.exists()
        assert event["data"]["embedded"]["found"] is True
        assert event["data"]["embedded"]["filename"] == "secret.txt"
        assert event["data"]["embedded"]["file_size"] == len("secret payload".encode("utf-8"))


def test_zipandpng_recovers_payload_from_disguised_image() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-zipandpng-files-") as tmp:
        root = Path(tmp)
        cover = root / "cover.png"
        payload = root / "secret.txt"
        disguised = root / "hidden.png"
        recovered = root / "restored.txt"
        cover.write_bytes(PNG_1X1)
        payload.write_text("secret payload", encoding="utf-8")

        disguise_events = run_zipandpng(
            {
                "task_id": "zipandpng-002a",
                "action": "disguise",
                "payload": {
                    "cover_path": str(cover),
                    "payload_path": str(payload),
                    "output_path": str(disguised),
                },
            },
        )
        assert disguise_events[-1]["type"] == "result"

        recover_events = run_zipandpng(
            {
                "task_id": "zipandpng-002b",
                "action": "recover",
                "payload": {
                    "image_path": str(disguised),
                    "output_path": str(recovered),
                },
            },
        )

        event = recover_events[-1]
        assert event["type"] == "result"
        assert Path(event["data"]["output_path"]) == recovered
        assert recovered.read_text(encoding="utf-8") == "secret payload"


def test_zipandpng_requires_payload_for_disguise() -> None:
    events = run_zipandpng(
        {
            "task_id": "zipandpng-003",
            "action": "disguise",
            "payload": {"cover_path": "cover.png"},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
