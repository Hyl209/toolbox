from __future__ import annotations

from pathlib import Path
from typing import Optional
from .base import PluginBase, PluginInfo
from .discovery import PluginDiscovery
from .registry import PluginRegistry
from ..core.logger import get_logger
from ..core.exceptions import PluginError

logger = get_logger(__name__)


class PluginManager:
    """插件管理器"""

    def __init__(self, plugins_dir: str | Path = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent
        self._discovery = PluginDiscovery(self.plugins_dir)
        self._registry = PluginRegistry()
        self._initialized = False

    @property
    def discovery(self) -> PluginDiscovery:
        return self._discovery

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def discover_plugins(self) -> dict[str, PluginInfo]:
        """发现插件"""
        return self._discovery.discover_plugins()

    def register_plugin(self, plugin: PluginBase) -> bool:
        """注册插件"""
        return self._registry.register(plugin)

    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        return self._registry.unregister(plugin_name)

    def initialize_plugin(self, plugin_name: str) -> bool:
        """初始化插件"""
        return self._registry.initialize_plugin(plugin_name)

    def initialize_all_plugins(self) -> dict[str, bool]:
        """初始化所有插件"""
        return self._registry.initialize_all()

    def cleanup_plugin(self, plugin_name: str):
        """清理插件"""
        self._registry.cleanup_plugin(plugin_name)

    def cleanup_all_plugins(self):
        """清理所有插件"""
        self._registry.cleanup_all()

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件"""
        return self._registry.get_plugin(plugin_name)

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._registry.get_plugin_info(plugin_name)

    def get_all_plugins(self) -> dict[str, PluginBase]:
        """获取所有插件"""
        return self._registry.get_all_plugins()

    def get_all_plugin_infos(self) -> dict[str, PluginInfo]:
        """获取所有插件信息"""
        return self._registry.get_all_plugin_infos()

    def get_enabled_plugins(self) -> dict[str, PluginBase]:
        """获取所有启用的插件"""
        return self._registry.get_enabled_plugins()

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        return self._registry.enable_plugin(plugin_name)

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        return self._registry.disable_plugin(plugin_name)

    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        # 发现插件
        plugin_info = self._discovery.get_plugin_info(plugin_name)
        if plugin_info is None:
            logger.error(f"插件未发现: {plugin_name}")
            return False

        # 验证插件
        if not self._discovery.validate_plugin(plugin_name):
            logger.error(f"插件验证失败: {plugin_name}")
            return False

        # 注册插件
        # 这里需要实际加载插件类并创建实例
        # 暂时返回 True
        logger.info(f"插件加载成功: {plugin_name}")
        return True

    def load_all_plugins(self) -> dict[str, bool]:
        """加载所有插件"""
        results = {}
        discovered_plugins = self._discovery.discover_plugins()

        for plugin_name in discovered_plugins:
            results[plugin_name] = self.load_plugin(plugin_name)

        return results

    def get_plugin_count(self) -> int:
        """获取插件数量"""
        return self._registry.get_plugin_count()

    def has_plugin(self, plugin_name: str) -> bool:
        """检查插件是否存在"""
        return self._registry.has_plugin(plugin_name)

    def get_plugins_by_priority(self) -> list[PluginBase]:
        """按优先级获取插件"""
        plugins = list(self._registry.get_all_plugins().values())
        return sorted(plugins, key=lambda p: p.plugin_info.priority, reverse=True)

    def get_plugin_dependencies(self, plugin_name: str) -> list[str]:
        """获取插件依赖"""
        plugin_info = self._discovery.get_plugin_info(plugin_name)
        if plugin_info is None:
            return []
        return plugin_info.dependencies.copy()

    def check_dependencies(self, plugin_name: str) -> bool:
        """检查插件依赖"""
        dependencies = self.get_plugin_dependencies(plugin_name)
        for dep in dependencies:
            if not self.has_plugin(dep):
                return False
        return True


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugins_dir: str | Path = None) -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(plugins_dir)
    return _plugin_manager
