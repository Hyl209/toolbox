from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TimestampToolError(Exception):
    pass


_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
)


def parse_timezone_offset(offset: str | int | float = "+08:00") -> timezone:
    text = str(offset).strip()
    if not text:
        raise TimestampToolError("请输入时区偏移")
    if text.upper() in {"UTC", "Z"}:
        return timezone.utc

    sign = -1 if text.startswith("-") else 1
    value = text[1:] if text[:1] in "+-" else text
    try:
        if ":" in value:
            hour_text, minute_text = value.split(":", 1)
            hours = int(hour_text or "0")
            minutes = int(minute_text or "0")
        elif "." in value:
            total_hours = float(value)
            hours = int(total_hours)
            minutes = round((total_hours - hours) * 60)
        else:
            hours = int(value)
            minutes = 0
    except ValueError as exc:
        raise TimestampToolError("无法识别时区偏移") from exc
    if hours > 23 or minutes > 59:
        raise TimestampToolError("时区偏移超出范围")
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def _require_text(text: str) -> str:
    value = str(text).strip()
    if not value:
        raise TimestampToolError("请输入要转换的时间")
    return value


def _detect_unit(value: float, unit: str) -> tuple[float, str]:
    if unit not in {"auto", "seconds", "milliseconds"}:
        raise TimestampToolError("时间戳单位只能是 auto/seconds/milliseconds")
    if unit == "milliseconds" or (unit == "auto" and abs(value) >= 100_000_000_000):
        return value / 1000, "milliseconds"
    return value, "seconds"


def timestamp_to_datetime(text: str, tz_offset: str = "+08:00", unit: str = "auto") -> dict[str, str]:
    raw = _require_text(text)
    try:
        numeric = float(raw)
    except ValueError as exc:
        raise TimestampToolError("时间戳必须是数字") from exc

    seconds, detected_unit = _detect_unit(numeric, unit)
    tz = parse_timezone_offset(tz_offset)
    try:
        dt = datetime.fromtimestamp(seconds, tz)
    except (OverflowError, OSError, ValueError) as exc:
        raise TimestampToolError("时间戳超出可转换范围") from exc

    return {
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "iso": dt.isoformat(timespec="seconds"),
        "unit": detected_unit,
        "timezone": dt.strftime("%z"),
    }


def parse_datetime_text(text: str, tz_offset: str = "+08:00") -> datetime:
    value = _require_text(text).replace("T", " ")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        dt = None
        for fmt in _DATETIME_FORMATS:
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise TimestampToolError("无法识别时间格式")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=parse_timezone_offset(tz_offset))
    return dt


def datetime_to_timestamp(text: str, tz_offset: str = "+08:00") -> dict[str, int | str]:
    dt = parse_datetime_text(text, tz_offset)
    ts = dt.timestamp()
    seconds = int(ts)
    return {
        "seconds": seconds,
        "milliseconds": round(ts * 1000),
        "iso": dt.isoformat(timespec="seconds"),
    }


def current_time(tz_offset: str = "+08:00") -> dict[str, int | str]:
    now = datetime.now(parse_timezone_offset(tz_offset))
    ts = now.timestamp()
    seconds = int(ts)
    return {
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": seconds,
        "milliseconds": round(ts * 1000),
        "iso": now.isoformat(timespec="seconds"),
    }
