from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "uuid_tools"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("uuid_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_uuid_tools_plugin_loads():
    reset_plugin_manager()
    manager = PluginManager(ROOT / "plugins")
    found = manager.discover_plugins()
    assert "uuid_tools" in found
    assert found["uuid_tools"].sidebar_label == "UUID 工具"
    results = manager.load_all_plugins()
    assert results.get("uuid_tools") is True
    plugin = manager.get_plugin("uuid_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "UUID 工具"


def test_generate_uuid4_returns_valid_v4_uuid():
    converter = _load_converter()

    value = converter.generate_uuid4()

    parsed = uuid.UUID(value)
    assert parsed.version == 4
    assert str(parsed) == value


def test_generate_uuid4_can_emit_uppercase_without_hyphens():
    converter = _load_converter()

    value = converter.generate_uuid4(uppercase=True, hyphenated=False)

    assert len(value) == 32
    assert value == value.upper()
    assert converter.validate_uuid(value)


def test_generate_uuid_batch_respects_count():
    converter = _load_converter()

    values = converter.generate_uuid_batch(3)

    assert len(values) == 3
    assert all(converter.validate_uuid(value) for value in values)
    assert len(set(values)) == 3


def test_generate_uuid_batch_rejects_out_of_range_count():
    converter = _load_converter()

    try:
        converter.generate_uuid_batch(0)
    except converter.UuidToolError as exc:
        assert "数量范围必须是" in str(exc)
    else:
        raise AssertionError("out-of-range count should be rejected")


def test_normalize_uuid_accepts_compact_uuid():
    converter = _load_converter()

    value = converter.normalize_uuid("12345678123456781234567812345678")

    assert value == "12345678-1234-5678-1234-567812345678"


def test_describe_uuid_reports_nil_uuid():
    converter = _load_converter()

    state = converter.describe_uuid("00000000-0000-0000-0000-000000000000")

    assert state["is_nil"] is True
    assert state["canonical"] == "00000000-0000-0000-0000-000000000000"
    assert state["hex"] == "00000000000000000000000000000000"


def test_describe_uuid_reports_v4_uuid_details():
    converter = _load_converter()

    state = converter.describe_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d479")

    assert state["is_nil"] is False
    assert state["version"] == 4
    assert "urn" in state
    assert state["variant"] is not None


def test_validate_uuid_returns_false_for_invalid():
    converter = _load_converter()

    assert converter.validate_uuid("not-a-uuid") is False
    assert converter.validate_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d479") is True


def test_normalize_uuid_raises_on_invalid():
    converter = _load_converter()

    try:
        converter.normalize_uuid("invalid")
    except converter.UuidToolError as exc:
        assert "UUID 格式无效" in str(exc)
    else:
        raise AssertionError("invalid UUID should be rejected")


def test_parse_count_rejects_above_maximum():
    converter = _load_converter()

    try:
        converter.parse_count(501)
    except converter.UuidToolError as exc:
        assert "数量范围必须是" in str(exc)
    else:
        raise AssertionError("count above max should be rejected")
