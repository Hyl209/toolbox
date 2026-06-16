"""Thumbnail embedding, downloading, and video frame extraction."""
from __future__ import annotations

from ..web_backend import (  # noqa: F401
    _guess_thumbnail_suffix,
    _download_thumbnail_file,
    _extract_video_frame_thumbnail,
    _video_has_embedded_thumbnail,
    _maybe_fill_missing_embedded_thumbnails,
    embed_thumbnail,
)
