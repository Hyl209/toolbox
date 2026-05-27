"""Single source of truth for all tool definitions.

Every consumer (hyl_toolbox.py, window.py, HylToolbox.spec, tests)
should read from TOOL_DEFINITIONS instead of hard-coding tool lists.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolDef:
    id: str
    title: str
    sidebar_label: str
    dir_name: str
    converter_file: str
    tab_file: str
    extra_files: tuple[str, ...] = ()
    tab_kwargs: dict = field(default_factory=dict)


TOOL_DEFINITIONS: list[ToolDef] = [
    ToolDef('music', 'NCM转换', 'NCM 转 MP3', 'music', 'ncm_to_mp3.py', 'tab.py'),
    ToolDef('zipandpng', 'PNG伪装', '图片伪装', 'zipandpng', 'zipandpng.py', 'tab.py'),
    ToolDef('mp4mp3', 'MP4转MP3', 'MP4 转 MP3', 'mp4-mp3', 'converter.py', 'tab.py',
            extra_files=('config_store.py',)),
    ToolDef('imageconvert', '图片格式互转', '图片格式互转', 'image-convert', 'converter.py', 'tab.py'),
    ToolDef('pdftools', 'PDF工具', 'PDF工具', 'pdf-tools', 'converter.py', 'tab.py'),
    ToolDef('tgdownloader', 'TG下载', 'TG下载', 'video-downloader', 'converter.py', 'tab.py',
            extra_files=('bin/aria2c.exe', 'bin/aria2c.SHA256.txt'),
            tab_kwargs={'source_mode': 'telegram'}),
    ToolDef('webvideodownloader', '网页视频下载', '网页视频下载', 'video-downloader', 'converter.py', 'tab.py',
            tab_kwargs={'source_mode': 'web'}),
    ToolDef('batchrename', '批量命名', '批量命名', 'name', 'converter.py', 'tab.py'),
    ToolDef('filesorter', '文件分类', '文件分类', '分类', 'converter.py', 'tab.py'),
    ToolDef('same', '重复文件', '重复文件', 'same', 'converter.py', 'tab.py'),
    ToolDef('base64', '图片Base64', '图片Base64', 'base64', 'converter.py', 'tab.py'),
]

TOOL_BY_ID = {t.id: t for t in TOOL_DEFINITIONS}
TOOL_IDS = [t.id for t in TOOL_DEFINITIONS]
SIDEBAR_LABELS = [t.sidebar_label for t in TOOL_DEFINITIONS]


def get_tool_definitions() -> list[dict]:
    """Return tool definitions as plain dicts (backward-compatible)."""
    return [
        {'key': t.id, 'title': t.title}
        for t in TOOL_DEFINITIONS
    ]


def get_dynamic_module_specs(root) -> dict[tuple[str, str]]:
    """Build DynamicModuleLoader specs from TOOL_DEFINITIONS."""
    specs: dict[str, tuple[str, str]] = {}
    for t in TOOL_DEFINITIONS:
        dir_path = root / t.dir_name
        # converter modules
        conv_key = t.id.replace('mp3', '') if t.id == 'mp4mp3' else t.id
        conv_module_name = f'{conv_key}_module'
        specs[conv_key] = (conv_module_name, dir_path / t.converter_file)
        # tab modules
        tab_key = f'{t.id}_tab' if t.id not in ('music',) else 'music_tab'
        tab_module_name = f'{tab_key}_module'
        specs.setdefault(tab_key, (tab_module_name, dir_path / t.tab_file))
    # legacy aliases
    specs['ncm'] = ('music_ncm_to_mp3', root / 'music' / 'ncm_to_mp3.py')
    return specs


def get_packaging_datas() -> list[tuple[str, str]]:
    """Build PyInstaller datas list from TOOL_DEFINITIONS."""
    datas = []
    seen = set()
    for t in TOOL_DEFINITIONS:
        dir_name = t.dir_name
        conv = f'{dir_name}/{t.converter_file}'
        tab = f'{dir_name}/{t.tab_file}'
        datas.append((conv.replace('/', '\\'), dir_name))
        datas.append((tab.replace('/', '\\'), dir_name))
        for extra in t.extra_files:
            path = f'{dir_name}/{extra}'
            if path not in seen:
                datas.append((path.replace('/', '\\'), dir_name))
                seen.add(path)
    return datas
