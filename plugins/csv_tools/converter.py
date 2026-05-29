from __future__ import annotations

import csv
import json
from io import StringIO


class CsvToolError(Exception):
    pass


def _require_text(text: str) -> str:
    value = str(text)
    if not value.strip():
        raise CsvToolError("请输入 CSV 文本")
    return value


def parse_csv(text: str, delimiter: str = ",") -> list[list[str]]:
    value = _require_text(text)
    rows = [row for row in csv.reader(StringIO(value), delimiter=delimiter)]
    if not rows:
        raise CsvToolError("未读取到 CSV 行")
    return rows


def write_csv(rows: list[list[str]], delimiter: str = ",") -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().rstrip("\n")


def format_csv(text: str, delimiter: str = ",") -> str:
    return write_csv(parse_csv(text, delimiter), delimiter)


def csv_to_tsv(text: str, delimiter: str = ",") -> str:
    return write_csv(parse_csv(text, delimiter), "\t")


def _unique_headers(headers: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for index, header in enumerate(headers, 1):
        base = header.strip() or f"column_{index}"
        counts[base] = counts.get(base, 0) + 1
        result.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return result


def csv_to_json(text: str, delimiter: str = ",", has_header: bool = True) -> str:
    rows = parse_csv(text, delimiter)
    if not has_header:
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if len(rows) < 2:
        raise CsvToolError("带表头转换至少需要 2 行")
    headers = _unique_headers(rows[0])
    records = []
    for row in rows[1:]:
        padded = row + [""] * max(0, len(headers) - len(row))
        records.append(dict(zip(headers, padded[:len(headers)])))
    return json.dumps(records, ensure_ascii=False, indent=2)


def table_summary(text: str, delimiter: str = ",") -> dict[str, int]:
    rows = parse_csv(text, delimiter)
    return {
        "rows": len(rows),
        "columns": max((len(row) for row in rows), default=0),
    }
