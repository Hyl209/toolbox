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
CONVERTER_PATH = ROOT / "modules" / "duplicate-finder" / "converter.py"
PKG_DIR = CONVERTER_PATH.parent
PKG_NAME = PKG_DIR.name.replace("-", "_")


def _load_converter_module() -> ModuleType:
    qualified_name = f"{PKG_NAME}.converter"
    cached = sys.modules.get(qualified_name)
    if cached is not None:
        return cached
    if PKG_NAME not in sys.modules:
        pkg = ModuleType(PKG_NAME)
        pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
        pkg.__package__ = PKG_NAME
        pkg.__file__ = str(PKG_DIR / "__init__.py")
        sys.modules[PKG_NAME] = pkg
    spec = importlib.util.spec_from_file_location(qualified_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy duplicate finder converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    module.__package__ = PKG_NAME
    sys.modules[qualified_name] = module
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


def _payload_bool(task: dict, key: str, default: bool = False) -> bool:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


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


def run_same(task: dict) -> dict:
    action = task.get("action")
    if action == "scan":
        return _run_scan(task)
    if action == "move":
        return _run_move(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_scan(task: dict) -> dict:
    folder_path = _payload_str(task, "folder_path")
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    target_dir_name = _payload_str(task, "target_dir_name")
    try:
        result = _load_converter_module().find_duplicate_groups(
            folder_path,
            _payload_bool(task, "recursive", True),
            target_dir_name or "重复文件",
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": _jsonable(result)}


def _run_move(task: dict) -> dict:
    folder_path = _payload_str(task, "folder_path")
    payload = _payload(task)
    scan_result = payload.get("scan_result") if payload else None
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    if not isinstance(scan_result, dict):
        return _error("INVALID_PAYLOAD", "payload.scan_result is required")
    try:
        module = _load_converter_module()
        results = module.move_duplicates(folder_path, scan_result)
    except (FileNotFoundError, NotADirectoryError, TypeError, ValueError) as exc:
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
            "renamed_count": sum(1 for item in results if item.get("renamed")),
        },
    }
