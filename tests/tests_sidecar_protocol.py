import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_sidecar(tool, input_path, control_path=None):
    args = [
        sys.executable,
        str(SIDECAR),
        "run",
        "--tool",
        tool,
        "--input",
        str(input_path),
    ]
    if control_path is not None:
        args.extend(["--control", str(control_path)])
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def json_lines(stdout):
    return [json.loads(line) for line in stdout.splitlines() if line]


def write_input(path, content):
    path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")


def test_base64_emits_progress_and_result_json_lines():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.json"
        write_input(
            input_path,
            {"task_id": "base64-001", "action": "encode_text", "payload": {"text": "hello"}},
        )

        result = run_sidecar("base64", input_path)

    assert result.returncode == 0
    assert result.stderr == ""
    events = json_lines(result.stdout)
    assert events == [
        {"type": "progress", "task_id": "base64-001", "message": "started", "percent": 0},
        {"type": "result", "task_id": "base64-001", "ok": True, "data": {"text": "aGVsbG8="}},
    ]


def test_unknown_tool_emits_single_error_json_line():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.json"
        write_input(input_path, {"task_id": "base64-001", "action": "encode_text", "payload": {}})

        result = run_sidecar("xxx", input_path)

    assert result.returncode != 0
    events = json_lines(result.stdout)
    assert events == [
        {
            "type": "error",
            "task_id": "base64-001",
            "ok": False,
            "code": "UNKNOWN_TOOL",
            "message": "unknown tool: xxx",
        }
    ]


def test_missing_input_file_emits_single_error_json_line():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_sidecar("base64", Path(temp_dir) / "missing.json")

    assert result.returncode != 0
    events = json_lines(result.stdout)
    assert events == [
        {
            "type": "error",
            "task_id": None,
            "ok": False,
            "code": "INPUT_NOT_FOUND",
            "message": "input file not found",
        }
    ]


def test_invalid_json_emits_single_error_json_line():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "bad.json"
        input_path.write_text("{bad json", encoding="utf-8")

        result = run_sidecar("base64", input_path)

    assert result.returncode != 0
    events = json_lines(result.stdout)
    assert events == [
        {
            "type": "error",
            "task_id": None,
            "ok": False,
            "code": "INVALID_JSON",
            "message": "invalid JSON input",
        }
    ]


def test_control_path_outside_temp_dir_emits_single_error_json_line():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.json"
        write_input(input_path, {"task_id": "base64-001", "action": "encode_text", "payload": {"text": "hello"}})

        result = run_sidecar("base64", input_path, ROOT / "AGENTS.md")

    assert result.returncode != 0
    assert result.stderr == ""
    events = json_lines(result.stdout)
    assert events == [
        {
            "type": "error",
            "task_id": "base64-001",
            "ok": False,
            "code": "INVALID_CONTROL_PATH",
            "message": "control file must be under the system temp directory",
        }
    ]
