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
CONVERTER_PATH = ROOT / "plugins" / "timestamp_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_timestamp_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load timestamp plugin converter: {CONVERTER_PATH}")
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


def _payload_str(task: dict, key: str, default: str) -> str:
    value = _payload(task).get(key, default)
    return value if isinstance(value, str) else default


def run_plugin_timestamp_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"to_datetime", "to_timestamp", "current_time"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    converter = _load_converter_module()
    try:
        tz_offset = _payload_str(task, "tz_offset", "+08:00")
        if action == "current_time":
            data = converter.current_time(tz_offset=tz_offset)
        else:
            text = _payload_text(task)
            if text is None:
                return _error("INVALID_PAYLOAD", "payload.text is required")
            if action == "to_datetime":
                data = converter.timestamp_to_datetime(
                    text,
                    tz_offset=tz_offset,
                    unit=_payload_str(task, "unit", "auto"),
                )
            else:
                data = converter.datetime_to_timestamp(text, tz_offset=tz_offset)
    except converter.TimestampToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
