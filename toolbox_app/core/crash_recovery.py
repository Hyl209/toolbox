"""崩溃恢复管理器 — 通过 JSON 文件持久化应用状态。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_STATE_FILE = Path("config") / "recovery.json"


class CrashRecoveryManager:
    """崩溃恢复管理器，将应用状态序列化到 JSON 文件。"""

    def __init__(self, state_file: Path | str | None = None) -> None:
        self._state_file = Path(state_file) if state_file else _DEFAULT_STATE_FILE

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def save_state(self, state: dict[str, Any]) -> None:
        """保存应用状态到磁盘。"""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Recovery state saved to %s", self._state_file)
        except Exception:
            logger.exception("Failed to save recovery state")

    def load_state(self) -> dict[str, Any] | None:
        """从磁盘加载保存的状态，失败或不存在时返回 None。"""
        try:
            if not self._state_file.exists():
                return None
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            logger.info("Recovery state loaded from %s", self._state_file)
            return data
        except Exception:
            logger.exception("Failed to load recovery state")
            return None

    def clear_state(self) -> None:
        """删除保存的状态文件。"""
        try:
            if self._state_file.exists():
                self._state_file.unlink()
                logger.info("Recovery state cleared: %s", self._state_file)
        except Exception:
            logger.exception("Failed to clear recovery state")

    def has_recovery_state(self) -> bool:
        """检查是否存在可恢复的状态文件。"""
        return self._state_file.is_file()
