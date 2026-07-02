from __future__ import annotations

import inspect
import logging
from types import ModuleType
from typing import Any

try:
    from ..runtime_state import current_download_token
except ImportError:  # direct script execution support
    from runtime_state import current_download_token


def add_cancel_token_kwarg(module: ModuleType, kwargs: dict[str, Any], logger: logging.Logger) -> None:
    supports_cancel = bool(getattr(module, "__supports_cancel__", False))
    try:
        signature = inspect.signature(module.download_batch)
    except (TypeError, ValueError):
        logger.warning("download_batch signature unavailable; cancellation may be delayed")
        return

    parameters = signature.parameters
    accepts_token = "token" in parameters or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )
    if supports_cancel and accepts_token:
        kwargs["token"] = current_download_token()
        return
    if supports_cancel:
        logger.warning("download module declares cancel support but download_batch does not accept token; cancellation may be delayed")
        return
    logger.warning("download module does not declare cancel token support; cancellation may be delayed")
    if accepts_token:
        kwargs["token"] = current_download_token()
