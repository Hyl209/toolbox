from __future__ import annotations

import importlib.util
from pathlib import Path

from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "regex_tools"


def _load_converter():
    spec = importlib.util.spec_from_file_location("regex_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_regex_tools_plugin_loads():
    reset_plugin_manager()
    manager = PluginManager(ROOT / "plugins")
    found = manager.discover_plugins()
    assert "regex_tools" in found
    assert found["regex_tools"].sidebar_label == "正则工具"
    results = manager.load_all_plugins()
    assert results.get("regex_tools") is True
    plugin = manager.get_plugin("regex_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "正则工具"


def test_extract_matches_returns_all_urls():
    converter = _load_converter()

    assert converter.extract_matches("a https://a.test b http://b.test", r"https?://\S+") == [
        "https://a.test",
        "http://b.test",
    ]


def test_extract_matches_supports_capture_group():
    converter = _load_converter()

    assert converter.extract_matches("id=12 id=34", r"id=(\d+)", group=1) == ["12", "34"]


def test_replace_matches_supports_backrefs():
    converter = _load_converter()

    assert converter.replace_matches("2026-05-30", r"(\d{4})-(\d{2})-(\d{2})", r"\1/\2/\3") == "2026/05/30"


def test_regex_summary_reports_match_and_unique_counts():
    converter = _load_converter()

    assert converter.regex_summary("A a B", r"[a-z]", ignore_case=True) == {"matches": 3, "unique": 3}


def test_invalid_pattern_reports_clear_error():
    converter = _load_converter()

    try:
        converter.extract_matches("abc", "(")
    except converter.RegexToolError as exc:
        assert "正则表达式无效" in str(exc)
    else:
        raise AssertionError("invalid regex should fail")


def test_missing_group_reports_clear_error():
    converter = _load_converter()

    try:
        converter.extract_matches("abc", r"(a)", group=2)
    except converter.RegexToolError as exc:
        assert "分组不存在" in str(exc)
    else:
        raise AssertionError("missing group should fail")


def test_extract_matches_text_joins_results():
    converter = _load_converter()

    result = converter.extract_matches_text("a1 b2 c3", r"\d")

    assert result == "1\n2\n3"
