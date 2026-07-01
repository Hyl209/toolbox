from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


try:
    from ..runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 2)
MODULE_DIR = ROOT / "modules" / "video-downloader"
PACKAGE_NAME = "hyl_legacy_video_downloader"


def _load_converter_module() -> ModuleType:
    cached = sys.modules.get(f"{PACKAGE_NAME}.converter")
    if cached is not None:
        return cached

    package = sys.modules.get(PACKAGE_NAME)
    if package is None:
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME,
            MODULE_DIR / "__init__.py",
            submodule_search_locations=[str(MODULE_DIR)],
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load legacy video downloader package: {MODULE_DIR}")
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)

    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.converter",
        MODULE_DIR / "converter.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy video downloader converter: {MODULE_DIR / 'converter.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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


def _clean(value: Any) -> Any:
    if is_dataclass(value):
        return _clean(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    return value


def _urls_from_payload(payload: dict[str, Any], module: ModuleType) -> list[str]:
    if isinstance(payload.get("urls"), list):
        return module.parse_task_lines("\n".join(str(item) for item in payload["urls"]))
    if payload.get("url") is not None:
        return module.parse_task_lines(str(payload.get("url")))
    return module.parse_task_lines(_payload_str(payload, "text"))


def _credential_payload(payload: dict[str, Any]) -> dict[str, Any]:
    credentials = payload.get("credentials")
    return credentials if isinstance(credentials, dict) else {}


def _config(payload: dict[str, Any], module: ModuleType) -> Any:
    credentials = _credential_payload(payload)
    session_file = (
        credentials.get("session_file")
        or credentials.get("session_path")
        or payload.get("session_file")
        or payload.get("session_path")
        or str(MODULE_DIR / module.SESSION_FILE_NAME)
    )
    return module.TelegramConfig(
        api_id=str(credentials.get("api_id", "")),
        api_hash=str(credentials.get("api_hash", "")),
        phone=str(credentials.get("phone", "")),
        session_file=str(session_file),
    )


def _options_payload(payload: dict[str, Any]) -> dict[str, Any]:
    options = payload.get("options")
    return options if isinstance(options, dict) else {}


def _download_options(payload: dict[str, Any], module: ModuleType) -> Any:
    options = _options_payload(payload)
    recent_limit = module.normalize_recent_limit(options.get("recent_limit", 500), default=500)
    date_from, date_to = module.normalize_date_range(
        options.get("date_from"),
        options.get("date_to"),
    )
    proxy_url = _payload_str(options, "proxy_url").strip()
    if not proxy_url:
        proxy_url = module.build_proxy_url(options.get("proxy_host"), options.get("proxy_port"))
    return module.DownloadOptions(
        overwrite=_payload_bool(options, "overwrite", False),
        output_subdir_by_title=_payload_bool(options, "output_subdir_by_title", False),
        proxy_url=proxy_url,
        max_concurrent_downloads=_payload_int(options, "max_concurrent_downloads", 1),
        telegram_recent_limit=recent_limit,
        telegram_download_all_messages=_payload_bool(options, "download_all_messages", False),
        telegram_date_from=date_from,
        telegram_date_to=date_to,
        telegram_include_videos=_payload_bool(options, "include_videos", True),
        telegram_include_photos=_payload_bool(options, "include_photos", False),
    )


def _telegram_tasks(urls: list[str], module: ModuleType) -> tuple[list[Any], list[str]]:
    tasks: list[Any] = []
    errors: list[str] = []
    for url in urls:
        try:
            built = module.build_download_tasks([url])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for task in built:
            if not str(task.source_kind).startswith("telegram"):
                errors.append(f"non-telegram URL is not supported by tgdownloader: {task.source_url}")
                continue
            tasks.append(task)
    return tasks, errors


def run_tgdownloader(task: dict) -> dict:
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
    if action == "auth_status":
        return _run_auth_status(payload)
    if action == "send_code":
        return _run_send_code(payload)
    if action == "complete_login":
        return _run_complete_login(payload)
    if action == "download":
        return _run_download(payload)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_probe() -> dict:
    module = _load_converter_module()
    return {"ok": True, "data": {"backends": _clean(module.probe_download_backends())}}


def _run_parse(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    urls = _urls_from_payload(payload, module)
    tasks, errors = _telegram_tasks(urls, module)
    return {
        "ok": True,
        "data": {
            "urls": urls,
            "tasks": _clean(tasks),
            "url_count": len(urls),
            "task_count": len(tasks),
            "errors": errors,
        },
    }


def _run_validate(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    urls = _urls_from_payload(payload, module)
    tasks, errors = _telegram_tasks(urls, module)
    options = _options_payload(payload)
    legacy_errors = module.validate_download_request(
        tasks,
        _payload_str(payload, "output_dir"),
        telegram_config=_config(payload, module),
        recent_limit=options.get("recent_limit", 500),
        telegram_download_all_messages=_payload_bool(options, "download_all_messages", False),
        date_from=options.get("date_from"),
        date_to=options.get("date_to"),
        telegram_include_videos=_payload_bool(options, "include_videos", True),
        telegram_include_photos=_payload_bool(options, "include_photos", False),
    )
    all_errors = [*errors, *_clean(legacy_errors)]
    return {"ok": True, "data": {"valid": not all_errors, "errors": all_errors}}


def _validation_errors(payload: dict[str, Any], tasks: list[Any], module: ModuleType) -> list[Any]:
    options = _options_payload(payload)
    return module.validate_download_request(
        tasks,
        _payload_str(payload, "output_dir"),
        telegram_config=_config(payload, module),
        recent_limit=options.get("recent_limit", 500),
        telegram_download_all_messages=_payload_bool(options, "download_all_messages", False),
        date_from=options.get("date_from"),
        date_to=options.get("date_to"),
        telegram_include_videos=_payload_bool(options, "include_videos", True),
        telegram_include_photos=_payload_bool(options, "include_photos", False),
    )


def _download_data(results: list[Any] | None = None, logs: list[str] | None = None, errors: list[Any] | None = None) -> dict:
    clean_results = _clean(results or [])
    clean_errors = [str(item) for item in (errors or [])]
    success_count = sum(1 for item in clean_results if isinstance(item, dict) and item.get("success"))
    failed_results = [item for item in clean_results if isinstance(item, dict) and not item.get("success")]
    result_errors = [str(item.get("error")) for item in failed_results if item.get("error")]
    files: list[str] = []
    for item in clean_results:
        if not isinstance(item, dict) or not item.get("success"):
            continue
        for file_path in item.get("files") or []:
            files.append(str(file_path))
    all_errors = [*result_errors, *clean_errors]
    return {
        "results": clean_results,
        "success_count": success_count,
        "fail_count": len(failed_results) if clean_results else len(all_errors),
        "logs": (logs or [])[-50:],
        "files": files,
        "errors": all_errors,
    }


def _run_download(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    logs: list[str] = []
    try:
        urls = _urls_from_payload(payload, module)
        tasks, input_errors = _telegram_tasks(urls, module)
        legacy_errors = _validation_errors(payload, tasks, module)
        errors = [*input_errors, *_clean(legacy_errors)]
        if errors:
            return {"ok": True, "data": _download_data(logs=logs, errors=errors)}
        options = _download_options(payload, module)
        results = module.download_batch(
            tasks,
            _payload_str(payload, "output_dir"),
            telegram_config=_config(payload, module),
            options=options,
            progress_cb=logs.append,
        )
        return {"ok": True, "data": _download_data(results=results, logs=logs)}
    except ValueError as exc:
        return {"ok": True, "data": _download_data(logs=logs, errors=[str(exc)])}
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))


def _run_auth_status(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    try:
        return {"ok": True, "data": _clean(module.check_telegram_authorization(_config(payload, module)))}
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))


def _run_send_code(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    try:
        return {"ok": True, "data": _clean(module.begin_telegram_login(_config(payload, module)))}
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))


def _run_complete_login(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    password = payload.get("password")
    try:
        return {
            "ok": True,
            "data": _clean(
                module.complete_telegram_login(
                    _config(payload, module),
                    _payload_str(payload, "code"),
                    _payload_str(payload, "phone_code_hash"),
                    password_callback=lambda: password,
                )
            ),
        }
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
