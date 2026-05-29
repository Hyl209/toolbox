from __future__ import annotations


class TextToolError(Exception):
    pass


def _require_text(text: str) -> str:
    value = str(text)
    if not value:
        raise TextToolError("请输入文本")
    return value


def normalize_newlines(text: str) -> str:
    return _require_text(text).replace("\r\n", "\n").replace("\r", "\n")


def clean_lines(text: str, trim: bool = True, drop_empty: bool = True) -> str:
    lines = normalize_newlines(text).split("\n")
    if trim:
        lines = [line.strip() for line in lines]
    if drop_empty:
        lines = [line for line in lines if line]
    return "\n".join(lines)


def dedupe_lines(text: str, case_sensitive: bool = True, trim: bool = True) -> str:
    lines = clean_lines(text, trim=trim, drop_empty=True).split("\n")
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        key = line if case_sensitive else line.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(line)
    return "\n".join(result)


def sort_lines(text: str, case_sensitive: bool = False, reverse: bool = False) -> str:
    lines = clean_lines(text, trim=True, drop_empty=True).split("\n")
    key = None if case_sensitive else str.casefold
    return "\n".join(sorted(lines, key=key, reverse=reverse))


def transform_case(text: str, mode: str) -> str:
    value = _require_text(text)
    if mode == "lower":
        return value.lower()
    if mode == "upper":
        return value.upper()
    if mode == "title":
        return value.title()
    raise TextToolError(f"不支持的大小写模式: {mode}")
