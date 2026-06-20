"""Data types for the video-downloader module."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from threading import Event
from typing import Callable, Literal

SourceKind = Literal['telegram_message', 'telegram_chat', 'web']
"""Supported source types: individual Telegram message, Telegram chat, or web URL."""

ProgressCallback = Callable[[str], None]
"""Signature for progress reporting callbacks."""

DEFAULT_FILENAME_TEMPLATE = '%(title)s [%(id)s].%(ext)s'
"""Default yt-dlp output filename template."""


@dataclass(frozen=True)
class TelegramConfig:
    """Telegram API credentials and session configuration.

    Attributes:
        api_id: Telegram API ID from https://my.telegram.org.
        api_hash: Telegram API hash.
        phone: Phone number in international format (e.g. '+861...').
        session_file: Path to the Telethon session file.
    """
    api_id: str
    api_hash: str
    phone: str
    session_file: str | Path


@dataclass(frozen=True)
class DownloadTask:
    """A single download task describing what to fetch and where to put it.

    Attributes:
        source_url: Full URL to download from.
        source_kind: Type of source (telegram_message, telegram_chat, or web).
        target_title: Preferred filename stem (without extension).
        output_subdir: Subdirectory under the output root for this task.
    """
    source_url: str
    source_kind: SourceKind
    target_title: str = ''
    output_subdir: str = ''


@dataclass(frozen=True)
class DownloadOptions:
    """Configuration for a download batch run.

    Attributes:
        web_use_browser_cookies: Reserved; browser cookies are retried only after cookie-specific errors.
        overwrite: Overwrite existing files instead of creating unique names.
        output_subdir_by_title: Create per-title subdirectories.
        proxy_url: HTTP/SOCKS5 proxy URL (e.g. 'http://127.0.0.1:7890').
        filename_template: yt-dlp output template.
        web_download_all_candidates: Download all candidates instead of just the first.
        max_concurrent_downloads: Max parallel web downloads (0 = auto-probe).
        telegram_recent_limit: Max recent messages to scan (None = all).
        telegram_download_all_messages: Ignore recent_limit and fetch everything.
        telegram_date_from: Only download messages on or after this date.
        telegram_date_to: Only download messages on or before this date.
        telegram_include_videos: Include video messages from Telegram.
        telegram_include_photos: Include photo messages from Telegram.
    """
    web_use_browser_cookies: bool = False
    overwrite: bool = False
    output_subdir_by_title: bool = False
    proxy_url: str = ''
    filename_template: str = DEFAULT_FILENAME_TEMPLATE
    web_download_all_candidates: bool = False
    max_concurrent_downloads: int = 1
    telegram_recent_limit: int | None = 500
    telegram_download_all_messages: bool = False
    telegram_date_from: date | None = None
    telegram_date_to: date | None = None
    telegram_include_videos: bool = True
    telegram_include_photos: bool = False


@dataclass(frozen=True)
class TelegramUrlParts:
    """Parsed components of a Telegram URL.

    Attributes:
        entity_ref: Username string or numeric chat ID.
        message_id: Specific message ID (None for chat-level links).
        invite_hash: Invite hash for private invite links.
    """
    entity_ref: str | int
    message_id: int | None
    invite_hash: str = ''


class DownloadError(RuntimeError):
    """Raised when a download operation fails."""
    pass


class CancelledError(RuntimeError):
    """Raised when a download is cancelled by the user."""
    pass


class Token:
    """Control signals for an active download batch.

    Attributes:
        cancel: Set to request immediate cancellation.
        pause: Set to pause downloads; clear to resume.
        reconnect: Set to force a reconnect of the current download.
    """
    __slots__ = ('cancel', 'pause', 'reconnect')

    def __init__(self) -> None:
        self.cancel = Event()
        self.pause = Event()
        self.reconnect = Event()
