from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token as ContextToken
import json
import logging
from pathlib import Path
import tempfile
from threading import Event, Thread
from typing import Callable, Iterator


ProgressEmitter = Callable[[str, int], None]

_progress_emitter: ContextVar[ProgressEmitter | None] = ContextVar("hyl_progress_emitter", default=None)
_download_token: ContextVar[DownloadToken | None] = ContextVar("hyl_download_token", default=None)
logger = logging.getLogger(__name__)


class ControlPathError(ValueError):
    pass


class DownloadToken:
    def __init__(self) -> None:
        self.cancel = Event()
        self.pause = Event()
        self.reconnect = Event()


@contextmanager
def bind_progress_emitter(emitter: ProgressEmitter | None) -> Iterator[None]:
    token: ContextToken[ProgressEmitter | None] = _progress_emitter.set(emitter)
    try:
        yield
    finally:
        _progress_emitter.reset(token)


def emit_runtime_progress(message: str, percent: int = 0) -> None:
    emitter = _progress_emitter.get()
    if emitter is not None and message:
        emitter(str(message), int(percent))


def current_download_token() -> DownloadToken | None:
    return _download_token.get()


def _read_control_state(path: Path) -> tuple[bool, bool, bool] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    return bool(payload.get("paused")), bool(payload.get("cancelled")), bool(payload.get("reconnect"))


def validate_control_path(path: Path) -> Path:
    expected_base = Path(tempfile.gettempdir()).resolve()
    candidate = Path(path).expanduser().resolve(strict=False)
    try:
        candidate.relative_to(expected_base)
    except ValueError as exc:
        raise ControlPathError("control file must be under the system temp directory") from exc
    return candidate


@contextmanager
def bind_download_control(control_path: Path | None) -> Iterator[DownloadToken | None]:
    token = DownloadToken()
    token_ctx: ContextToken[DownloadToken | None] = _download_token.set(token)
    stop_event = Event()
    watcher: Thread | None = None

    if control_path is not None:
        control_path = validate_control_path(control_path)

        def watch_control() -> None:
            last_state: tuple[bool, bool, bool] | None = None
            while not stop_event.is_set():
                state = _read_control_state(control_path)
                if state is not None and state != last_state:
                    paused, cancelled, reconnect = state
                    if paused:
                        token.pause.set()
                    else:
                        token.pause.clear()
                    if cancelled:
                        token.cancel.set()
                    else:
                        token.cancel.clear()
                    if reconnect:
                        token.reconnect.set()
                    else:
                        token.reconnect.clear()
                    last_state = state
                stop_event.wait(0.1)

        watcher = Thread(target=watch_control, name="hyl-download-control", daemon=True)
        watcher.start()

    try:
        yield token
    finally:
        stop_event.set()
        if watcher is not None:
            watcher.join(timeout=1.0)
            if watcher.is_alive():
                logger.warning("control watcher did not stop in 1s")
        _download_token.reset(token_ctx)
