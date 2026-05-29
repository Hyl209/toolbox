from __future__ import annotations

import importlib.util
from pathlib import Path

from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "text_tools"


def _load_converter():
    spec = importlib.util.spec_from_file_location("text_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_text_tools_plugin_loads():
    reset_plugin_manager()
    manager = PluginManager(ROOT / "plugins")
    found = manager.discover_plugins()
    assert "text_tools" in found
    assert found["text_tools"].sidebar_label == "文本工具"
    results = manager.load_all_plugins()
    assert results.get("text_tools") is True
    plugin = manager.get_plugin("text_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "文本工具"


def test_clean_lines_trims_and_drops_empty_lines():
    converter = _load_converter()

    assert converter.clean_lines("  a  \r\n\r\n b \n") == "a\nb"


def test_dedupe_lines_keeps_first_seen_line():
    converter = _load_converter()

    assert converter.dedupe_lines("A\na\nB\nA", case_sensitive=False) == "A\nB"


def test_sort_lines_defaults_to_case_insensitive_order():
    converter = _load_converter()

    assert converter.sort_lines("b\nA\nc") == "A\nb\nc"


def test_transform_case_supports_common_modes():
    converter = _load_converter()

    assert converter.transform_case("Abc", "lower") == "abc"
    assert converter.transform_case("Abc", "upper") == "ABC"


def test_transform_case_rejects_unknown_mode():
    converter = _load_converter()

    try:
        converter.transform_case("abc", "snake")
    except converter.TextToolError as exc:
        assert "不支持" in str(exc)
    else:
        raise AssertionError("unknown mode should fail")
