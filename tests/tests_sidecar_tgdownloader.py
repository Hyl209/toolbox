from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def run_tg(task: dict) -> tuple[int, list[dict], str]:
    with tempfile.TemporaryDirectory(prefix="hyl-sidecar-tg-") as tmp:
        input_path = Path(tmp) / "input.json"
        input_path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SIDECAR), "run", "--tool", "tgdownloader", "--input", str(input_path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line]
    return proc.returncode, lines, proc.stderr


def last_event(task: dict) -> dict:
    code, events, stderr = run_tg(task)
    assert stderr == ""
    assert events, "sidecar produced no stdout"
    if events[-1]["type"] != "error":
        assert code == 0
    return events[-1]


def test_tgdownloader_probe_returns_telethon_backend() -> None:
    event = last_event({"task_id": "tg-probe-001", "action": "probe", "payload": {}})

    assert event["type"] == "result"
    assert "telethon" in event["data"]["backends"]
    assert isinstance(event["data"]["backends"]["telethon"]["available"], bool)


def test_tgdownloader_manifest_marks_ready() -> None:
    from sidecar.tool_manifest import build_manifest, load_tool_definitions

    item = next(tool for tool in build_manifest(load_tool_definitions()) if tool["id"] == "tgdownloader")

    assert item["supported_in_tauri"] is True
    assert item["status"] == "ready"


def test_tgdownloader_config_defaults_to_legacy_module_session() -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    config = tool._config({"credentials": {}}, module)

    assert Path(config.session_file) == tool.MODULE_DIR / module.SESSION_FILE_NAME


def test_tgdownloader_config_respects_explicit_session_paths() -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()

    assert tool._config({"credentials": {"session_file": "custom.session"}}, module).session_file == "custom.session"
    assert tool._config({"credentials": {"session_path": "custom-path.session"}}, module).session_file == "custom-path.session"


def test_tgdownloader_parse_telegram_message_and_chat() -> None:
    event = last_event(
        {
            "task_id": "tg-parse-001",
            "action": "parse",
            "payload": {"text": "https://t.me/example/42\nhttps://t.me/example"},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["url_count"] == 2
    assert event["data"]["task_count"] == 2
    assert [task["source_kind"] for task in event["data"]["tasks"]] == ["telegram_message", "telegram_chat"]
    assert event["data"]["errors"] == []


def test_tgdownloader_parse_accepts_payload_url() -> None:
    event = last_event(
        {
            "task_id": "tg-parse-url",
            "action": "parse",
            "payload": {"url": "https://t.me/example/42"},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["url_count"] == 1
    assert event["data"]["task_count"] == 1
    assert event["data"]["tasks"][0]["source_kind"] == "telegram_message"
    assert event["data"]["errors"] == []


def test_tgdownloader_parse_accepts_payload_urls() -> None:
    event = last_event(
        {
            "task_id": "tg-parse-urls",
            "action": "parse",
            "payload": {"urls": ["https://t.me/example/42", "https://t.me/example"]},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["url_count"] == 2
    assert event["data"]["task_count"] == 2
    assert [task["source_kind"] for task in event["data"]["tasks"]] == ["telegram_message", "telegram_chat"]
    assert event["data"]["errors"] == []


def test_tgdownloader_parse_rejects_web_link_as_structured_result() -> None:
    event = last_event(
        {
            "task_id": "tg-parse-mixed",
            "action": "parse",
            "payload": {"text": "https://t.me/example/42\nhttps://example.com/video"},
        }
    )

    assert event["type"] == "result"
    assert event["task_id"] == "tg-parse-mixed"
    assert event["data"]["url_count"] == 2
    assert event["data"]["task_count"] == 1
    assert event["data"]["tasks"][0]["source_kind"] == "telegram_message"
    assert event["data"]["errors"]
    assert "https://example.com/video" in event["data"]["errors"][0]


def test_tgdownloader_validate_good_request(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "tg-validate-good",
            "action": "validate",
            "payload": {
                "urls": ["https://t.me/example/42"],
                "output_dir": str(tmp_path),
                "credentials": {"api_id": "12345", "api_hash": "hash", "phone": "+10000000000"},
                "options": {"recent_limit": 10, "include_videos": True, "include_photos": False},
            },
        }
    )

    assert event["type"] == "result"
    assert event["data"] == {"valid": True, "errors": []}


def test_tgdownloader_validate_missing_credentials_and_output() -> None:
    event = last_event(
        {
            "task_id": "tg-validate-bad",
            "action": "validate",
            "payload": {"text": "https://t.me/example/42", "output_dir": "", "credentials": {}, "options": {}},
        }
    )

    assert event["type"] == "result"
    assert event["data"]["valid"] is False
    assert len(event["data"]["errors"]) >= 2

def _valid_tg_payload(tmp_path: Path, options: dict | None = None) -> dict:
    return {
        "urls": ["https://t.me/example/42"],
        "output_dir": str(tmp_path),
        "credentials": {"api_id": "12345", "api_hash": "hash", "phone": "+10000000000"},
        "options": options or {"recent_limit": 10, "include_videos": True, "include_photos": False},
    }


def test_tgdownloader_validate_all_messages_allows_zero_recent_limit(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "tg-validate-all-zero",
            "action": "validate",
            "payload": _valid_tg_payload(
                tmp_path,
                {
                    "recent_limit": 0,
                    "download_all_messages": True,
                    "include_videos": True,
                    "include_photos": False,
                },
            ),
        }
    )

    assert event["type"] == "result"
    assert event["data"] == {"valid": True, "errors": []}


def test_tgdownloader_validate_rejects_inverted_date_range(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "tg-validate-date-range",
            "action": "validate",
            "payload": _valid_tg_payload(
                tmp_path,
                {
                    "recent_limit": 10,
                    "date_from": "2026-02-02",
                    "date_to": "2026-02-01",
                    "include_videos": True,
                    "include_photos": False,
                },
            ),
        }
    )

    assert event["type"] == "result"
    assert event["data"]["valid"] is False
    assert event["data"]["errors"]


def test_tgdownloader_validate_requires_at_least_one_media_type(tmp_path: Path) -> None:
    event = last_event(
        {
            "task_id": "tg-validate-media-type",
            "action": "validate",
            "payload": _valid_tg_payload(
                tmp_path,
                {"recent_limit": 10, "include_videos": False, "include_photos": False},
            ),
        }
    )

    assert event["type"] == "result"
    assert event["data"]["valid"] is False
    assert event["data"]["errors"]



def test_tgdownloader_download_options_preserve_migrated_settings_and_telegram_filters() -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()

    options = tool._download_options(
        {
            "options": {
                "overwrite": "true",
                "output_subdir_by_title": "1",
                "proxy_host": "127.0.0.1",
                "proxy_port": "7890",
                "max_concurrent_downloads": "3",
                "recent_limit": "12",
                "download_all_messages": "yes",
                "date_from": "2026-02-01",
                "date_to": "2026-02-03",
                "include_videos": False,
                "include_photos": True,
            }
        },
        module,
    )

    assert options.overwrite is True
    assert options.output_subdir_by_title is True
    assert options.proxy_url == "http://127.0.0.1:7890"
    assert options.max_concurrent_downloads == 3
    assert options.telegram_recent_limit == 12
    assert options.telegram_download_all_messages is True
    assert options.telegram_date_from == date(2026, 2, 1)
    assert options.telegram_date_to == date(2026, 2, 3)
    assert options.telegram_include_videos is False
    assert options.telegram_include_photos is True


def test_tgdownloader_download_options_prefers_proxy_url_over_host_port() -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()

    options = tool._download_options(
        {
            "options": {
                "proxy_url": "socks5://127.0.0.1:1080",
                "proxy_host": "127.0.0.1",
                "proxy_port": "7890",
            }
        },
        module,
    )

    assert options.proxy_url == "socks5://127.0.0.1:1080"

def test_tgdownloader_download_calls_legacy_batch_with_telegram_options(monkeypatch, tmp_path: Path) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    calls: list[dict] = []

    def fake_download_batch(tasks, output_dir, telegram_config=None, options=None, progress_cb=None):
        calls.append(
            {
                "tasks": list(tasks),
                "output_dir": output_dir,
                "telegram_config": telegram_config,
                "options": options,
            }
        )
        for index in range(60):
            progress_cb(f"log-{index}")
        return [
            {"success": True, "source_url": "https://t.me/example/42", "files": [tmp_path / "a.mp4"]},
            {"success": False, "source_url": "https://t.me/example/43", "files": [], "error": "boom"},
        ]

    monkeypatch.setattr(module, "download_batch", fake_download_batch)

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-download-call",
            "action": "download",
            "payload": {
                "text": "https://t.me/example/42\nhttps://t.me/example/43",
                "output_dir": str(tmp_path),
                "credentials": {"api_id": "12345", "api_hash": "hash", "phone": "+10000000000"},
                "options": {
                    "recent_limit": "12",
                    "date_from": "2026-02-01",
                    "date_to": "",
                    "include_videos": True,
                    "include_photos": True,
                },
            },
        }
    )

    assert result["ok"] is True
    assert len(calls) == 1
    assert [task.source_url for task in calls[0]["tasks"]] == ["https://t.me/example/42", "https://t.me/example/43"]
    assert calls[0]["output_dir"] == str(tmp_path)
    assert calls[0]["telegram_config"].api_id == "12345"
    assert calls[0]["telegram_config"].session_file.endswith("telegram.session")
    options = calls[0]["options"]
    assert options.telegram_recent_limit == 12
    assert options.telegram_download_all_messages is False
    assert options.telegram_date_from == date(2026, 2, 1)
    assert options.telegram_date_to is None
    assert options.telegram_include_videos is True
    assert options.telegram_include_photos is True
    assert result["data"]["success_count"] == 1
    assert result["data"]["fail_count"] == 1
    assert result["data"]["files"] == [str(tmp_path / "a.mp4")]
    assert result["data"]["errors"] == ["boom"]
    assert result["data"]["logs"] == [f"log-{index}" for index in range(10, 60)]


def test_tgdownloader_warns_when_cancel_token_support_is_not_declared(monkeypatch, tmp_path: Path, caplog) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    monkeypatch.delattr(module, "__supports_cancel__", raising=False)

    def fake_download_batch(tasks, output_dir, telegram_config=None, options=None, progress_cb=None):
        return [{"success": True, "source_url": "https://t.me/example/42", "files": []}]

    monkeypatch.setattr(module, "download_batch", fake_download_batch)

    caplog.set_level(logging.WARNING)
    result = tool.run_tgdownloader(
        {
            "task_id": "tg-download-cancel-support",
            "action": "download",
            "payload": _valid_tg_payload(tmp_path),
        }
    )

    assert result["ok"] is True
    assert "does not declare cancel token support" in caplog.text


def test_tgdownloader_download_mixed_web_url_returns_structured_errors(monkeypatch, tmp_path: Path) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()

    def fail_download_batch(*args, **kwargs):
        raise AssertionError("download_batch should not run for invalid mixed tgdownloader input")

    monkeypatch.setattr(module, "download_batch", fail_download_batch)

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-download-mixed",
            "action": "download",
            "payload": {
                "text": "https://t.me/example/42\nhttps://example.com/video",
                "output_dir": str(tmp_path),
                "credentials": {"api_id": "12345", "api_hash": "hash", "phone": "+10000000000"},
                "options": {"recent_limit": "10"},
            },
        }
    )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 0
    assert result["data"]["fail_count"] == 1
    assert result["data"]["results"] == []
    assert any("https://example.com/video" in error for error in result["data"]["errors"])


def test_tgdownloader_download_missing_credentials_and_output_are_structured_errors(monkeypatch) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()

    def fail_download_batch(*args, **kwargs):
        raise AssertionError("download_batch should not run when legacy validation fails")

    monkeypatch.setattr(module, "download_batch", fail_download_batch)

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-download-invalid",
            "action": "download",
            "payload": {"urls": ["https://t.me/example/42"], "output_dir": "", "credentials": {}, "options": {}},
        }
    )

    assert result["ok"] is True
    assert result["data"]["success_count"] == 0
    assert result["data"]["fail_count"] >= 2
    assert result["data"]["results"] == []
    assert result["data"]["errors"]


def test_tgdownloader_download_options_all_messages_zero_recent_limit(monkeypatch, tmp_path: Path) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    seen_options = []

    def fake_download_batch(tasks, output_dir, telegram_config=None, options=None, progress_cb=None):
        seen_options.append(options)
        return [{"success": True, "source_url": "https://t.me/example", "files": []}]

    monkeypatch.setattr(module, "download_batch", fake_download_batch)

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-download-all-zero",
            "action": "download",
            "payload": _valid_tg_payload(
                tmp_path,
                {
                    "recent_limit": "0",
                    "download_all_messages": True,
                    "date_from": "",
                    "date_to": "2026-03-04",
                },
            ),
        }
    )

    assert result["ok"] is True
    assert seen_options[0].telegram_recent_limit == 0
    assert seen_options[0].telegram_download_all_messages is True
    assert seen_options[0].telegram_date_from is None
    assert seen_options[0].telegram_date_to == date(2026, 3, 4)


def test_tgdownloader_auth_status_direct_monkeypatch_success(monkeypatch) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    monkeypatch.setattr(module, "check_telegram_authorization", lambda config: {"authorized": True, "message": "ok"})

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-auth-001",
            "action": "auth_status",
            "payload": {"credentials": {"api_id": "123", "api_hash": "hash", "phone": "+1"}},
        }
    )

    assert result == {"ok": True, "data": {"authorized": True, "message": "ok"}}


def test_tgdownloader_send_code_direct_monkeypatch_success(monkeypatch) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    module = tool._load_converter_module()
    monkeypatch.setattr(module, "begin_telegram_login", lambda config: {"sent": True, "phone_code_hash": "abc"})

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-code-001",
            "action": "send_code",
            "payload": {"credentials": {"api_id": "123", "api_hash": "hash", "phone": "+1"}},
        }
    )

    assert result == {"ok": True, "data": {"sent": True, "phone_code_hash": "abc"}}


def test_tgdownloader_complete_login_direct_monkeypatch_success(monkeypatch) -> None:
    from sidecar.tools import tgdownloader_tool as tool

    def fake_complete(config, code, phone_code_hash, password_callback=None):
        assert code == "12345"
        assert phone_code_hash == "abc"
        assert password_callback() == "pw"
        return {"authorized": True, "message": "done"}

    module = tool._load_converter_module()
    monkeypatch.setattr(module, "complete_telegram_login", fake_complete)

    result = tool.run_tgdownloader(
        {
            "task_id": "tg-login-001",
            "action": "complete_login",
            "payload": {
                "credentials": {"api_id": "123", "api_hash": "hash", "phone": "+1"},
                "code": "12345",
                "phone_code_hash": "abc",
                "password": "pw",
            },
        }
    )

    assert result == {"ok": True, "data": {"authorized": True, "message": "done"}}


def test_tgdownloader_unknown_action_returns_error() -> None:
    event = last_event({"task_id": "tg-bogus-001", "action": "bogus", "payload": {}})

    assert event["type"] == "error"
    assert event["code"] == "UNKNOWN_ACTION"


def test_tgdownloader_rejects_missing_payload() -> None:
    event = last_event({"task_id": "tg-invalid-001", "action": "parse"})

    assert event["type"] == "error"
    assert event["code"] == "INVALID_PAYLOAD"
