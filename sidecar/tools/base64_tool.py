from __future__ import annotations

import base64
import sys
from pathlib import Path

try:
    from ..runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 2)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.base64.converter import (
    build_data_url,
    decode_base64_to_file,
    encode_file_to_base64,
    guess_mime_from_path,
    normalize_base64_text,
    save_base64_text,
)


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _payload_text(task: dict) -> str | None:
    payload = task.get("payload")
    if not isinstance(payload, dict):
        return None
    text = payload.get("text")
    return text if isinstance(text, str) else None


def _payload(task: dict) -> dict | None:
    payload = task.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_str(task: dict, key: str) -> str | None:
    payload = _payload(task)
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _payload_bool(task: dict, key: str, default: bool = False) -> bool:
    payload = _payload(task)
    if payload is None:
        return default
    value = payload.get(key, default)
    return value if isinstance(value, bool) else default


def run_base64(task: dict) -> dict:
    action = task.get("action")
    if action not in {"encode_text", "decode_text", "encode_file", "decode_file"}:
        return _error("UNKNOWN_ACTION", f"unknown action: {action}")

    if action == "encode_file":
        return _run_encode_file(task)

    if action == "decode_file":
        return _run_decode_file(task)

    text = _payload_text(task)
    if text is None:
        return _error("INVALID_PAYLOAD", "payload.text is required")

    if action == "encode_text":
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return {"ok": True, "data": {"text": encoded}}

    try:
        decoded = base64.b64decode(normalize_base64_text(text)).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        return _error("INVALID_PAYLOAD", str(exc))
    return {"ok": True, "data": {"text": decoded}}


def _run_encode_file(task: dict) -> dict:
    file_path = _payload_str(task, "file_path")
    output_dir = _payload_str(task, "output_dir")
    output_name = _payload_str(task, "output_name") or "base64"
    if not file_path:
        return _error("INVALID_PAYLOAD", "payload.file_path is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    try:
        text = encode_file_to_base64(file_path)
        if _payload_bool(task, "data_url"):
            text = build_data_url(text, Path(file_path).suffix)
        output_path = save_base64_text(text, output_dir, output_name)
    except Exception as exc:
        return _error("TOOL_ERROR", str(exc))

    return {
        "ok": True,
        "data": {
            "text": text,
            "output_path": str(output_path),
            "mime": guess_mime_from_path(file_path),
        },
    }


def _run_decode_file(task: dict) -> dict:
    text = _payload_text(task)
    output_dir = _payload_str(task, "output_dir")
    output_name = _payload_str(task, "output_name") or "output"
    if text is None:
        return _error("INVALID_PAYLOAD", "payload.text is required")
    if not output_dir:
        return _error("INVALID_PAYLOAD", "payload.output_dir is required")

    try:
        output_path = decode_base64_to_file(text, output_dir, output_name)
    except Exception as exc:
        return _error("INVALID_PAYLOAD", str(exc))

    return {"ok": True, "data": {"output_path": str(output_path)}}
