"""JSON Lines emit helpers for the Python sidecar."""
from __future__ import annotations

import json


def _emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False, separators=(",", ":")), flush=True)


def emit_progress(task_id: str | None, message: str, percent: int) -> None:
    _emit({"type": "progress", "task_id": task_id, "message": message, "percent": percent})


def emit_result(task_id: str | None, data: dict | None = None) -> None:
    _emit({"type": "result", "task_id": task_id, "ok": True, "data": data or {}})


def emit_error(task_id: str | None, code: str, message: str) -> None:
    _emit({"type": "error", "task_id": task_id, "ok": False, "code": code, "message": message})
