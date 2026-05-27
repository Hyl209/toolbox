from __future__ import annotations

from typing import Optional
from .base import PluginBase, PluginInfo
from ..core.logger import get_logger
from ..core.exceptions import PluginError

logger = get_logger(__name__)


class PluginRegistry:
    """插件注册系统"""

    def __init__(self):
        self._plugins: dict[str, PluginBase] = {}
        self._plugin_infos: dict[str, PluginInfo] = {}

    def register(self, plugin: PluginBase) -> bool:
        """注册插件"""
        try:
            plugin_info = plugin.plugin_info

            if plugin_info.name in self._plugins:
                raise PluginError(f"插件已注册: {plugin_info.name}", plugin_info.name)

            self._plugins[plugin_info.name] = plugin
            self._plugin_infos[plugin_info.name] = plugin_info

            logger.info(f"插件已注册: {plugin_info.name} v{plugin_info.version}")
            return True

        except Exception as e:
            logger.error(f"注册插件失败: {e}")
            return False

    def unregister(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]
        try:
            plugin.cleanup()
        except Exception as e:
            logger.error(f"清理插件失败 {plugin_name}: {e}")

        del self._plugins[plugin_name]
        del self._plugin_infos[plugin_name]

        logger.info(f"插件已注销: {plugin_name}")
        return True

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件"""
        return self._plugins.get(plugin_name)

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._plugin_infos.get(plugin_name)

    def get_all_plugins(self) -> dict[str, PluginBase]:
        """获取所有插件"""
        return self._plugins.copy()

    def get_all_plugin_infos(self) -> dict[str, PluginInfo]:
        """获取所有插件信息"""
        return self._plugin_infos.copy()

    def get_enabled_plugins(self) -> dict[str, PluginBase]:
        """获取所有启用的插件"""
        return {
            name: plugin for name, plugin in self._plugins.items()
            if plugin.is_enabled
        }

    def initialize_plugin(self, plugin_name: str) -> bool:
        """初始化插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return False

        if plugin.is_initialized:
            return True

        try:
            result = plugin.initialize()
            if result:
                logger.info(f"插件初始化成功: {plugin_name}")
            else:
                logger.warning(f"插件初始化失败: {plugin_name}")
            return result
        except Exception as e:
            logger.error(f"插件初始化异常 {plugin_name}: {e}")
            return False

    def initialize_all(self) -> dict[str, bool]:
        """初始化所有插件"""
        results = {}
        for plugin_name in self._plugins:
            results[plugin_name] = self.initialize_plugin(plugin_name)
        return results

    def cleanup_plugin(self, plugin_name: str):
        """清理插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return

        try:
            plugin.cleanup()
            logger.info(f"插件清理完成: {plugin_name}")
        except Exception as e:
            logger.error(f"插件清理失败 {plugin_name}: {e}")

    def cleanup_all(self):
        """清理所有插件"""
        for plugin_name in list(self._plugins.keys()):
            self.cleanup_plugin(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return False

        plugin.enable()
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return False

        plugin.disable()
        return True

    def get_plugin_count(self) -> int:
        """获取插件数量"""
        return len(self._plugins)

    def has_plugin(self, plugin_name: str) -> bool:
        """检查插件是否存在"""
        return plugin_name in self._plugins
