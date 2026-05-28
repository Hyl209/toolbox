"""Verify tool_registry is consistent with HylToolbox.spec and window sidebar."""
from __future__ import annotations

import pathlib

from toolbox_app.tool_registry import TOOL_DEFINITIONS, get_tool_definitions, get_packaging_datas, SIDEBAR_LABELS

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / 'HylToolbox.spec'


def test_get_tool_definitions_matches_dataclass():
    defs = get_tool_definitions()
    assert len(defs) == len(TOOL_DEFINITIONS)
    for d, td in zip(defs, TOOL_DEFINITIONS):
        assert d['key'] == td.id
        assert d['title'] == td.title


def test_every_tool_has_converter_and_tab_file():
    for td in TOOL_DEFINITIONS:
        tool_dir = ROOT / td.dir_name
        assert (tool_dir / td.converter_file).exists(), f'{td.id}: missing {td.converter_file}'
        assert (tool_dir / td.tab_file).exists(), f'{td.id}: missing {td.tab_file}'


def _norm(p: str) -> str:
    return p.replace('\\', '/').replace('//', '/')


def test_spec_includes_all_registered_tools():
    spec_text = _norm(SPEC_PATH.read_text(encoding='utf-8'))
    for td in TOOL_DEFINITIONS:
        conv_path = _norm(f'{td.dir_name}/{td.converter_file}')
        tab_path = _norm(f'{td.dir_name}/{td.tab_file}')
        assert conv_path in spec_text, f'{td.id}: spec missing {conv_path}'
        assert tab_path in spec_text, f'{td.id}: spec missing {tab_path}'


def test_sidebar_labels_are_unique():
    assert len(SIDEBAR_LABELS) == len(set(SIDEBAR_LABELS))


def test_tool_ids_are_unique():
    ids = [td.id for td in TOOL_DEFINITIONS]
    assert len(ids) == len(set(ids))


def test_spec_includes_all_packaging_datas():
    """Verify spec includes every file from get_packaging_datas()."""
    spec_text = _norm(SPEC_PATH.read_text(encoding='utf-8'))
    for src, dest in get_packaging_datas():
        normalized = _norm(src)
        assert normalized in spec_text, f'spec missing {normalized}'


def test_packaging_datas_covers_all_registered_tools():
    """Every registered tool should contribute at least converter + tab to packaging."""
    datas = get_packaging_datas()
    datas_srcs = {src for src, _ in datas}
    for td in TOOL_DEFINITIONS:
        conv = f'{td.dir_name}/{td.converter_file}'
        tab = f'{td.dir_name}/{td.tab_file}'
        assert conv in datas_srcs or conv.replace('/', '\\') in datas_srcs, f'{td.id}: missing converter in packaging'
        assert tab in datas_srcs or tab.replace('/', '\\') in datas_srcs, f'{td.id}: missing tab in packaging'
