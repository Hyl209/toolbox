"""yt-dlp download engine, cookie retry logic, and progress hooks."""
from __future__ import annotations

from ..web_backend import (  # noqa: F401
    COOKIE_RETRY_BROWSERS,
    COOKIE_FILE_NAMES,
    _require_web_backend,
    _cookie_browser_name,
    _needs_browser_cookie_retry,
    _iter_cookie_retry_browsers,
    _iter_cookie_file_candidates,
    _can_retry_with_cookie_file,
    _is_cookie_access_blocked_error,
    _build_cookie_retry_failure_message,
    _run_ytdlp_with_cookie_retry,
    _make_web_progress_hook,
    _ffmpeg_path,
    _download_url_with_ytdlp,
)
