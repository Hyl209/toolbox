from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "csv_tools"


_cached_converter = None


def _load_converter():
    global _cached_converter
    if _cached_converter is not None:
        return _cached_converter
    spec = importlib.util.spec_from_file_location("csv_tools_converter_test", PLUGIN_DIR / "converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_converter = module
    return module


def test_csv_tools_plugin_loads():
    reset_plugin_manager()
    manager = PluginManager(ROOT / "plugins")
    found = manager.discover_plugins()
    assert "csv_tools" in found
    assert found["csv_tools"].sidebar_label == "CSV 工具"
    results = manager.load_all_plugins()
    assert results.get("csv_tools") is True
    plugin = manager.get_plugin("csv_tools")
    assert plugin is not None
    assert plugin.get_sidebar_label() == "CSV 工具"


def test_format_csv_quotes_values_when_needed():
    converter = _load_converter()

    assert converter.format_csv('name,note\n立哥,"a,b"') == 'name,note\n立哥,"a,b"'


def test_csv_to_tsv_converts_delimiter():
    converter = _load_converter()

    assert converter.csv_to_tsv("a,b\n1,2") == "a\tb\n1\t2"


def test_csv_to_json_with_header_preserves_chinese():
    converter = _load_converter()

    data = json.loads(converter.csv_to_json("name,score\n立哥,100"))

    assert data == [{"name": "立哥", "score": "100"}]


def test_csv_to_json_without_header_returns_rows():
    converter = _load_converter()

    data = json.loads(converter.csv_to_json("a,b\n1,2", has_header=False))

    assert data == [["a", "b"], ["1", "2"]]


def test_duplicate_headers_are_made_unique():
    converter = _load_converter()

    data = json.loads(converter.csv_to_json("name,name\nA,B"))

    assert data == [{"name": "A", "name_2": "B"}]


def test_table_summary_reports_rows_and_max_columns():
    converter = _load_converter()

    assert converter.table_summary("a,b\n1,2,3") == {"rows": 2, "columns": 3}
