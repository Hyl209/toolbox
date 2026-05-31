from __future__ import annotations

import importlib.util
from pathlib import Path

from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "json_tools"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("json_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_json_tools_plugin_loads():
    reset_plugin_manager()
    manager = PluginManager(ROOT / "plugins")
    found = manager.discover_plugins()
    assert "json_tools" in found
    results = manager.load_all_plugins()
    assert results.get("json_tools") is True
    plugin = manager.get_plugin("json_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "JSON 工具"


def test_format_json_preserves_chinese_and_sorts_keys():
    converter = _load_converter()

    formatted = converter.format_json('{"b":1,"a":"中文"}', sort_keys=True)

    assert formatted.splitlines()[1] == '  "a": "中文",'
    assert formatted.splitlines()[2] == '  "b": 1'


def test_minify_json_removes_unnecessary_spaces():
    converter = _load_converter()

    assert converter.minify_json('{ "a": 1, "b": [2] }') == '{"a":1,"b":[2]}'


def test_validate_json_reports_container_size():
    converter = _load_converter()

    state = converter.validate_json('[1, 2, 3]')

    assert state == {"valid": True, "type": "list", "items": 3}


def test_parse_json_reports_line_and_column():
    converter = _load_converter()

    try:
        converter.format_json('{"a": }')
    except converter.JsonToolError as exc:
        message = str(exc)
        assert "JSON 解析失败" in message
        assert "第 1 行" in message
    else:
        raise AssertionError("invalid JSON should be rejected")


def test_validate_json_reports_dict_type_and_key_count():
    converter = _load_converter()

    state = converter.validate_json('{"a": 1, "b": 2}')

    assert state == {"valid": True, "type": "dict", "items": 2}


def test_validate_json_reports_scalar_type():
    converter = _load_converter()

    state = converter.validate_json('"hello"')

    assert state["valid"] is True
    assert state["type"] == "str"
    assert state["items"] == 1
