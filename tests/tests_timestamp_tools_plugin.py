from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "timestamp_tools"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("timestamp_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_timestamp_tools_plugin_loads(shared_plugin_manager):
    found = shared_plugin_manager.discovery.discover_plugins()
    assert "timestamp_tools" in found
    assert found["timestamp_tools"].sidebar_label == "时间戳工具"
    plugin = shared_plugin_manager.get_plugin("timestamp_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "时间戳工具"


def test_timestamp_to_datetime_uses_seconds_in_requested_timezone():
    converter = _load_converter()

    state = converter.timestamp_to_datetime("0", "+08:00")

    assert state["datetime"] == "1970-01-01 08:00:00"
    assert state["unit"] == "seconds"
    assert state["timezone"] == "+0800"


def test_timestamp_to_datetime_auto_detects_milliseconds():
    converter = _load_converter()

    state = converter.timestamp_to_datetime("1000", "UTC", unit="milliseconds")

    assert state["datetime"] == "1970-01-01 00:00:01"
    assert state["unit"] == "milliseconds"


def test_datetime_to_timestamp_defaults_to_configured_timezone():
    converter = _load_converter()

    state = converter.datetime_to_timestamp("1970-01-01 08:00:01", "+08:00")

    assert state["seconds"] == 1
    assert state["milliseconds"] == 1000


def test_invalid_timezone_offset_is_rejected():
    converter = _load_converter()

    try:
        converter.timestamp_to_datetime("0", "+25:00")
    except converter.TimestampToolError as exc:
        assert "时区偏移超出范围" in str(exc)
    else:
        raise AssertionError("invalid timezone should be rejected")


def test_decimal_timezone_offset_is_supported():
    converter = _load_converter()

    state = converter.timestamp_to_datetime("0", "+5.5")

    assert state["datetime"] == "1970-01-01 05:30:00"
    assert state["timezone"] == "+0530"


def test_non_numeric_timezone_offset_reports_tool_error():
    converter = _load_converter()

    try:
        converter.timestamp_to_datetime("0", "abc")
    except converter.TimestampToolError as exc:
        assert "无法识别时区偏移" in str(exc)
    else:
        raise AssertionError("invalid timezone text should be rejected")


def test_current_time_returns_datetime_and_timestamp():
    converter = _load_converter()

    state = converter.current_time("+08:00")

    assert "datetime" in state
    assert "seconds" in state
    assert "milliseconds" in state
    assert "iso" in state
    assert state["seconds"] > 0
    assert abs(state["milliseconds"] - state["seconds"] * 1000) < 1000


def test_datetime_to_timestamp_preserves_millisecond_precision():
    converter = _load_converter()

    state = converter.datetime_to_timestamp("2026-05-30 12:00:00", "UTC")

    # milliseconds should be close to seconds * 1000 (within 1s tolerance)
    assert abs(state["milliseconds"] - state["seconds"] * 1000) < 1000
