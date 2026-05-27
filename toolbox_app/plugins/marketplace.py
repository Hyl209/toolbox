"""插件市场 — 预留接口，当前所有操作返回空/False。"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PluginMarketplace:
    """插件市场管理器（预留接口）。"""

    def list_available(self) -> list[dict[str, Any]]:
        """列出可用插件。当前返回空列表。"""
        return []

    def install(self, plugin_name: str) -> bool:
        """安装指定插件。当前为预留实现，返回 False。"""
        logger.warning("PluginMarketplace.install not implemented: %s", plugin_name)
        return False

    def uninstall(self, plugin_name: str) -> bool:
        """卸载指定插件。当前为预留实现，返回 False。"""
        logger.warning("PluginMarketplace.uninstall not implemented: %s", plugin_name)
        return False

    def search(self, keyword: str) -> list[dict[str, Any]]:
        """搜索插件。当前返回空列表。"""
        return []
