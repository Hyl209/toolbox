"""Backward-compatible re-export layer.

All implementation lives in sub-modules. This file re-exports everything
so that ``from .converter import X`` continues to work unchanged.

A custom module class with property descriptors ensures that monkey-patching
``_probe_video`` and ``_build_video_signature`` on this module propagates
to the shared function references used by sub-modules.
"""
from __future__ import annotations

import sys as _sys
import types as _types

# --- Shared constants and utilities from _common ---
from ._common import (  # noqa: F401
    DEFAULT_TARGET_DIR_NAME,
    HASH_CHUNK_SIZE,
    FFPROBE_PATH,
    FFMPEG_PATH,
    VIDEO_SUFFIXES,
    VIDEO_SAMPLE_COUNT,
    VIDEO_FRAME_WIDTH,
    VIDEO_FRAME_HEIGHT,
    VIDEO_MIN_FRAME_COUNT,
    VIDEO_DURATION_TOLERANCE_SECONDS,
    VIDEO_ASPECT_RATIO_TOLERANCE,
    VIDEO_SIMILARITY_THRESHOLD,
    MEDIA_COMMAND_TIMEOUT_SECONDS,
    VIDEO_PARALLEL_WORKERS,
    _CACHE_MAX_SIZE,
    _BoundedCache,
    _ensure_root,
    _normalize_target_dir_name,
    _iter_top_level_files,
    _iter_recursive_files,
    _scan_files_from_root,
    scan_files,
    _group_by_size,
    _is_video_file,
    _map_parallel,
    _safe_float,
    _build_cache_key,
    resolve_name_conflict,
    _build_group,
    _split_video_and_other_files,
    probe_video_ref,
    build_video_signature_ref,
)

# --- Exact duplicate detection from exact_duplicate ---
from .exact_duplicate import (  # noqa: F401
    hash_file,
    _build_exact_duplicate_groups,
    find_duplicate_groups,
)

# --- Video similarity detection from video_signature ---
from .video_signature import (  # noqa: F401
    _probe_video,
    _extract_video_frames,
    _build_video_signature,
    _frame_similarity,
    _video_similarity_score,
    _build_video_similarity_groups,
)

# --- Duplicate file moving from move_plan ---
from .move_plan import (  # noqa: F401
    _build_target_path,
    _resolve_move_inputs,
    move_duplicates,
)


# ---------------------------------------------------------------------------
# Custom module class: property descriptors for _probe_video and
# _build_video_signature so that monkey-patching on this module propagates
# to the shared _FnRef objects used by sub-modules at call time.
# ---------------------------------------------------------------------------

class _ConverterModule(_types.ModuleType):
    """Module subclass that syncs _probe_video / _build_video_signature
    patches to the shared function-reference holders in _common."""

    @property  # type: ignore[override]
    def _probe_video(self):  # type: ignore[override]
        return probe_video_ref.fn

    @_probe_video.setter
    def _probe_video(self, value):  # type: ignore[override]
        probe_video_ref.fn = value

    @property  # type: ignore[override]
    def _build_video_signature(self):  # type: ignore[override]
        return build_video_signature_ref.fn

    @_build_video_signature.setter
    def _build_video_signature(self, value):  # type: ignore[override]
        build_video_signature_ref.fn = value


# Activate the custom class on *this* module (works for both normal import
# and the test's importlib-based loading).
_sys.modules[__name__].__class__ = _ConverterModule
