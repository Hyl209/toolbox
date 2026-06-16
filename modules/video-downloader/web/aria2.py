"""Aria2 console progress capture, speed/ETA parsing, and related constants.

Actual implementations live in web_backend.py. This module re-exports for
structured access: ``from video_downloader.web.aria2 import X``.
"""
from __future__ import annotations

from ..web_backend import (  # noqa: F401
    ARIA2_PROGRESS_RE,
    ARIA2_VERSION,
    ARIA2_SOURCE_URL,
    _console_capture_lock,
    _PausedDownload,
    _capture_aria2_console_progress,
    _emit_aria2_progress,
    _normalize_aria2_speed,
    _normalize_aria2_eta,
)
