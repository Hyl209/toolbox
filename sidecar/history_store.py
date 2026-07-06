from __future__ import annotations

import json
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .settings_bridge import DEFAULT_SETTINGS
except ImportError:  # direct script execution support
    from settings_bridge import DEFAULT_SETTINGS


DEFAULT_HISTORY_LIMIT = 100
SENSITIVE_KEYS = {
    "api_key",
    "api_hash",
    "password",
    "code",
    "phone_code_hash",
    "secret",
    "secret_ref",
    "token",
}


def history_path(settings_path: str | Path | None = None) -> Path:
    base = Path(settings_path) if settings_path else Path(DEFAULT_SETTINGS)
    return base.with_name("hyl_toolbox_history.json")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _read(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    data: dict[str, list[dict[str, Any]]] = {}
    for tool_id, items in loaded.items():
        if isinstance(tool_id, str) and isinstance(items, list):
            data[tool_id] = [deepcopy(item) for item in items if isinstance(item, dict)]
    return data


def _write(path: Path, data: dict[str, list[dict[str, Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temp_path.replace(path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def scrub_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in SENSITIVE_KEYS:
                continue
            cleaned[key_text] = scrub_sensitive(item)
        return cleaned
    if isinstance(value, list):
        return [scrub_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [scrub_sensitive(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def load_history(tool_id: str, *, settings_path: str | Path | None = None) -> list[dict[str, Any]]:
    return deepcopy(_read(history_path(settings_path)).get(tool_id, []))


def append_history(
    tool_id: str,
    item: dict[str, Any],
    *,
    settings_path: str | Path | None = None,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    path = history_path(settings_path)
    data = _read(path)
    clean_item = scrub_sensitive(item)
    clean_item.setdefault("id", f"{tool_id}-{uuid.uuid4().hex}")
    clean_item.setdefault("created_at", _now_iso())
    items = [clean_item, *data.get(tool_id, [])]
    data[tool_id] = items[: max(1, limit)]
    _write(path, data)
    return deepcopy(data[tool_id])


def delete_history(tool_id: str, item_id: str, *, settings_path: str | Path | None = None) -> bool:
    path = history_path(settings_path)
    data = _read(path)
    before = data.get(tool_id, [])
    after = [item for item in before if str(item.get("id", "")) != item_id]
    data[tool_id] = after
    _write(path, data)
    return len(after) != len(before)


def clear_history(tool_id: str, *, settings_path: str | Path | None = None) -> None:
    path = history_path(settings_path)
    data = _read(path)
    data[tool_id] = []
    _write(path, data)


def history_action(tool_id: str, action: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    settings_path = payload.get("settings_path")
    path = Path(settings_path) if isinstance(settings_path, str) and settings_path.strip() else Path(DEFAULT_SETTINGS)
    if action == "load_history":
        return {"items": load_history(tool_id, settings_path=path)}
    if action == "delete_history":
        delete_history(tool_id, str(payload.get("id", "")), settings_path=path)
        return {"items": load_history(tool_id, settings_path=path)}
    if action == "clear_history":
        clear_history(tool_id, settings_path=path)
        return {"items": []}
    return None
