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
CONVERTER_PATH = ROOT / "modules" / "batch-rename" / "converter.py"

DEFAULT_PREFIX = "批量命名"
DEFAULT_GROUP_MODE = "suffix"
DEFAULT_SORT_MODE = "name"
DEFAULT_SORT_ORDER = "asc"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_batchrename_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy batch rename converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_str(task: dict, key: str, default: str = "") -> str:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    return value if isinstance(value, str) else default


def _options(task: dict) -> tuple[str, str, str, str, str]:
    folder_path = _payload_str(task, "folder_path")
    prefix = _payload_str(task, "prefix", DEFAULT_PREFIX) or DEFAULT_PREFIX
    group_mode = _payload_str(task, "group_mode", DEFAULT_GROUP_MODE) or DEFAULT_GROUP_MODE
    sort_mode = _payload_str(task, "sort_mode", DEFAULT_SORT_MODE) or DEFAULT_SORT_MODE
    sort_order = _payload_str(task, "sort_order", DEFAULT_SORT_ORDER) or DEFAULT_SORT_ORDER
    return folder_path, prefix, group_mode, sort_mode, sort_order


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def run_batchrename(task: dict) -> dict:
    action = task.get("action")
    if action == "preview":
        return _run_preview(task)
    if action == "rename":
        return _run_rename(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_preview(task: dict) -> dict:
    folder_path, prefix, group_mode, sort_mode, sort_order = _options(task)
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    try:
        summary = _load_converter_module().summarize_folder(
            folder_path,
            prefix,
            group_mode,
            sort_mode,
            sort_order,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {"ok": True, "data": _jsonable(summary)}


def _run_rename(task: dict) -> dict:
    folder_path, prefix, group_mode, sort_mode, sort_order = _options(task)
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    try:
        results = _load_converter_module().rename_files(
            folder_path,
            prefix,
            group_mode,
            sort_mode,
            sort_order,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    success_count = sum(1 for item in results if item.get("success"))
    return {
        "ok": True,
        "data": {
            "results": _jsonable(results),
            "success_count": success_count,
            "fail_count": len(results) - success_count,
        },
    }
