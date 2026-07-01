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
IMAGE_CONVERTER_PATH = ROOT / "modules" / "image-converter" / "converter.py"


def _load_image_module() -> ModuleType:
    module_name = "hyl_legacy_image_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, IMAGE_CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy image converter module: {IMAGE_CONVERTER_PATH}")
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


def _payload_int(task: dict, key: str, default: int) -> int:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    try:
        return max(1, min(100, int(value)))
    except (TypeError, ValueError):
        return default


def _payload_paths(task: dict) -> list[Path] | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get("paths")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return [Path(item) for item in value]


def _image_item(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "name": resolved.name,
        "format": resolved.suffix.lower().lstrip("."),
        "size": str(resolved.stat().st_size if resolved.exists() else 0),
    }


def run_imageconvert(task: dict) -> dict:
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
        available, message = _load_image_module().probe_imagemagick()
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"available": bool(available), "message": str(message)}}


def _run_list(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    try:
        files = _load_image_module().collect_image_inputs([str(path) for path in paths])
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    items = [_image_item(path) for path in files]
    return {"ok": True, "data": {"files": items, "count": len(items)}}


def _run_convert(task: dict) -> dict:
    paths = _payload_paths(task)
    output_dir = _payload_str(task, "output_dir")
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    target_format = (_payload_str(task, "target_format") or "png").strip().lower()
    target_size_raw = _payload_str(task, "target_size_kb") or ""

    try:
        module = _load_image_module()
        target_size_kb = module.validate_target_size_kb(target_size_raw)
        files = module.collect_image_inputs([str(path) for path in paths])
        output_root = Path(output_dir).resolve()
        results = []
        for source in files:
            output_path = module.convert_image(
                input_path=source,
                output_dir=output_root,
                target_format=target_format,
                quality=_payload_int(task, "quality", 90),
                preserve_alpha=_payload_bool(task, "preserve_alpha", True),
                jpg_background=_payload_str(task, "jpg_background") or "white",
                target_size_kb=target_size_kb,
            )
            results.append({"source": str(source.resolve()), "output": str(Path(output_path).resolve())})
    except ValueError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {
        "ok": True,
        "data": {
            "results": results,
            "success_count": len(results),
            "fail_count": 0,
        },
    }
