"""Video downloader converter -- public API re-export layer.

All logic lives in sub-modules (models, progress, source_parser,
telegram_backend, web_backend, _shared).  This file re-exports the
public API so that ``from video_downloader.converter import X`` works.

Internal / underscore-prefixed symbols are NOT re-exported here.
Use the sub-modules directly if you need private helpers.
"""
from __future__ import annotations

# ── Data types & models ──────────────────────────────────────────────
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

# ── Source parsing & validation ──────────────────────────────────────
from .source_parser import (
    parse_task_lines,
    build_download_tasks,
    normalize_recent_limit,
    normalize_positive_indices,
    parse_iso_date,
    normalize_proxy_url,
    build_proxy_url,
    split_proxy_url,
    normalize_date_range,
    validate_download_request,
    probe_download_backends,
)

# ── Telegram backend ─────────────────────────────────────────────────
from .telegram_backend import (
    check_telegram_authorization,
    begin_telegram_login,
    complete_telegram_login,
)

# ── Web download backend ─────────────────────────────────────────────
from .web_backend import (
    download_batch,
    inspect_web_media_batch,
    inspect_web_media_candidates,
    embed_thumbnail,
)

# ── Shared utilities ─────────────────────────────────────────────────
from ._shared import (
    sanitize_filename_component,
    ensure_unique_path,
    ensure_unique_stem,
    classify_source,
    guess_task_title,
    SESSION_FILE_NAME,
)

# ── Sub-package (for structured access) ──────────────────────────────
from . import web as web  # noqa: F401
from . import _shared as _shared  # noqa: F401
