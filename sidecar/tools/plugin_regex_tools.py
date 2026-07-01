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
CONVERTER_PATH = ROOT / "plugins" / "regex_tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_regex_tools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load regex plugin converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else {}


def _payload_text(task: dict, key: str, default: str | None = None) -> str | None:
    value = _payload(task).get(key, default)
    return value if isinstance(value, str) else default


def _payload_bool(task: dict, key: str, default: bool) -> bool:
    value = _payload(task).get(key, default)
    return value if isinstance(value, bool) else default


def _payload_group(task: dict) -> int | str:
    value: Any = _payload(task).get("group", 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        group = value.strip()
        if group.lstrip("-").isdigit():
            return int(group)
        return group or 0
    return 0


def run_plugin_regex_tools(task: dict) -> dict:
    action = task.get("action")
    if action not in {"extract", "replace", "summary"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    text = _payload_text(task, "text")
    pattern = _payload_text(task, "pattern")
    if text is None:
        return _error("INVALID_PAYLOAD", "payload.text is required")
    if pattern is None:
        return _error("INVALID_PAYLOAD", "payload.pattern is required")

    converter = _load_converter_module()
    ignore_case = _payload_bool(task, "ignore_case", False)
    multiline = _payload_bool(task, "multiline", True)
    try:
        if action == "extract":
            group = _payload_group(task)
            matches = converter.extract_matches(
                text,
                pattern,
                group=group,
                ignore_case=ignore_case,
                multiline=multiline,
            )
            result_text = converter.extract_matches_text(
                text,
                pattern,
                group=group,
                ignore_case=ignore_case,
                multiline=multiline,
            )
            data = {"matches": matches, "text": result_text}
        elif action == "replace":
            data = {
                "text": converter.replace_matches(
                    text,
                    pattern,
                    replacement=_payload_text(task, "replacement", "") or "",
                    ignore_case=ignore_case,
                    multiline=multiline,
                )
            }
        else:
            data = {
                "summary": converter.regex_summary(
                    text,
                    pattern,
                    ignore_case=ignore_case,
                    multiline=multiline,
                )
            }
    except converter.RegexToolError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
