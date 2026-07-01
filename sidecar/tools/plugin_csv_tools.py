from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


try:
    from ..runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 2)
CONVERTER_PATH = ROOT / "plugins" / "csv_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_csv_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load CSV plugin converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else {}


def _payload_text(task: dict) -> str | None:
    text = _payload(task).get("text")
    return text if isinstance(text, str) else None


def _delimiter(task: dict) -> str:
    value = _payload(task).get("delimiter", ",")
    return value if isinstance(value, str) and len(value) == 1 else ","


def _has_header(task: dict) -> bool:
    value = _payload(task).get("has_header", True)
    return value if isinstance(value, bool) else True


def run_plugin_csv_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"format", "to_tsv", "to_json", "summary"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")
    text = _payload_text(task)
    if text is None:
        return _error("INVALID_PAYLOAD", "payload.text is required")

    converter = _load_converter_module()
    try:
        delimiter = _delimiter(task)
        if action == "format":
            data = {"text": converter.format_csv(text, delimiter=delimiter)}
        elif action == "to_tsv":
            data = {"text": converter.csv_to_tsv(text, delimiter=delimiter)}
        elif action == "to_json":
            data = {"text": converter.csv_to_json(text, delimiter=delimiter, has_header=_has_header(task))}
        else:
            data = converter.table_summary(text, delimiter=delimiter)
    except converter.CsvToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
