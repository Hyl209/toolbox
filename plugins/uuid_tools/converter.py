from __future__ import annotations

import uuid


class UuidToolError(Exception):
    pass


def _coerce_uuid(text: str) -> uuid.UUID:
    value = str(text).strip()
    if not value:
        raise UuidToolError("请输入 UUID")
    try:
        return uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise UuidToolError("UUID 格式无效") from exc


def _format_uuid(value: uuid.UUID, uppercase: bool = False, hyphenated: bool = True) -> str:
    text = str(value) if hyphenated else value.hex
    return text.upper() if uppercase else text


def generate_uuid4(uppercase: bool = False, hyphenated: bool = True) -> str:
    return _format_uuid(uuid.uuid4(), uppercase=uppercase, hyphenated=hyphenated)


def parse_count(value, minimum: int = 1, maximum: int = 500) -> int:
    try:
        count = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise UuidToolError("数量必须是整数") from exc
    if count < minimum or count > maximum:
        raise UuidToolError(f"数量范围必须是 {minimum}-{maximum}")
    return count


def generate_uuid_batch(count=10, uppercase: bool = False, hyphenated: bool = True) -> list[str]:
    total = parse_count(count)
    return [generate_uuid4(uppercase=uppercase, hyphenated=hyphenated) for _ in range(total)]


def normalize_uuid(text: str, uppercase: bool = False, hyphenated: bool = True) -> str:
    return _format_uuid(_coerce_uuid(text), uppercase=uppercase, hyphenated=hyphenated)


def validate_uuid(text: str) -> bool:
    try:
        _coerce_uuid(text)
    except UuidToolError:
        return False
    return True


def describe_uuid(text: str) -> dict[str, object]:
    value = _coerce_uuid(text)
    return {
        "canonical": str(value),
        "hex": value.hex,
        "urn": value.urn,
        "version": value.version,
        "variant": value.variant,
        "is_nil": value.int == 0,
    }
