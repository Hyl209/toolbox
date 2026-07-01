# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os

from PyInstaller.config import CONF

SPEC_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_DIR.parent
SIDECAR_ROOT = SPEC_DIR
CONF["distpath"] = str(PROJECT_ROOT / "dist" / "hyl_sidecar")


def data_tree(root: Path, target: str) -> list[tuple[str, str]]:
    """Collect source-loaded legacy modules for sidecar importlib loaders."""
    ignored_dirs = {"__pycache__", ".pytest_cache", ".venv", ".venv-pytest", "dist", "build"}
    allowed_suffixes = {".py", ".json", ".txt", ".exe"}
    datas: list[tuple[str, str]] = []
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in ignored_dirs]
        current_path = Path(current)
        for filename in filenames:
            path = current_path / filename
            if filename.startswith(("test_", "tests_")):
                continue
            if path.suffix.lower() not in allowed_suffixes:
                continue
            relative_parent = path.parent.relative_to(root)
            dest = Path(target) / relative_parent
            datas.append((str(path), str(dest).replace("\\", "/")))
    return datas


datas = [
    (str(PROJECT_ROOT / "toolbox_app" / "tool_registry.py"), "toolbox_app"),
    *data_tree(PROJECT_ROOT / "modules", "modules"),
    *data_tree(PROJECT_ROOT / "plugins", "plugins"),
]

DYNAMIC_SOURCE_HIDDENIMPORTS = [
    "argparse",
    "asyncio",
    "base64",
    "collections",
    "concurrent",
    "contextlib",
    "copy",
    "csv",
    "dataclasses",
    "datetime",
    "functools",
    "hashlib",
    "html",
    "importlib",
    "io",
    "json",
    "math",
    "mimetypes",
    "os",
    "pathlib",
    "random",
    "re",
    "shlex",
    "shutil",
    "signal",
    "struct",
    "subprocess",
    "sys",
    "tarfile",
    "tempfile",
    "threading",
    "time",
    "types",
    "typing",
    "urllib",
    "uuid",
    "zipfile",
]

a = Analysis(
    [str(SIDECAR_ROOT / "hyl_sidecar.py")],
    pathex=[str(PROJECT_ROOT), str(SIDECAR_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "modules.base64.converter",
        "protocol",
        "runtime_paths",
        "settings_bridge",
        "tool_manifest",
        "tools.batchrename_tool",
        "tools.base64_tool",
        "tools.directdownloader_tool",
        "tools.filesorter_tool",
        "tools.imageconvert_tool",
        "tools.mp4mp3_tool",
        "tools.music_tool",
        "tools.pdftools_tool",
        "tools.plugin_archive_extractor",
        "tools.plugin_csv_tools",
        "tools.plugin_file_hasher",
        "tools.plugin_json_tools",
        "tools.plugin_regex_tools",
        "tools.plugin_text_tools",
        "tools.plugin_timestamp_tools",
        "tools.plugin_url_tools",
        "tools.plugin_uuid_tools",
        "tools.same_tool",
        "tools.tgdownloader_tool",
        "tools.webvideodownloader_tool",
        "tools.wordformatter_tool",
        "tools.zipandpng_tool",
        *DYNAMIC_SOURCE_HIDDENIMPORTS,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6",
        "pytest",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="hyl_sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
