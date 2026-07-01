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
CONVERTER_PATH = ROOT / "modules" / "file-sorter" / "converter.py"

MODE_LABELS = {
    "按大类分类": "category",
    "按分辨率分类": "resolution",
    "category": "category",
    "resolution": "resolution",
}


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_filesorter_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy file sorter converter: {CONVERTER_PATH}")
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


def _mode(task: dict) -> str:
    return MODE_LABELS.get(_payload_str(task, "mode", "category"), "category")


def _selected_categories(task: dict) -> list[str] | None:
    payload = _payload(task)
    if payload is None or "selected_categories" not in payload:
        return None
    raw = payload.get("selected_categories")
    if raw is None:
        return None
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item)]
    return []


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


def _summary_data(module: ModuleType, summary: dict[str, Any]) -> dict[str, Any]:
    mode = str(summary.get("mode") or "category")
    selected = set(summary.get("selected_categories") or ())
    files = []
    for path in summary.get("files") or []:
        resolved = Path(path)
        category = module.get_category_for_file(resolved)
        item: dict[str, Any] = {
            "path": str(resolved),
            "name": resolved.name,
            "category": category,
            "selected": category in selected,
        }
        if mode == "resolution" and category in module.RESOLUTION_CATEGORY_ORDER:
            resolution = module.get_media_resolution(resolved, category)
            item["resolution"] = list(resolution) if resolution else []
            item["group_label"] = module.get_resolution_bucket(*resolution) if resolution else ""
        files.append(item)
    return {
        "mode": mode,
        "folder": str(summary.get("folder") or ""),
        "total_files": int(summary.get("total_files") or 0),
        "category_counts": _jsonable(summary.get("category_counts") or {}),
        "selected_categories": list(summary.get("selected_categories") or ()),
        "selected_total_files": int(summary.get("selected_total_files") or 0),
        "media_total_files": int(summary.get("media_total_files") or 0),
        "detected_media_files": int(summary.get("detected_media_files") or 0),
        "unresolved_media_files": int(summary.get("unresolved_media_files") or 0),
        "resolution_bucket_counts": _jsonable(summary.get("resolution_bucket_counts") or {}),
        "category_order": list(module.CATEGORY_ORDER),
        "resolution_category_order": list(module.RESOLUTION_CATEGORY_ORDER),
        "files": files,
    }


def run_filesorter(task: dict) -> dict:
    action = task.get("action")
    if action == "preview":
        return _run_preview(task)
    if action == "sort":
        return _run_sort(task)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_preview(task: dict) -> dict:
    folder_path = _payload_str(task, "folder_path")
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    try:
        module = _load_converter_module()
        summary = module.summarize_folder(folder_path, _selected_categories(task), _mode(task))
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": _summary_data(module, summary)}


def _run_sort(task: dict) -> dict:
    folder_path = _payload_str(task, "folder_path")
    if not folder_path:
        return _error("INVALID_PAYLOAD", "payload.folder_path is required")
    try:
        module = _load_converter_module()
        mode = _mode(task)
        selected = _selected_categories(task)
        summary = module.summarize_folder(folder_path, selected, mode)
        files = summary.get("files")
        results = module.classify_files(
            folder_path,
            selected,
            files if isinstance(files, list) else None,
            mode,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    success_count = sum(1 for item in results if item.get("success"))
    skipped_count = sum(1 for item in results if item.get("skip_reason"))
    fail_count = len(results) - success_count - skipped_count
    return {
        "ok": True,
        "data": {
            "summary": _summary_data(module, summary),
            "results": _jsonable(results),
            "success_count": success_count,
            "fail_count": fail_count,
            "skipped_count": skipped_count,
            "renamed_count": sum(1 for item in results if item.get("renamed")),
        },
    }
