#!/usr/bin/env python3
"""Generate HylToolbox.spec from tool_registry.py.

Run: python generate_spec.py > HylToolbox.spec
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from toolbox_app.tool_registry import get_packaging_datas


PLUGIN_DATA_SUFFIXES = {'.json', '.md', '.py'}
PLUGIN_DATA_SKIP_PARTS = {'__pycache__', 'logs', '.codex-pytest-tmp', '.pytest-tmp'}


def _should_skip_plugin_data_path(rel_path: Path) -> bool:
    return any(part in PLUGIN_DATA_SKIP_PARTS or part.startswith('.') for part in rel_path.parts)


def get_plugin_packaging_datas(root: Path | None = None) -> list[tuple[str, str]]:
    root = root or Path(__file__).resolve().parent
    plugins_dir = root / 'plugins'
    if not plugins_dir.exists():
        return []

    datas: list[tuple[str, str]] = []
    for path in sorted(plugins_dir.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if _should_skip_plugin_data_path(rel):
            continue
        if path.suffix.lower() not in PLUGIN_DATA_SUFFIXES:
            continue
        datas.append((rel.as_posix(), rel.parent.as_posix()))
    return datas


def generate_spec() -> str:
    datas = get_packaging_datas()

    # Collect extra files not from tool_registry
    extra_datas = [
        ('themes/dark.qss', 'themes'),
        ('themes/light.qss', 'themes'),
        ('arrow-dark.svg', '.'),
        ('arrow-light.svg', '.'),
        ('check.svg', '.'),
        ('uncheck.svg', '.'),
        ('logo.png', '.'),
        ('sound.mp3', '.'),
        ('modules/ncm-converter/weixin_base64.txt', 'modules/ncm-converter'),
        ('modules/theme-customizer/__init__.py', 'modules/theme-customizer'),
        ('modules/theme-customizer/color_scheme.py', 'modules/theme-customizer'),
    ]
    # Deduplicate
    seen = {src for src, _ in datas}
    for src, dest in extra_datas:
        if src not in seen:
            datas.append((src, dest))
            seen.add(src)
    for src, dest in get_plugin_packaging_datas():
        if src not in seen:
            datas.append((src, dest))
            seen.add(src)

    # Add music weixin.png via collect_data_files
    datas_lines = []
    for src, dest in datas:
        datas_lines.append(f"        ('{src}', '{dest}'),")

    datas_block = '\n'.join(datas_lines)

    return f"""# -*- mode: python ; coding: utf-8 -*-
# Auto-generated from tool_registry.py — do not edit manually.
# Regenerate: python generate_spec.py > HylToolbox.spec

from PyInstaller.utils.hooks import collect_data_files

music_datas = collect_data_files('modules.ncm-converter', includes=['weixin.png'])

a = Analysis(
    ['hyl_toolbox.py'],
    pathex=[],
    binaries=[],
    datas=[
{datas_block}
    ] + music_datas,
    hiddenimports=['ncmdump', 'yt_dlp', 'telethon', 'docx', 'docx.oxml', 'docx.oxml.ns', 'docx.shared'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
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
    name='格式转换工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
    onefile=True,
)
"""


if __name__ == '__main__':
    spec_content = generate_spec()
    spec_path = Path(__file__).resolve().parent / 'HylToolbox.spec'
    spec_path.write_text(spec_content, encoding='utf-8')
    print(f'Generated {spec_path}')
