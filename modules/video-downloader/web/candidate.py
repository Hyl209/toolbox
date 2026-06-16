"""Candidate management, yt-dlp entry extraction, media candidate collection."""
from __future__ import annotations

from ..web_backend import (  # noqa: F401
    MEDIA_URL_RE,
    RELATIVE_MEDIA_RE,
    _is_m3u8_url,
    _pick_candidates,
    _select_candidates,
    _inverse_indices,
    _normalize_web_candidate_url,
    _collect_ytdlp_entry_candidates,
    _collect_ytdlp_candidate_entries,
    _extract_ytdlp_entry_candidates,
    _fetch_webpage_html,
    _extract_media_candidates,
    _normalize_thumbnail_url,
    _collect_thumbnail_urls_from_info,
    _select_ytdlp_thumbnail_entry,
    _extract_thumbnail_urls,
    _supports_ytdlp_direct_media,
    _collect_web_media_candidates,
)
