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
CONVERTER_PATH = ROOT / "plugins" / "uuid_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_uuid_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load UUID plugin converter: {CONVERTER_PATH}")
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


def _payload_value(task: dict, key: str, default: Any = None) -> Any:
    payload = _payload(task)
    if payload is None:
        return default
    return payload.get(key, default)


def run_plugin_uuid_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"generate", "normalize", "validate", "describe"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    converter = _load_converter_module()
    uppercase = _payload_bool(task, "uppercase")
    hyphenated = _payload_bool(task, "hyphenated", True)
    try:
        if action == "generate":
            items = converter.generate_uuid_batch(
                _payload_value(task, "count", 10),
                uppercase=uppercase,
                hyphenated=hyphenated,
            )
            data = {"items": items, "text": "\n".join(items)}
        else:
            text = _payload_text(task)
            if text is None:
                return _error("INVALID_PAYLOAD", "payload.text is required")
            if action == "normalize":
                data = {"text": converter.normalize_uuid(text, uppercase=uppercase, hyphenated=hyphenated)}
            elif action == "validate":
                data = {"valid": converter.validate_uuid(text)}
            else:
                data = converter.describe_uuid(text)
    except converter.UuidToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
