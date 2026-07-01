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
CONVERTER_PATH = ROOT / "modules" / "pdf-tools" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_pdftools_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy PDF tools converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_paths(task: dict) -> list[str] | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get("paths", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


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


def _payload_int(task: dict, key: str, default: int) -> int:
    payload = _payload(task)
    if payload is None:
        return default
    try:
        return int(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def _file_item(path: Path) -> dict[str, str | int]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "name": resolved.name,
        "size": resolved.stat().st_size if resolved.exists() else 0,
    }


def _result_rows(outputs: list[Path], source: str = "") -> list[dict[str, str]]:
    return [{"source": source, "output": str(Path(output).resolve())} for output in outputs]


def run_pdftools(task: dict) -> dict:
    action = task.get("action")
    if action == "probe_ocr":
        return _run_probe_ocr()
    if action == "list":
        return _run_list(task)
    if action in {"merge", "split", "images", "text"}:
        return _run_action(task, str(action))
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_probe_ocr() -> dict:
    try:
        available, message = _load_converter_module().probe_tesseract()
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"available": bool(available), "message": str(message)}}


def _run_list(task: dict) -> dict:
    paths = _payload_paths(task)
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    try:
        files = _load_converter_module().collect_pdf_inputs(paths)
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return {"ok": True, "data": {"files": [_file_item(path) for path in files], "count": len(files)}}


def _run_action(task: dict, action: str) -> dict:
    paths = _payload_paths(task)
    output_dir = _payload_str(task, "output_dir")
    if paths is None:
        return _error("INVALID_PAYLOAD", "payload.paths is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    try:
        module = _load_converter_module()
        files = module.collect_pdf_inputs(paths)
        errors = module.validate_pdf_action(action, files, _payload_str(task, "page_ranges"))
        if errors:
            return _error("INVALID_PAYLOAD", "\n".join(errors))
        output_root = Path(output_dir).resolve()
        if action == "merge":
            outputs = [module.merge_pdfs(files, output_root / "merged.pdf")]
        elif action == "split":
            from pypdf import PdfReader

            reader = PdfReader(str(files[0]))
            page_indexes = module.parse_page_ranges(_payload_str(task, "page_ranges"), len(reader.pages))
            outputs = module.split_pdf(files[0], output_root, page_indexes)
        elif action == "images":
            outputs = module.pdf_to_images(
                files[0],
                output_root,
                _payload_str(task, "image_format", "png") or "png",
                _payload_int(task, "dpi", 150),
            )
        else:
            outputs = [
                module.export_pdf_text(
                    files[0],
                    output_root,
                    _payload_str(task, "text_export_format", "txt") or "txt",
                    ocr_fallback=_payload_bool(task, "ocr_fallback", False),
                    dpi=_payload_int(task, "dpi", 150),
                )
            ]
    except Exception as exc:
        error_type = getattr(module if "module" in locals() else _load_converter_module(), "PdfToolsError", Exception)
        if isinstance(exc, (ValueError, error_type)):
            return _error("INVALID_PAYLOAD", str(exc))
        return _error("TOOL_ERROR", str(exc))

    rows = _result_rows(outputs, str(files[0].resolve()) if files else "")
    return {
        "ok": True,
        "data": {
            "results": rows,
            "success_count": len(rows),
            "fail_count": 0,
        },
    }
