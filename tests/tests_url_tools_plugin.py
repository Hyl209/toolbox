from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "url_tools"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("url_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_url_tools_plugin_loads(shared_plugin_manager):
    found = shared_plugin_manager.discovery.discover_plugins()
    assert "url_tools" in found
    assert found["url_tools"].sidebar_label == "URL 工具"
    plugin = shared_plugin_manager.get_plugin("url_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "URL 工具"


def test_encode_and_decode_url_component():
    converter = _load_converter()

    encoded = converter.encode_url_component("中文 参数")

    assert encoded == "%E4%B8%AD%E6%96%87%20%E5%8F%82%E6%95%B0"
    assert converter.decode_url_component(encoded) == "中文 参数"


def test_parse_query_string_from_full_url():
    converter = _load_converter()

    pairs = converter.parse_query_string("https://example.test/watch?id=42&empty=&tag=a&tag=b")

    assert pairs == [("id", "42"), ("empty", ""), ("tag", "a"), ("tag", "b")]


def test_format_query_params_aligns_keys():
    converter = _load_converter()

    assert converter.format_query_params("?short=1&long_key=2") == "short    = 1\nlong_key = 2"


def test_summarize_url_requires_full_url():
    converter = _load_converter()

    try:
        converter.summarize_url("a=1&b=2")
    except converter.UrlToolError as exc:
        assert "请输入完整 URL" in str(exc)
    else:
        raise AssertionError("partial query should be rejected")


def test_build_query_string_from_pairs():
    converter = _load_converter()

    result = converter.build_query_string([("key", "value"), ("q", "hello world")])

    assert "key=value" in result
    assert "q=hello+world" in result


def test_build_query_string_rejects_empty_pairs():
    converter = _load_converter()

    try:
        converter.build_query_string([])
    except converter.UrlToolError as exc:
        assert "没有可生成的查询参数" in str(exc)
    else:
        raise AssertionError("empty pairs should be rejected")
