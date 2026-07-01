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
MUSIC_PATH = ROOT / "modules" / "ncm-converter" / "ncm_to_mp3.py"


def _load_music_module() -> ModuleType:
    module_name = "hyl_legacy_ncm_to_mp3"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, MUSIC_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy music module: {MUSIC_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_str(task: dict, key: str) -> str | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _payload_bool(task: dict, key: str, default: bool = False) -> bool:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    return value if isinstance(value, bool) else default


def _payload_paths(task: dict) -> list[Path] | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get("paths")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return [Path(item) for item in value]


def run_music(task: dict) -> dict:
    action = task.get("action")
    if action == "probe":
        return _run_probe()
    if action == "list":
        return _run_list(task)
    if action == "convert":
        return _run_convert(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_probe() -> dict:
    try:
        available, message = _load_music_module().probe_converter_backend()
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"available": bool(available), "message": str(message)}}


def _run_list(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    try:
        module = _load_music_module()
        files = module.collect_input_paths(paths)
        items = [module.extract_song_info(path) for path in files]
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"files": items, "count": len(items)}}


def _run_convert(task: dict) -> dict:
    paths = _payload_paths(task)
    output_dir = _payload_str(task, "output_dir")
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    try:
        module = _load_music_module()
        files = module.collect_input_paths(paths)
        results = module.convert_many(files, Path(output_dir), overwrite=_payload_bool(task, "overwrite"))
        items = [
            {"source": str(Path(source).resolve()), "output": str(Path(output).resolve())}
            for source, output in results
        ]
        deleted = _delete_sources([Path(source) for source, _ in results]) if _payload_bool(task, "delete_source") else []
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {
        "ok": True,
        "data": {
            "results": items,
            "success_count": len(items),
            "fail_count": 0,
            "deleted": deleted,
        },
    }


def _delete_sources(sources: list[Path]) -> list[dict[str, Any]]:
    deleted: list[dict[str, Any]] = []
    for source in sources:
        try:
            source.unlink()
            deleted.append({"path": str(source.resolve()), "ok": True})
        except Exception as exc:
            deleted.append({"path": str(source.resolve()), "ok": False, "message": str(exc)})
    return deleted
