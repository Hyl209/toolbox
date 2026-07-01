from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


try:
    from ..runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 2)
CONVERTER_PATH = ROOT / "plugins" / "json_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_json_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load JSON plugin converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_text(task: dict) -> str | None:
    payload = _payload(task)
    if payload is None:
        return None
    text = payload.get("text")
    return text if isinstance(text, str) else None


def _payload_bool(task: dict, key: str, default: bool = False) -> bool:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    return value if isinstance(value, bool) else default


def _payload_indent(task: dict) -> int:
    payload = _payload(task)
    value: Any = 2 if payload is None else payload.get("indent", 2)
    try:
        indent = int(value)
    except (TypeError, ValueError):
        indent = 2
    return min(max(indent, 0), 8)


def run_plugin_json_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"format", "minify", "validate", "parse", "summary"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")
    text = _payload_text(task)
    if text is None:
        return _error("INVALID_PAYLOAD", "payload.text is required")

    converter = _load_converter_module()
    sort_keys = _payload_bool(task, "sort_keys")
    try:
        if action == "format":
            data = {"text": converter.format_json(text, indent=_payload_indent(task), sort_keys=sort_keys)}
        elif action == "minify":
            data = {"text": converter.minify_json(text, sort_keys=sort_keys)}
        elif action == "validate":
            data = converter.validate_json(text)
        else:
            parsed = converter.parse_json(text)
            summary = converter.validate_json(text)
            data = {"value": parsed, "summary": summary} if action == "parse" else summary
    except converter.JsonToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
