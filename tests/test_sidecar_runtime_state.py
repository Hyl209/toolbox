from __future__ import annotations

import json
import time
from pathlib import Path

from sidecar.runtime_state import bind_download_control, current_download_token


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
