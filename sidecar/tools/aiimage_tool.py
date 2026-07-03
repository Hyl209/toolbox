from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


try:
    from ..runtime_paths import project_root
    from ..settings_bridge import DEFAULT_SETTINGS
except ImportError:  # direct script execution support
    from runtime_paths import project_root
    from settings_bridge import DEFAULT_SETTINGS


ROOT = project_root(__file__, 2)
CONVERTER_PATH = ROOT / "modules" / "ai-image-gen" / "converter.py"


def _load_converter_module() -> ModuleType:
    module_name = "hyl_aiimage_converter"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load ai image converter: {CONVERTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload(task: dict) -> dict:
    value = task.get("payload")
    return value if isinstance(value, dict) else {}


def _settings_path(task: dict) -> Path:
    raw = _payload(task).get("settings_path")
    return Path(raw) if isinstance(raw, str) and raw.strip() else Path(DEFAULT_SETTINGS)


def run_aiimage(task: dict) -> dict:
    action = task.get("action")
    payload = _payload(task)
    settings_path = _settings_path(task)
    try:
        module = _load_converter_module()
        store = module.KeyringSecretStore()
        if action == "load_config":
            data = module.load_config(settings_path=settings_path, secret_store=store)
            return {"ok": True, "data": data}
        if action == "save_config":
            data = module.save_config(payload, settings_path=settings_path, secret_store=store)
            return {"ok": True, "data": data}
        if action == "generate":
            data = module.generate_images(payload, settings_path=settings_path, secret_store=store)
            return {"ok": True, "data": data}
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")
    except Exception as exc:
        error_type = getattr(locals().get("module"), "AiImageError", RuntimeError)
        if isinstance(exc, error_type):
            return _error("INVALID_PAYLOAD", str(exc))
        return _error("TOOL_ERROR", str(exc))
