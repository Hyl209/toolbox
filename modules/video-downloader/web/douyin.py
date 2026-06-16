"""Douyin (TikTok China) share link parsing and candidate extraction."""
from __future__ import annotations

from ..web_backend import (  # noqa: F401
    DOUYIN_HOSTS,
    _is_douyin_url,
    _normalize_douyin_play_url,
    _is_douyin_direct_play_url,
    _fetch_douyin_share_html,
    _extract_douyin_page_json,
    _find_douyin_item_list,
    _extract_douyin_share_candidates,
)
