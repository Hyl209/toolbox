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
CONVERTER_PATH = ROOT / "plugins" / "archive_extractor" / "converter.py"
MAX_LISTED_FILES = 200


def _load_converter_module() -> ModuleType:
    module_name = "hyl_plugin_archive_extractor_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load archive_extractor plugin converter: {CONVERTER_PATH}")
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


def _listed_files(output_dir: Path) -> list[str]:
    if not output_dir.exists():
        return []
    files = []
    for path in output_dir.rglob("*"):
        if path.is_file():
            files.append(path.relative_to(output_dir).as_posix())
    return sorted(files)[:MAX_LISTED_FILES]


def run_plugin_archive_extractor(task: dict) -> dict:
    action = task.get("action")
    if action not in {"detect", "extract"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    payload = _payload(task)
    if payload is None:
        return _error("INVALID_PAYLOAD", "payload object is required")
    archive_path = _payload_text(payload, "archive_path")
    if archive_path is None:
        return _error("INVALID_PAYLOAD", "payload.archive_path is required")

    converter = _load_converter_module()
    try:
        archive = Path(archive_path)
        archive_type = converter.detect_archive_type(archive)
        if action == "detect":
            data = {
                "archive_path": str(archive),
                "archive_type": archive_type,
                "supported": bool(archive_type),
            }
        else:
            output_dir_text = _payload_text(payload, "output_dir")
            if output_dir_text is None:
                return _error("INVALID_PAYLOAD", "payload.output_dir is required")
            password = _payload_text(payload, "password", "") or ""
            output_dir = Path(output_dir_text)
            extracted_count = converter.extract_archive_sync(archive, output_dir, password=password)
            data = {
                "archive_path": str(archive),
                "output_dir": str(output_dir),
                "archive_type": archive_type or converter.detect_archive_type(archive),
                "extracted_count": extracted_count,
                "files": _listed_files(output_dir),
            }
    except converter.ArchiveExtractError as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": data}
