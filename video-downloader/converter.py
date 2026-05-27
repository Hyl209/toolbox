"""Video downloader converter -- thin re-export layer.

All logic lives in sub-modules.  This file re-exports for backward
compatibility so that ``from video_downloader.converter import X`` still works.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Wildcard re-exports (public names from each sub-module)
# ---------------------------------------------------------------------------
from .models import *  # noqa: F401,F403
from .progress import *  # noqa: F401,F403
from .source_parser import *  # noqa: F401,F403
from .telegram_backend import *  # noqa: F401,F403
from .web_backend import *  # noqa: F401,F403
from . import _shared as _shared  # noqa: F401

# ---------------------------------------------------------------------------
# Explicit re-exports for private / underscore-prefixed symbols that callers
# depend on.  Wildcard imports skip names starting with "_", so these must be
# listed individually.
# ---------------------------------------------------------------------------

from .models import (
    SourceKind,
    ProgressCallback,
    DEFAULT_FILENAME_TEMPLATE,
    TelegramConfig,
    DownloadTask,
    DownloadOptions,
    TelegramUrlParts,
    DownloadError,
    CancelledError,
    Token,
)

from .source_parser import (
    ARIA2_PROGRESS_RE,
    _state,
    _check_cancel,
    _current_token,
    _set_current_token,
    _require_token,
    parse_task_lines,
    build_download_tasks,
    _coerce_tasks,
    normalize_recent_limit,
    _parse_candidate_mode,
    _resolve_candidate_indices,
    normalize_positive_indices,
    parse_iso_date,
    normalize_date_range,
    validate_download_request,
    probe_download_backends,
)

from .progress import (
    ANSI_ESCAPE_RE,
    WHITESPACE_RE,
    _normalize_progress_text,
    _coerce_float,
    _format_progress_percent,
    _format_byte_rate,
    _format_eta_seconds,
    _parse_ffmpeg_time,
    _format_duration,
    _estimate_download_rate,
    _build_download_log_message,
    _resolve_web_percent_text,
    _resolve_web_speed_text,
    _emit_web_transfer_progress,
    _emit,
    _emit_task_start,
    _emit_task_done,
    _emit_scan_progress,
    _emit_file_select,
    _make_result,
)

from .telegram_backend import (
    _require_telegram_backend,
    _create_telegram_client,
    _check_telegram_authorization_async,
    _begin_telegram_login_async,
    _complete_telegram_login_async,
    check_telegram_authorization,
    begin_telegram_login,
    complete_telegram_login,
    _download_telegram_entries,
    _download_single_telegram_task,
    _resolve_telegram_entity,
    _download_telegram_message_media,
    _parse_telegram_url,
    _is_video_message,
    _is_photo_message,
    _message_matches_media_selection,
    _get_entity_title,
    _dialog_matches_invite,
    _resolve_task_output_dir,
    _normalize_message_datetime,
    _date_start_utc,
    _date_end_utc,
)

from .web_backend import (
    MEDIA_URL_RE,
    RELATIVE_MEDIA_RE,
    ARIA2_VERSION,
    ARIA2_SOURCE_URL,
    _console_capture_lock,
    _INTER_TASK_DELAY_RANGE,
    _capture_aria2_console_progress,
    _emit_aria2_progress,
    _normalize_aria2_speed,
    _normalize_aria2_eta,
    _require_web_backend,
    _run_web_task,
    _download_web_entries,
    _download_web_sequential,
    _download_web_concurrent,
    _download_web_auto,
    _SpeedTracker,
    _parse_speed_bytes,
    _speed_to_concurrency,
    _expand_web_all_candidates,
    download_batch,
    _is_m3u8_url,
    _download_web_candidate,
    _download_web_candidates,
    inspect_web_media_batch,
    inspect_web_media_candidates,
    _download_web_task,
    _pick_candidates,
    _select_candidates,
    _inverse_indices,
    _collect_web_media_candidates,
    _download_url_with_ytdlp,
    _fetch_webpage_html,
    _extract_media_candidates,
    _extract_ytdlp_entry_candidates,
    _collect_ytdlp_entry_candidates,
    _supports_ytdlp_direct_media,
    _normalize_web_candidate_url,
    _download_m3u8_with_ffmpeg,
    _probe_stream_duration,
    _make_web_progress_hook,
    embed_thumbnail,
)

from ._shared import (
    TELEGRAM_HOSTS,
    INVALID_FILENAME_CHARS,
    SESSION_FILE_NAME,
    WEB_USER_AGENT,
    _stem_lock,
    sanitize_filename_component,
    ensure_unique_path,
    ensure_unique_stem,
    _find_files_by_stem,
    _find_completed_downloads,
    _normalize_url_text,
    classify_source,
    guess_task_title,
    _resolve_bundled_tool,
    _resolve_aria2c_path,
    _build_backend_status,
    _build_web_headers,
    _build_ffmpeg_header_text,
)
