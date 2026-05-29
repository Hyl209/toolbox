from __future__ import annotations

from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit


class UrlToolError(Exception):
    pass


def require_text(text: str) -> str:
    value = str(text)
    if not value:
        raise UrlToolError("请输入要处理的文本")
    return value


def encode_url_component(text: str, safe: str = "") -> str:
    return quote(require_text(text), safe=safe)


def decode_url_component(text: str) -> str:
    return unquote(require_text(text))


def parse_query_string(text: str) -> list[tuple[str, str]]:
    value = require_text(text).strip()
    query = urlsplit(value).query if "://" in value else value.lstrip("?")
    return parse_qsl(query, keep_blank_values=True)


def format_query_params(text: str) -> str:
    pairs = parse_query_string(text)
    if not pairs:
        raise UrlToolError("未找到查询参数")
    width = max(len(key) for key, _value in pairs)
    return "\n".join(f"{key.ljust(width)} = {value}" for key, value in pairs)


def build_query_string(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        raise UrlToolError("没有可生成的查询参数")
    return urlencode(pairs, doseq=True)


def summarize_url(text: str) -> dict[str, str]:
    value = require_text(text).strip()
    parts = urlsplit(value)
    if not parts.scheme and not parts.netloc:
        raise UrlToolError("请输入完整 URL")
    return {
        "scheme": parts.scheme,
        "host": parts.netloc,
        "path": parts.path,
        "query": parts.query,
        "fragment": parts.fragment,
    }
