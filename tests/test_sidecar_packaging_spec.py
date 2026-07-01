from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "sidecar" / "hyl_sidecar.spec"


def _spec_prefix_namespace() -> dict:
    source = SPEC.read_text(encoding="utf-8")
    prefix = source.split("\na = Analysis", 1)[0]
    namespace = {"SPECPATH": str(SPEC.parent)}
    exec(prefix, namespace)
    return namespace


def test_sidecar_spec_uses_project_root_and_tauri_dist_path() -> None:
    namespace = _spec_prefix_namespace()

    assert namespace["SPEC_DIR"] == ROOT / "sidecar"
    assert namespace["PROJECT_ROOT"] == ROOT
    assert namespace["SIDECAR_ROOT"] == ROOT / "sidecar"
    assert namespace["CONF"]["distpath"] == str(ROOT / "dist" / "hyl_sidecar")


def test_sidecar_spec_packages_file_loaded_legacy_sources() -> None:
    namespace = _spec_prefix_namespace()
    datas = set(namespace["datas"])

    assert (str(ROOT / "toolbox_app" / "tool_registry.py"), "toolbox_app") in datas
    assert (str(ROOT / "modules" / "direct-downloader" / "converter.py"), "modules/direct-downloader") in datas
    assert (str(ROOT / "modules" / "video-downloader" / "converter.py"), "modules/video-downloader") in datas
    assert (str(ROOT / "modules" / "video-downloader" / "bin" / "aria2c.exe"), "modules/video-downloader/bin") in datas
    assert (str(ROOT / "plugins" / "json_tools" / "converter.py"), "plugins/json_tools") in datas

    assert not any("__pycache__" in source or Path(source).name.startswith(("test_", "tests_")) for source, _ in datas)


def test_sidecar_spec_includes_hidden_imports_for_dynamic_sources() -> None:
    namespace = _spec_prefix_namespace()
    hidden = set(namespace["DYNAMIC_SOURCE_HIDDENIMPORTS"])

    for module_name in ("shlex", "zipfile", "tarfile", "mimetypes", "urllib"):
        assert module_name in hidden


def test_runtime_project_root_uses_pyinstaller_meipass(monkeypatch) -> None:
    from sidecar.runtime_paths import project_root

    monkeypatch.setattr(sys, "_MEIPASS", str(ROOT / "dist" / "_MEI-test"), raising=False)

    assert project_root(__file__, 1) == ROOT / "dist" / "_MEI-test"
