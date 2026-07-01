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
CONVERTER_PATH = ROOT / "plugins" / "url_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_url_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load URL plugin converter: {CONVERTER_PATH}")
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


def _pairs(value: Any) -> list[tuple[str, str]] | None:
    if not isinstance(value, list):
        return None
    pairs: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            key = item.get("key")
            val = item.get("value", "")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            key, val = item
        else:
            return None
        if not isinstance(key, str) or not isinstance(val, str):
            return None
        pairs.append((key, val))
    return pairs


def run_plugin_url_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"encode", "decode", "parse_query", "format_query", "build_query", "summarize"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    payload = _payload(task) or {}
    converter = _load_converter_module()
    try:
        if action == "build_query":
            pairs = _pairs(payload.get("pairs"))
            if pairs is None:
                return _error("INVALID_PAYLOAD", "payload.pairs must be key/value pairs")
            data = {"text": converter.build_query_string(pairs)}
        else:
            text = _payload_text(task)
            if text is None:
                return _error("INVALID_PAYLOAD", "payload.text is required")
            if action == "encode":
                safe = payload.get("safe", "")
                data = {"text": converter.encode_url_component(text, safe=safe if isinstance(safe, str) else "")}
            elif action == "decode":
                data = {"text": converter.decode_url_component(text)}
            elif action == "parse_query":
                data = {"pairs": converter.parse_query_string(text)}
            elif action == "format_query":
                data = {"text": converter.format_query_params(text)}
            else:
                data = converter.summarize_url(text)
    except converter.UrlToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
