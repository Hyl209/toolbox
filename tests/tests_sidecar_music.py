from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_music(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-music-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "music", "--input", str(input_path)],
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


def write_fake_ncm(path: Path, title: str = "Song", artist: str = "Artist") -> None:
    metadata = json.dumps({"musicName": title, "artist": [[artist]]}, ensure_ascii=False)
    path.write_bytes(b"header music:" + metadata.encode("utf-8") + b" footer")


def test_music_probe_reports_backend_status() -> None:
    events = run_music({"task_id": "music-001", "action": "probe", "payload": {}})

    event = events[-1]
    assert event["type"] == "result"
    assert isinstance(event["data"]["available"], bool)
    assert isinstance(event["data"]["message"], str)


def test_music_lists_ncm_files_with_metadata() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-music-files-") as tmp:
        root = Path(tmp)
        ncm = root / "song.ncm"
        ignored = root / "song.txt"
        write_fake_ncm(ncm, "立哥测试歌", "HYL")
        ignored.write_text("ignore", encoding="utf-8")

        events = run_music(
            {
                "task_id": "music-002",
                "action": "list",
                "payload": {"paths": [str(root)]},
            },
        )

    event = events[-1]
    assert event["type"] == "result"
    assert len(event["data"]["files"]) == 1
    item = event["data"]["files"][0]
    assert item["file_path"] == str(ncm.resolve())
    assert item["title"] == "立哥测试歌"
    assert item["artist"] == "HYL"


def test_music_convert_uses_legacy_module_and_reports_outputs(monkeypatch) -> None:
    from sidecar.tools import music_tool

    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-music-files-") as tmp:
        root = Path(tmp)
        source = root / "song.ncm"
        output_dir = root / "out"
        write_fake_ncm(source)

        def fake_convert_many(files: list[Path], output_dir: Path, overwrite: bool = False):
            assert files == [source.resolve()]
            assert output_dir == output_dir.resolve()
            assert overwrite is True
            target = output_dir / "song.mp3"
            output_dir.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"mp3")
            return [(source.resolve(), target.resolve())]

        fake_module = SimpleNamespace(
            collect_input_paths=lambda paths: [source.resolve()],
            convert_many=fake_convert_many,
        )
        monkeypatch.setattr(music_tool, "_load_music_module", lambda: fake_module)

        result = music_tool.run_music(
            {
                "task_id": "music-003",
                "action": "convert",
                "payload": {
                    "paths": [str(source)],
                    "output_dir": str(output_dir),
                    "overwrite": True,
                },
            },
        )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 0
    assert result["data"]["results"][0]["source"] == str(source.resolve())
    assert result["data"]["results"][0]["output"].endswith("song.mp3")


def test_music_convert_requires_output_dir() -> None:
    events = run_music(
        {
            "task_id": "music-004",
            "action": "convert",
            "payload": {"paths": ["song.ncm"]},
        },
    )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
