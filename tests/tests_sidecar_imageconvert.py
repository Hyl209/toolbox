from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_imageconvert(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-imageconvert-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "imageconvert", "--input", str(input_path)],
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


def test_imageconvert_probe_reports_imagemagick_status() -> None:
    events = run_imageconvert({"task_id": "imageconvert-001", "action": "probe", "payload": {}})

    event = events[-1]
    assert event["type"] == "result"
    assert isinstance(event["data"]["available"], bool)
    assert isinstance(event["data"]["message"], str)


def test_imageconvert_lists_supported_images_recursively() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-imageconvert-files-") as tmp:
        root = Path(tmp)
        (root / "a.png").write_bytes(b"png")
        (root / "ignore.txt").write_text("ignore", encoding="utf-8")
        nested = root / "nested"
        nested.mkdir()
        (nested / "b.WEBP").write_bytes(b"webp")

        events = run_imageconvert(
            {
                "task_id": "imageconvert-002",
                "action": "list",
                "payload": {"paths": [str(root)]},
            },
        )

    event = events[-1]
    assert event["type"] == "result"
    assert [item["name"] for item in event["data"]["files"]] == ["a.png", "b.WEBP"]


def test_imageconvert_convert_uses_legacy_converter(monkeypatch) -> None:
    from sidecar.tools import imageconvert_tool

    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-imageconvert-files-") as tmp:
        root = Path(tmp)
        source = root / "photo.png"
        output_dir = root / "out"
        source.write_bytes(b"png")

        def fake_convert_image(
            input_path: Path,
            output_dir: Path,
            target_format: str,
            quality: int,
            preserve_alpha: bool,
            jpg_background: str,
            target_size_kb: float | None = None,
        ) -> Path:
            assert input_path == source.resolve()
            assert target_format == "webp"
            assert quality == 82
            assert preserve_alpha is True
            assert jpg_background == "white"
            assert target_size_kb == 256
            output_dir.mkdir(parents=True, exist_ok=True)
            target = output_dir / "photo.webp"
            target.write_bytes(b"webp")
            return target

        fake_module = SimpleNamespace(
            collect_image_inputs=lambda paths: [source.resolve()],
            validate_target_size_kb=lambda raw: 256 if raw == "256" else None,
            convert_image=fake_convert_image,
        )
        monkeypatch.setattr(imageconvert_tool, "_load_image_module", lambda: fake_module)

        result = imageconvert_tool.run_imageconvert(
            {
                "task_id": "imageconvert-003",
                "action": "convert",
                "payload": {
                    "paths": [str(source)],
                    "output_dir": str(output_dir),
                    "target_format": "webp",
                    "quality": 82,
                    "preserve_alpha": True,
                    "jpg_background": "white",
                    "target_size_kb": "256",
                },
            },
        )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 0
    assert result["data"]["results"][0]["source"] == str(source.resolve())
    assert result["data"]["results"][0]["output"].endswith("photo.webp")


def test_imageconvert_convert_requires_output_dir() -> None:
    events = run_imageconvert(
        {
            "task_id": "imageconvert-004",
            "action": "convert",
            "payload": {"paths": ["photo.png"], "target_format": "png"},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
