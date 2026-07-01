from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_pdftools(task: dict) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "pdftools", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    assert proc.stderr == ""
    lines = [line for line in proc.stdout.splitlines() if line]
    assert lines, "sidecar produced no stdout"
    return [json.loads(line) for line in lines]


def make_pdf(path: Path, pages: int = 1) -> Path:
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def test_pdftools_lists_pdf_inputs_recursively() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        (root / "a.pdf").write_bytes(b"%PDF-1.4")
        (root / "ignore.txt").write_text("ignore", encoding="utf-8")
        nested = root / "nested"
        nested.mkdir()
        (nested / "b.PDF").write_bytes(b"%PDF-1.4")

        events = run_pdftools(
            {
                "task_id": "pdftools-001",
                "action": "list",
                "payload": {"paths": [str(root)]},
            },
        )

    event = events[-1]
    assert event["type"] == "result"
    assert [item["name"] for item in event["data"]["files"]] == ["a.pdf", "b.PDF"]


def test_pdftools_merges_two_pdfs() -> None:
    pypdf = pytest.importorskip("pypdf")
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        first = make_pdf(root / "a.pdf", pages=1)
        second = make_pdf(root / "b.pdf", pages=2)
        out_dir = root / "out"

        events = run_pdftools(
            {
                "task_id": "pdftools-002",
                "action": "merge",
                "payload": {"paths": [str(first), str(second)], "output_dir": str(out_dir)},
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        output = Path(event["data"]["results"][0]["output"])
        reader = pypdf.PdfReader(str(output))
        assert output.name == "merged.pdf"
        assert len(reader.pages) == 3


def test_pdftools_splits_selected_pages() -> None:
    pypdf = pytest.importorskip("pypdf")
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        source = make_pdf(root / "source.pdf", pages=3)
        out_dir = root / "out"

        events = run_pdftools(
            {
                "task_id": "pdftools-003",
                "action": "split",
                "payload": {"paths": [str(source)], "output_dir": str(out_dir), "page_ranges": "1,3"},
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        outputs = [Path(item["output"]) for item in event["data"]["results"]]
        assert [path.name for path in outputs] == ["source_page_001.pdf", "source_page_003.pdf"]
        assert all(len(pypdf.PdfReader(str(path)).pages) == 1 for path in outputs)


def test_pdftools_probe_ocr_reports_status() -> None:
    events = run_pdftools({"task_id": "pdftools-004", "action": "probe_ocr", "payload": {}})

    event = events[-1]
    assert event["type"] == "result"
    assert isinstance(event["data"]["available"], bool)
    assert isinstance(event["data"]["message"], str)


def test_pdftools_rejects_merge_with_one_input() -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        source = make_pdf(root / "source.pdf")
        events = run_pdftools(
            {
                "task_id": "pdftools-005",
                "action": "merge",
                "payload": {"paths": [str(source)], "output_dir": str(root / "out")},
            },
        )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"


def test_pdftools_converts_pdf_to_images() -> None:
    pytest.importorskip("fitz")
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        source = make_pdf(root / "source.pdf", pages=1)
        out_dir = root / "images"

        events = run_pdftools(
            {
                "task_id": "pdftools-006",
                "action": "images",
                "payload": {
                    "paths": [str(source)],
                    "output_dir": str(out_dir),
                    "image_format": "png",
                    "dpi": 72,
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        outputs = [Path(item["output"]) for item in event["data"]["results"]]
        assert [path.name for path in outputs] == ["source_page_001.png"]
        assert all(path.is_file() and path.stat().st_size > 0 for path in outputs)


def test_pdftools_exports_pdf_text_without_ocr_fallback() -> None:
    pytest.importorskip("fitz")
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        source = make_pdf(root / "source.pdf", pages=1)
        out_dir = root / "text"

        events = run_pdftools(
            {
                "task_id": "pdftools-007",
                "action": "text",
                "payload": {
                    "paths": [str(source)],
                    "output_dir": str(out_dir),
                    "text_export_format": "txt",
                    "ocr_fallback": False,
                },
            },
        )

        event = events[-1]
        assert event["type"] == "result"
        output = Path(event["data"]["results"][0]["output"])
        assert output.name == "source.txt"
        assert output.is_file()


def test_pdftools_unknown_action_returns_error() -> None:
    events = run_pdftools({"task_id": "pdftools-008", "action": "bogus", "payload": {}})

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "UNKNOWN_ACTION"


@pytest.mark.parametrize("action", ["merge", "split", "images", "text"])
def test_pdftools_actions_require_output_dir(action: str) -> None:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-pdftools-files-") as tmp:
        root = Path(tmp)
        first = make_pdf(root / "a.pdf")
        second = make_pdf(root / "b.pdf")
        payload: dict[str, object] = {
            "paths": [str(first), str(second)] if action == "merge" else [str(first)],
        }
        if action == "split":
            payload["page_ranges"] = "1"

        events = run_pdftools(
            {
                "task_id": f"pdftools-missing-output-{action}",
                "action": action,
                "payload": payload,
            },
        )

    event = events[-1]
    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
