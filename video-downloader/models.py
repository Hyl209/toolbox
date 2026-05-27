"""Data types for the video-downloader module."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from threading import Event
from typing import Callable, Literal

SourceKind = Literal['telegram_message', 'telegram_chat', 'web']
ProgressCallback = Callable[[str], None]

DEFAULT_FILENAME_TEMPLATE = '%(title)s [%(id)s].%(ext)s'


@dataclass(frozen=True)
class TelegramConfig:
    api_id: str
    api_hash: str
    phone: str
    session_file: str | Path


@dataclass(frozen=True)
class DownloadTask:
    source_url: str
    source_kind: str  # SourceKind
    target_title: str = ''
    output_subdir: str = ''


@dataclass(frozen=True)
class DownloadOptions:
    web_use_browser_cookies: bool = False
    overwrite: bool = False
    filename_template: str = DEFAULT_FILENAME_TEMPLATE
    web_candidate_indices: list[int] | None = None
    web_candidate_mode: str = 'pick'
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
    entity_ref: str | int
    message_id: int | None
    invite_hash: str = ''


class DownloadError(RuntimeError):
    pass


class CancelledError(RuntimeError):
    pass


class Token:
    __slots__ = ('cancel', 'pause', 'reconnect')

    def __init__(self) -> None:
        self.cancel = Event()
        self.pause = Event()
        self.reconnect = Event()
