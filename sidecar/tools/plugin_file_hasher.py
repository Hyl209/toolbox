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
CONVERTER_PATH = ROOT / "plugins" / "file_hasher" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_file_hasher_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load file_hasher plugin converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict[str, Any] | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_text(payload: dict[str, Any], key: str, default: str | None = None) -> str | None:
    value = payload.get(key, default)
    return value if isinstance(value, str) else default


def _payload_algorithms(payload: dict[str, Any], converter: ModuleType) -> tuple[str, ...] | None:
    value = payload.get("algorithms")
    if value is None:
        return tuple(converter.SUPPORTED_ALGORITHMS)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return tuple(item.strip().lower() for item in value if item.strip())


def run_plugin_file_hasher(task: dict) -> dict:
    action = task.get("action")
    if action not in {"calculate", "verify"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    payload = _payload(task)
    if payload is None:
        return _error("INVALID_PAYLOAD", "payload object is required")
    path = _payload_text(payload, "path")
    if path is None:
        return _error("INVALID_PAYLOAD", "payload.path is required")

    converter = _load_converter_module()
    try:
        source = Path(path)
        if action == "calculate":
            algorithms = _payload_algorithms(payload, converter)
            if not algorithms:
                return _error("INVALID_PAYLOAD", "payload.algorithms must be a list of strings")
            hashes = converter.calculate_hashes(source, algorithms=algorithms)
            data = {
                "path": str(source),
                "size": source.stat().st_size,
                "hashes": hashes,
            }
        else:
            expected = _payload_text(payload, "expected_checksum")
            if expected is None:
                return _error("INVALID_PAYLOAD", "payload.expected_checksum is required")
            algorithm = _payload_text(payload, "algorithm", "auto") or "auto"
            data = {"path": str(source), **converter.verify_file_hash(source, expected, algorithm=algorithm)}
    except converter.FileHashError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
