from __future__ import annotations

import sys
from pathlib import Path


def project_root(file: str, dev_parent_levels: int) -> Path:
    """Return repo/data root in dev and PyInstaller one-file runtimes."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(file).resolve().parents[dev_parent_levels]
