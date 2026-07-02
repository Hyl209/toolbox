from __future__ import annotations

import importlib.util
import logging
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


try:
    from ..runtime_paths import project_root
    from ..runtime_state import emit_runtime_progress
    from ._cancel_support import add_cancel_token_kwarg
except ImportError:  # direct script execution support
    from runtime_paths import project_root
    from runtime_state import emit_runtime_progress
    from tools._cancel_support import add_cancel_token_kwarg


ROOT = project_root(__file__, 2)
MODULE_DIR = ROOT / "modules" / "video-downloader"
PACKAGE_NAME = "hyl_legacy_video_downloader"
logger = logging.getLogger(__name__)


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


def _options(payload: dict[str, Any], module: ModuleType) -> Any:
    raw = payload.get("options")
    data = raw if isinstance(raw, dict) else {}
    proxy_url = _payload_str(data, "proxy_url").strip()
    if not proxy_url:
        proxy_url = module.build_proxy_url(data.get("proxy_host"), data.get("proxy_port"))
    return module.DownloadOptions(
        web_use_browser_cookies=_payload_bool(data, "web_use_browser_cookies", False),
        overwrite=_payload_bool(data, "overwrite", False),
        output_subdir_by_title=_payload_bool(data, "output_subdir_by_title", False),
        proxy_url=proxy_url,
        filename_template=_payload_str(data, "filename_template", module.DEFAULT_FILENAME_TEMPLATE),
        web_download_all_candidates=_payload_bool(data, "web_download_all_candidates", False),
        max_concurrent_downloads=_payload_int(data, "max_concurrent_downloads", 1),
    )


def _urls_from_payload(payload: dict[str, Any], module: ModuleType) -> list[str]:
    if isinstance(payload.get("urls"), list):
        return module.parse_task_lines("\n".join(str(item) for item in payload["urls"]))
    if payload.get("url") is not None:
        return module.parse_task_lines(str(payload.get("url")))
    return module.parse_task_lines(_payload_str(payload, "text"))


def _download_tasks_from_payload(payload: dict[str, Any], module: ModuleType) -> list[Any]:
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list):
        return module.build_download_tasks(_urls_from_payload(payload, module))
    tasks: list[Any] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        urls = module.parse_task_lines(str(item.get("source_url") or item.get("url") or ""))
        if not urls:
            continue
        source_url = urls[0]
        source_kind = str(item.get("source_kind") or "web")
        target_title = str(item.get("target_title") or "").strip()
        output_subdir = str(item.get("output_subdir") or "").strip()
        tasks.append(module.DownloadTask(source_url, source_kind, target_title, output_subdir))
    return tasks


def _inspect_urls_from_payload(payload: dict[str, Any], module: ModuleType) -> tuple[list[str], list[str]]:
    urls = _urls_from_payload(payload, module)
    web_urls: list[str] = []
    errors: list[str] = []
    for url in urls:
        try:
            tasks = module.build_download_tasks([url])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        web_urls.extend(task.source_url for task in tasks if task.source_kind == "web")
    return web_urls, errors


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


def run_webvideodownloader(task: dict) -> dict:
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
    if action == "inspect":
        return _run_inspect(payload)
    if action == "embed_thumbnail":
        return _run_embed_thumbnail(payload)
    if action == "download":
        return _run_download(payload)
    return _error("UNKNOWN_ACTION", f"unknown action: {action}")


def _run_probe() -> dict:
    module = _load_converter_module()
    return {"ok": True, "data": {"backends": _clean(module.probe_download_backends())}}


def _run_parse(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    urls = module.parse_task_lines(_payload_str(payload, "text"))
    errors: list[str] = []
    try:
        tasks = module.build_download_tasks(urls)
    except ValueError as exc:
        tasks = []
        errors.append(str(exc))
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
    errors = module.validate_download_request(urls, _payload_str(payload, "output_dir"))
    return {"ok": True, "data": {"valid": not errors, "errors": _clean(errors)}}


def _run_inspect(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    urls, errors = _inspect_urls_from_payload(payload, module)
    if errors:
        return {
            "ok": True,
            "data": {
                "results": [],
                "success_count": 0,
                "fail_count": 0,
                "logs": [],
                "errors": _clean(errors),
            },
        }
    if not urls:
        return _error("INVALID_PAYLOAD", "payload.url, payload.urls, or payload.text must contain at least one URL")
    logs: list[str] = []
    def _progress(message: str) -> None:
        logs.append(message)
        emit_runtime_progress(message)
    try:
        results = module.inspect_web_media_batch(urls, progress_cb=_progress, options=_options(payload, module))
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    clean_results = _clean(results)
    success_count = sum(1 for item in clean_results if isinstance(item, dict) and item.get("success"))
    return {
        "ok": True,
        "data": {
            "results": clean_results,
            "success_count": success_count,
            "fail_count": len(clean_results) - success_count,
            "logs": [str(item) for item in logs[-50:]],
            "errors": [],
        },
    }


def _download_data(
    results: list[Any] | None = None,
    logs: list[str] | None = None,
    errors: list[Any] | None = None,
) -> dict:
    clean_results = _clean(results or [])
    success_count = sum(1 for item in clean_results if isinstance(item, dict) and item.get("success"))
    files: list[str] = []
    result_errors: list[str] = []
    for item in clean_results:
        if not isinstance(item, dict):
            continue
        if item.get("success"):
            for path in item.get("files") or []:
                files.append(str(path))
        else:
            error = str(item.get("error") or "").strip()
            if error:
                result_errors.append(error)
    return {
        "ok": True,
        "data": {
            "results": clean_results,
            "success_count": success_count,
            "fail_count": len(clean_results) - success_count,
            "logs": [str(item) for item in (logs or [])[-50:]],
            "files": files,
            "errors": _clean(errors or result_errors),
        },
    }


def _thumbnail_jobs_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_jobs = payload.get("jobs")
    jobs: list[dict[str, Any]] = []
    if isinstance(raw_jobs, list):
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or item.get("file") or "").strip()
            if not path:
                continue
            candidate_index = item.get("candidate_index")
            try:
                candidate_index = int(candidate_index) if candidate_index is not None else None
            except (TypeError, ValueError):
                candidate_index = None
            source_url = str(item.get("source_url") or "").strip()
            thumbnail_mode = str(item.get("thumbnail_mode") or ("web_then_frame" if source_url else "frame")).strip() or "frame"
            jobs.append(
                {
                    "path": Path(path),
                    "source_url": source_url,
                    "candidate_index": candidate_index,
                    "thumbnail_mode": thumbnail_mode,
                }
            )
    if jobs:
        return jobs

    files = payload.get("files")
    if not isinstance(files, list):
        return []
    source_url = _payload_str(payload, "source_url").strip()
    thumbnail_mode = _payload_str(payload, "thumbnail_mode", "web_then_frame" if source_url else "frame").strip() or "frame"
    candidate_index = payload.get("candidate_index")
    try:
        candidate_index = int(candidate_index) if candidate_index is not None else None
    except (TypeError, ValueError):
        candidate_index = None
    for item in files:
        path = str(item or "").strip()
        if not path:
            continue
        jobs.append(
            {
                "path": Path(path),
                "source_url": source_url,
                "candidate_index": candidate_index,
                "thumbnail_mode": thumbnail_mode,
            }
        )
    return jobs


def _run_embed_thumbnail(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    jobs = _thumbnail_jobs_from_payload(payload)
    if not jobs:
        return _download_data(errors=["payload.jobs or payload.files must contain at least one file"])

    logs: list[str] = []
    proxy_url = _options(payload, module).proxy_url
    results: list[dict[str, Any]] = []

    def _progress(message: str) -> None:
        logs.append(message)
        emit_runtime_progress(message)

    for job in jobs:
        try:
            result = module.embed_thumbnail(
                job["path"],
                job["source_url"],
                progress_cb=_progress,
                candidate_index=job["candidate_index"],
                thumbnail_mode=job["thumbnail_mode"],
                proxy_url=proxy_url,
            )
            clean_result = _clean(result)
            if isinstance(clean_result, dict):
                clean_result.setdefault("files", [str(job["path"])] if clean_result.get("success") else [])
                clean_result.setdefault("_path", str(job["path"]))
                results.append(clean_result)
            else:
                results.append({"success": True, "files": [str(job["path"])], "_path": str(job["path"])})
        except Exception as exc:
            results.append({"success": False, "error": str(exc), "files": [], "_path": str(job["path"])})
    return _download_data(results=results, logs=logs)


def _run_download(payload: dict[str, Any]) -> dict:
    module = _load_converter_module()
    output_dir = _payload_str(payload, "output_dir")
    try:
        tasks = _download_tasks_from_payload(payload, module)
    except ValueError as exc:
        return _download_data(errors=[str(exc)])

    web_errors = [
        f"only web URLs are supported: {task.source_url}"
        for task in tasks
        if str(getattr(task, "source_kind", "")) != "web"
    ]
    if web_errors:
        return _download_data(errors=web_errors)

    validation_errors = module.validate_download_request(tasks, output_dir)
    if validation_errors:
        return _download_data(errors=validation_errors)

    logs: list[str] = []
    def _progress(message: str) -> None:
        logs.append(message)
        emit_runtime_progress(message)
    try:
        kwargs = {
            "telegram_config": None,
            "options": _options(payload, module),
            "progress_cb": _progress,
        }
        add_cancel_token_kwarg(module, kwargs, logger)
        results = module.download_batch(tasks, output_dir, **kwargs)
    except ValueError as exc:
        return _download_data(logs=logs, errors=[str(exc)])
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))
    return _download_data(results=results, logs=logs)
