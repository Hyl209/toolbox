from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import pytest

from sidecar import runtime_state
from sidecar.runtime_state import ControlPathError, bind_download_control, current_download_token


def _write_control(path: Path, *, paused: bool = False, cancelled: bool = False, reconnect: bool = False) -> None:
    path.write_text(
        json.dumps(
            {
                "paused": paused,
                "cancelled": cancelled,
                "reconnect": reconnect,
            }
        ),
        encoding="utf-8",
    )


def _wait_until(predicate, timeout: float = 1.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def test_download_control_updates_runtime_token_from_control_file(tmp_path: Path) -> None:
    control_path = tmp_path / "runtime-control.json"
    _write_control(control_path)

    with bind_download_control(control_path):
        token = current_download_token()

        assert token is not None
        assert not token.pause.is_set()
        assert not token.cancel.is_set()

        _write_control(control_path, paused=True)
        assert _wait_until(token.pause.is_set)

        _write_control(control_path, paused=False)
        assert _wait_until(lambda: not token.pause.is_set())

        _write_control(control_path, cancelled=True)
        assert _wait_until(token.cancel.is_set)


def test_download_control_rejects_control_file_outside_temp_dir() -> None:
    with pytest.raises(ControlPathError):
        with bind_download_control(Path.cwd() / "AGENTS.md"):
            pass


def test_download_control_warns_when_watcher_does_not_stop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    class StuckThread:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def start(self) -> None:
            pass

        def join(self, timeout: float | None = None) -> None:
            pass

        def is_alive(self) -> bool:
            return True

    monkeypatch.setattr(runtime_state, "Thread", StuckThread)

    caplog.set_level(logging.WARNING)
    with bind_download_control(tmp_path / "runtime-control.json"):
        pass

    assert "control watcher did not stop in 1s" in caplog.text
