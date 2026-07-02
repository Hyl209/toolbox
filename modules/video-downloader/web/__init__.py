"""Web download sub-package.

This package provides a structured API for web downloading.  The actual
implementations live in the parent ``web_backend`` module; this package
re-exports public symbols so that downstream code can import from
``video_downloader.web`` instead of ``video_downloader.web_backend``.

Sub-module breakdown (logical grouping):
- aria2:  Aria2 console progress capture, speed/ETA parsing
- ytdlp:  yt-dlp download engine, cookie retry, progress hooks
- m3u8:   FFmpeg m3u8 download, stream probing
- douyin: Douyin share link parsing, candidate extraction
- candidate: Candidate management, yt-dlp entry extraction
- orchestrator: Batch orchestration, concurrency, task routing
- thumbnail: Thumbnail embedding, downloading, frame extraction
- speed:  Speed tracking and concurrency mapping
"""
from __future__ import annotations

# Re-export everything from web_backend for backward compatibility.
# The web_backend module is the single source of truth for implementations.
from ..web_backend import (  # noqa: F401
    # Constants
    ARIA2_PROGRESS_RE,
    MEDIA_URL_RE,
    RELATIVE_MEDIA_RE,
    ARIA2_VERSION,
    ARIA2_SOURCE_URL,
    COOKIE_RETRY_BROWSERS,
    COOKIE_FILE_NAMES,
    DOUYIN_HOSTS,
    _INTER_TASK_DELAY_RANGE,
    _console_capture_lock,
    # Aria2
    _PausedDownload,
    _capture_aria2_console_progress,
    _monitor_aria2_file_progress,
    _emit_aria2_progress,
    _emit_aria2_file_progress,
    _extract_ytdlp_total_bytes,
    _normalize_aria2_speed,
    _normalize_aria2_eta,
    # Common
    _options_proxy_url,
    _urlopen_with_proxy,
    _require_web_backend,
    # Cookie / retry
    _cookie_browser_name,
    _needs_browser_cookie_retry,
    _iter_cookie_retry_browsers,
    _iter_cookie_file_candidates,
    _can_retry_with_cookie_file,
    _is_cookie_access_blocked_error,
    _build_cookie_retry_failure_message,
    _run_ytdlp_with_cookie_retry,
    # yt-dlp
    _make_web_progress_hook,
    _ffmpeg_path,
    _download_url_with_ytdlp,
    # Candidate
    _is_m3u8_url,
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
    # Direct download
    _download_direct_media_file,
    # Douyin
    _is_douyin_url,
    _normalize_douyin_play_url,
    _is_douyin_direct_play_url,
    _fetch_douyin_share_html,
    _extract_douyin_page_json,
    _find_douyin_item_list,
    _extract_douyin_share_candidates,
    # M3U8
    _download_m3u8_with_ffmpeg,
    _probe_stream_duration,
    _terminate_ffmpeg,
    # Speed
    _SpeedTracker,
    _parse_speed_bytes,
    _speed_to_concurrency,
    # Thumbnail
    _guess_thumbnail_suffix,
    _download_thumbnail_file,
    _extract_video_frame_thumbnail,
    _video_has_embedded_thumbnail,
    _maybe_fill_missing_embedded_thumbnails,
    embed_thumbnail,
    # Orchestrator
    _run_async,
    _wait_if_paused,
    _check_paused_non_blocking,
    _run_web_task,
    _resolve_web_task_output_dir,
    _download_web_task,
    _download_web_candidate,
    _download_web_candidates,
    _download_web_entries,
    _download_web_sequential,
    _download_web_concurrent,
    _download_web_auto,
    _expand_web_all_candidates,
    inspect_web_media_batch,
    inspect_web_media_candidates,
    download_batch,
)
