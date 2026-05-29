from __future__ import annotations

import json
from typing import Any


class JsonToolError(Exception):
    pass


def parse_json(text: str) -> Any:
    if not str(text).strip():
        raise JsonToolError("请输入 JSON 文本")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonToolError(f"JSON 解析失败: 第 {exc.lineno} 行，第 {exc.colno} 列，{exc.msg}") from exc


def format_json(text: str, indent: int = 2, sort_keys: bool = False) -> str:
    data = parse_json(text)
    return json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=sort_keys)


def minify_json(text: str, sort_keys: bool = False) -> str:
    data = parse_json(text)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=sort_keys)


def validate_json(text: str) -> dict[str, object]:
    data = parse_json(text)
    return {
        "valid": True,
        "type": type(data).__name__,
        "items": len(data) if isinstance(data, (dict, list)) else 1,
    }
