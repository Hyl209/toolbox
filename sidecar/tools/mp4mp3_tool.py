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
CONVERTER_PATH = ROOT / "modules" / "audio-extractor" / "converter.py"
MP4_SUFFIXES = {".mp4"}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from toolbox_app.tab_utils import collect_inputs_by_suffix


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_mp4mp3_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy MP4 converter module: {CONVERTER_PATH}")
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


def _payload_bool(task: dict, key: str, default: bool = True) -> bool:
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


def _collect_mp4(paths: list[Path]) -> list[Path]:
    return collect_inputs_by_suffix([str(path) for path in paths], MP4_SUFFIXES)


def _file_item(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "name": resolved.name,
        "size": str(resolved.stat().st_size if resolved.exists() else 0),
    }


def run_mp4mp3(task: dict) -> dict:
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
        ffmpeg = _load_converter_module().ensure_ffmpeg()
    except Exception as exc:
        return {"ok": True, "data": {"available": False, "message": str(exc)}}
    return {"ok": True, "data": {"available": True, "message": f"ffmpeg 可用：{ffmpeg}"}}


def _run_list(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    try:
        files = _collect_mp4(paths)
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    items = [_file_item(path) for path in files]
    return {"ok": True, "data": {"files": items, "count": len(items)}}


def _run_convert(task: dict) -> dict:
    paths = _payload_paths(task)
    output_dir = _payload_str(task, "output_dir")
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    try:
        module = _load_converter_module()
        files = _collect_mp4(paths)
        output_root = Path(output_dir).resolve()
        results = []
        for source in files:
            output_path = output_root / f"{source.stem}.mp3"
            converted = module.convert_mp4_to_mp3(
                source,
                output_path,
                overwrite=_payload_bool(task, "overwrite", True),
            )
            results.append({"source": str(source.resolve()), "output": str(Path(converted).resolve())})
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
