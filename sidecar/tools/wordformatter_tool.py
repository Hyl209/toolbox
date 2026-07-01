from __future__ import annotations

from copy import deepcopy
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
CONVERTER_PATH = ROOT / "modules" / "word-formatter" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_wordformatter_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy word formatter converter: {CONVERTER_PATH}")
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


def _payload_paths(task: dict) -> list[str] | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get("paths", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


def _payload_config(task: dict, module: ModuleType) -> dict[str, object]:
    payload = _payload(task)
    config = module.get_default_config()
    raw = payload.get("config") if payload else None
    if not isinstance(raw, dict):
        return config
    merged = deepcopy(config)
    page = raw.get("page")
    if isinstance(page, dict):
        merged["page"].update(page)
    styles = raw.get("styles")
    if isinstance(styles, dict):
        for key, value in styles.items():
            if key in merged["styles"] and isinstance(value, dict):
                merged["styles"][key].update(value)
    return merged


def _file_item(path: Path) -> dict[str, str | int]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "name": resolved.name,
        "size": resolved.stat().st_size if resolved.exists() else 0,
    }


def run_wordformatter(task: dict) -> dict:
    action = task.get("action")
    if action == "default_config":
        return _run_default_config()
    if action == "list":
        return _run_list(task)
    if action == "format":
        return _run_format(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_default_config() -> dict:
    try:
        config = _load_converter_module().get_default_config()
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"config": config}}


def _run_list(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    try:
        files = _load_converter_module().collect_word_inputs(paths)
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"files": [_file_item(path) for path in files], "count": len(files)}}


def _run_format(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    text = _payload_str(task, "text")
    output_dir = _payload_str(task, "output_dir")
    output_mode = _payload_str(task, "output_mode", "copy") or "copy"
    try:
        module = _load_converter_module()
        files = module.collect_word_inputs(paths)
        config = _payload_config(task, module)
        outputs = module.format_batch(files, text, config, output_dir, output_mode)
    except Exception as exc:
        error_type = getattr(module if "module" in locals() else _load_converter_module(), "WordFormatError", Exception)
        if isinstance(exc, (ValueError, error_type)):
            return _error("INVALID_PAYLOAD", str(exc))
        return _error("TOOL_ERROR", str(exc))

    results = []
    for index, output in enumerate(outputs):
        source = str(files[index].resolve()) if index < len(files) else "text"
        results.append({"source": source, "output": str(Path(output).resolve())})
    return {
        "ok": True,
        "data": {
            "results": results,
            "success_count": len(results),
            "fail_count": 0,
        },
    }
