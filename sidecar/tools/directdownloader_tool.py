from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


try:
    from ..runtime_paths import project_root
    from ..runtime_state import current_download_token, emit_runtime_progress
except ImportError:  # direct script execution support
    from runtime_paths import project_root
    from runtime_state import current_download_token, emit_runtime_progress


ROOT = project_root(__file__, 2)
CONVERTER_PATH = ROOT / "modules" / "direct-downloader" / "converter.py"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _load_converter_module() -> ModuleType:
    module_name = "hyl_legacy_directdownloader_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy direct downloader converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict[str, Any] | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_str(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    return value if isinstance(value, str) else str(value)


def _payload_bool(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _payload_int(payload: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def _payload_headers(payload: dict[str, Any]) -> tuple[str, ...]:
    value = payload.get("extra_headers", ())
    if isinstance(value, str):
        return tuple(line.strip() for line in value.splitlines() if line.strip())
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(item.strip() for item in value if item.strip())
    return ()


def _request_item(request: Any, module: ModuleType) -> dict[str, Any]:
    return {
        "url": request.url,
        "output_name": request.output_name,
        "extra_headers": list(request.extra_headers),
        "referer": request.referer,
        "guess_filename": request.output_name or module.guess_filename(request.url),
    }


def _clean_text(value: Any) -> Any:
    if isinstance(value, str):
        return ANSI_RE.sub("", value)
    return value


def _proxy_url(payload: dict[str, Any], module: ModuleType) -> str:
    direct = _payload_str(payload, "proxy_url").strip()
    if direct:
        return direct
    return module.build_proxy_url(payload.get("proxy_host"), payload.get("proxy_port"))


def _options(payload: dict[str, Any], module: ModuleType) -> Any:
    return module.DirectDownloadOptions(
        output_dir=_payload_str(payload, "output_dir"),
        output_name=_payload_str(payload, "output_name"),
        proxy_url=_proxy_url(payload, module),
        connections=_payload_int(payload, "connections", module.DEFAULT_CONNECTIONS),
        extra_headers=_payload_headers(payload),
        referer=_payload_str(payload, "referer"),
        overwrite=_payload_bool(payload, "overwrite", False),
        output_subdir_by_filename=_payload_bool(payload, "output_subdir_by_filename", False),
    )


def _aria2_path(module: ModuleType) -> tuple[str, bool]:
    path = module.resolve_aria2c_path(ROOT)
    return (path or "aria2c", bool(path))


def run_directdownloader(task: dict) -> dict:
    action = task.get("action")
    if action == "probe":
        return _run_probe()

    payload = _payload(task)
    if payload is None:
        return _error("INVALID_PAYLOAD", "payload object is required")

    if action == "parse":
        return _run_parse(payload)
    if action == "validate":
        return _run_validate(payload)
    if action == "build_commands":
        return _run_build_commands(payload)
    if action == "download":
        return _run_download(payload)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_probe() -> dict:
    module = _load_converter_module()
    path = module.resolve_aria2c_path(ROOT)
    return {
        "ok": True,
        "data": {
            "available": bool(path),
            "path": path or "",
            "default_connections": module.DEFAULT_CONNECTIONS,
        },
    }


def _run_parse(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    requests = module.parse_download_requests(_payload_str(payload, "url_text"))
    return {"ok": True, "data": {"requests": [_request_item(item, module) for item in requests], "count": len(requests)}}


def _run_validate(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    errors = module.validate_download_form(
        _payload_str(payload, "url_text"),
        _payload_str(payload, "output_dir"),
        payload.get("connections", module.DEFAULT_CONNECTIONS),
        _payload_str(payload, "output_name"),
    )
    return {"ok": True, "data": {"valid": not errors, "errors": errors}}


def _run_build_commands(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    requests = module.parse_download_requests(_payload_str(payload, "url_text"))
    if not requests:
        return _error("INVALID_PAYLOAD", "payload.url_text must contain at least one http/https URL")
    aria2c, available = _aria2_path(module)
    options = _options(payload, module)
    commands = [
        {
            "request": _request_item(request, module),
            "command": module.build_aria2_command_for_request(request, options, aria2c),
        }
        for request in requests
    ]
    return {"ok": True, "data": {"commands": commands, "aria2_available": available, "aria2_path": aria2c}}


def _run_download(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    requests = module.parse_download_requests(_payload_str(payload, "url_text"))
    if not requests:
        return _error("INVALID_PAYLOAD", "payload.url_text must contain at least one http/https URL")
    try:
        logs: list[str] = []
        results = module.iter_download_requests(
            requests,
            _options(payload, module),
            progress_cb=logs.append,
            root=ROOT,
            should_stop=lambda: bool(current_download_token() and current_download_token().cancel.is_set()),
            structured_progress_cb=emit_runtime_progress,
        )
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    success_count = sum(1 for item in results if item.get("success"))
    clean_results = [
        {key: _clean_text(value) for key, value in dict(item).items()}
        for item in results
    ]
    return {
        "ok": True,
        "data": {
            "results": clean_results,
            "success_count": success_count,
            "fail_count": len(clean_results) - success_count,
            "logs": [str(_clean_text(item)) for item in logs[-50:]],
        },
    }
