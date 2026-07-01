from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "sidecar" / "tool_manifest.py"
TS_MANIFEST = ROOT / "desktop-tauri" / "src" / "tools" / "manifest.ts"


def test_manifest_check_does_not_rewrite_ts_manifest() -> None:
    before = TS_MANIFEST.read_text(encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(MANIFEST), "--check"],
        cwd=ROOT,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    after = TS_MANIFEST.read_text(encoding="utf-8")
    assert proc.returncode == 0
    assert "base64" in proc.stdout
    assert after == before


def test_manifest_check_fails_when_ts_manifest_is_stale(tmp_path, monkeypatch, capsys) -> None:
    from sidecar import tool_manifest

    stale_manifest = tmp_path / "manifest.ts"
    stale_manifest.write_text("export const toolManifest = [];\n", encoding="utf-8")
    monkeypatch.setattr(tool_manifest, "TS_MANIFEST_PATH", stale_manifest)

    result = tool_manifest.main(["--check"])
    captured = capsys.readouterr()

    assert result != 0
    assert "base64" in captured.out
    assert "stale" in captured.err.lower()
    assert str(stale_manifest) in captured.err


def test_build_manifest_preserves_legacy_registry_metadata() -> None:
    from sidecar.tool_manifest import build_manifest, load_tool_definitions

    definitions = {item["id"]: item for item in load_tool_definitions()}
    manifest = {item["id"]: item for item in build_manifest(definitions.values())}

    mp4 = manifest["mp4mp3"]
    assert mp4["sidebar_label"] == definitions["mp4mp3"]["sidebar_label"]
    assert mp4["dir_name"] == "modules/audio-extractor"
    assert mp4["converter_file"] == "converter.py"
    assert mp4["tab_file"] == "tab.py"
    assert mp4["extra_files"] == ["config_store.py"]
    assert mp4["tab_kwargs"] == {}

    tg = manifest["tgdownloader"]
    assert tg["extra_files"] == ["bin/aria2c.exe", "bin/aria2c.SHA256.txt"]
    assert tg["tab_kwargs"] == {"source_mode": "telegram"}
    assert tg["title"] == definitions["tgdownloader"]["title"]
    assert tg["status"] == "ready"


def test_generate_ts_declares_legacy_metadata_fields() -> None:
    from sidecar.tool_manifest import generate_ts

    source = generate_ts([])

    for marker in (
        "sidebar_label?: string;",
        "dir_name?: string;",
        "converter_file?: string;",
        "tab_file?: string;",
        "extra_files?: readonly string[];",
        "tab_kwargs?: Record<string, unknown>;",
    ):
        assert marker in source
