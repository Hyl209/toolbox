from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType


try:
    from ..runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 2)
ZIPANDPNG_PATH = ROOT / "modules" / "file-disguise" / "zipandpng.py"


def _load_zipandpng_module() -> ModuleType:
    module_name = "hyl_legacy_zipandpng"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, ZIPANDPNG_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy zipandpng module: {ZIPANDPNG_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _call_legacy(func, *args) -> None:
    with redirect_stdout(io.StringIO()):
        func(*args)


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_str(task: dict, key: str) -> str | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _default_output_path(cover_path: Path, payload_path: Path, output_dir: str | None, output_name: str | None) -> Path | None:
    if not output_dir and not output_name:
        return None
    if not output_dir:
        raise ValueError("payload.output_dir is required when output_name is provided")
    name = (output_name or payload_path.stem).strip() or payload_path.stem
    suffix = cover_path.suffix.lower() if cover_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"} else ".png"
    return Path(output_dir) / f"{Path(name).stem}{suffix}"


def run_zipandpng(task: dict) -> dict:
    action = task.get("action")
    if action == "disguise":
        return _run_disguise(task)
    if action == "recover":
        return _run_recover(task)
    if action == "info":
        return _run_info(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_disguise(task: dict) -> dict:
    cover_path = _payload_str(task, "cover_path")
    payload_path = _payload_str(task, "payload_path")
    output_path = _payload_str(task, "output_path")
    if not cover_path:
        return _error("INVALID_PAYLOAD", "payload.cover_path is required")
    if not payload_path:
        return _error("INVALID_PAYLOAD", "payload.payload_path is required")

    cover = Path(cover_path)
    payload = Path(payload_path)
    try:
        final_output = Path(output_path) if output_path else _default_output_path(
            cover,
            payload,
            _payload_str(task, "output_dir"),
            _payload_str(task, "output_name"),
        )
        if final_output is not None:
            final_output.parent.mkdir(parents=True, exist_ok=True)
        module = _load_zipandpng_module()
        _call_legacy(module.disguise_file, cover, payload, final_output)
        if final_output is None:
            final_output = module.build_default_disguised_output_path(cover)
        info = module.get_embedded_file_info(final_output)
    except ValueError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {"ok": True, "data": {"output_path": str(final_output), "embedded": info}}


def _run_recover(task: dict) -> dict:
    image_path = _payload_str(task, "image_path")
    if not image_path:
        return _error("INVALID_PAYLOAD", "payload.image_path is required")
    output_path = _payload_str(task, "output_path")

    try:
        image = Path(image_path)
        final_output = Path(output_path) if output_path else None
        if final_output is not None:
            final_output.parent.mkdir(parents=True, exist_ok=True)
        module = _load_zipandpng_module()
        info = module.get_embedded_file_info(image)
        _call_legacy(module.recover_file, image, final_output)
        if final_output is None:
            final_output = image.with_name(info["filename"])
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {"ok": True, "data": {"output_path": str(final_output), "embedded": info}}


def _run_info(task: dict) -> dict:
    image_path = _payload_str(task, "image_path")
    if not image_path:
        return _error("INVALID_PAYLOAD", "payload.image_path is required")
    try:
        info = _load_zipandpng_module().get_embedded_file_info(Path(image_path))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"embedded": info}}
