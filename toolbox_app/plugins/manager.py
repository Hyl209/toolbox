from __future__ import annotations

import importlib.util
import sys
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
        self._loaded_module_names: dict[str, str] = {}  # plugin_name → sys.modules key

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

    def initialize_plugin(self, plugin_name: str, deps: dict = None) -> bool:
        """初始化插件"""
        return self._registry.initialize_plugin(plugin_name, deps)

    def initialize_all_plugins(self, deps: dict = None) -> dict[str, bool]:
        """初始化所有插件"""
        return self._registry.initialize_all(deps)

    def cleanup_plugin(self, plugin_name: str):
        """清理插件"""
        self._registry.cleanup_plugin(plugin_name)

    def cleanup_all_plugins(self):
        """清理所有插件"""
        self._registry.cleanup_all()
        # 清理 sys.modules 中注入的插件模块，防止内存泄漏
        for name, module_name in self._loaded_module_names.items():
            sys.modules.pop(module_name, None)
        self._loaded_module_names.clear()

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

    def load_plugin(self, plugin_name: str, disabled_names: set[str] = None) -> bool:
        """加载单个插件：发现 → 验证 → 导入 → 实例化 → 注册"""
        plugin_info = self._discovery.get_plugin_info(plugin_name)
        if plugin_info is None:
            logger.error(f"插件未发现: {plugin_name}")
            return False

        # 跳过 manifest 中标记为 disabled 或被用户禁用的插件
        if not plugin_info.enabled:
            logger.info(f"插件已禁用 (manifest): {plugin_name}")
            return False
        if disabled_names and plugin_name in disabled_names:
            logger.info(f"插件已禁用 (用户设置): {plugin_name}")
            return False

        if not self._discovery.validate_plugin(plugin_name):
            logger.error(f"插件验证失败: {plugin_name}")
            return False

        try:
            instance = self._instantiate_plugin(plugin_info)
            if instance is None:
                return False
            return self._registry.register(instance)
        except Exception as e:
            logger.error(f"加载插件异常 {plugin_name}: {e}")
            return False

    def _instantiate_plugin(self, plugin_info: PluginInfo) -> Optional[PluginBase]:
        """根据 PluginInfo 导入模块并实例化 PluginBase 子类"""
        entry = plugin_info.entry
        plugin_path = Path(plugin_info.plugin_path)

        if not entry:
            logger.error(f"插件缺少 entry: {plugin_info.name}")
            return None

        # 解析 entry: "file.py:ClassName"
        if ':' in entry:
            file_part, class_name = entry.rsplit(':', 1)
        else:
            file_part, class_name = entry, None

        # 确定模块文件路径
        if plugin_path.is_dir():
            module_file = plugin_path / file_part
        elif plugin_path.is_file():
            module_file = plugin_path
        else:
            logger.error(f"插件路径不存在: {plugin_path}")
            return None

        if not module_file.exists():
            logger.error(f"插件入口文件不存在: {module_file}")
            return None

        # 防止路径遍历：加载文件必须在插件目录内
        resolved = module_file.resolve()
        if not resolved.is_relative_to(self.plugins_dir.resolve()):
            logger.error(f"插件入口路径越界: {resolved}")
            return None

        # 用 importlib 加载模块
        qualified_name = f"plugin_{plugin_info.name}"
        spec = importlib.util.spec_from_file_location(qualified_name, str(resolved))
        if spec is None or spec.loader is None:
            logger.error(f"无法加载插件模块: {module_file}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            sys.modules.pop(qualified_name, None)
            logger.error(f"插件模块执行失败 {module_file}: {e}")
            return None

        # 找 PluginBase 子类
        target_class = None
        if class_name:
            target_class = getattr(module, class_name, None)
            if target_class is None:
                logger.error(f"插件类 {class_name} 未找到于 {module_file}")
                return None
        else:
            # 自动找第一个 PluginBase 子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, PluginBase)
                        and attr is not PluginBase):
                    target_class = attr
                    break

        if target_class is None:
            logger.error(f"插件中未找到 PluginBase 子类: {module_file}")
            return None

        # 实例化
        instance = target_class()
        self._loaded_module_names[plugin_info.name] = qualified_name
        logger.info(f"插件实例化成功: {plugin_info.name}")
        return instance

    def load_all_plugins(self, disabled_names: set[str] = None) -> dict[str, bool]:
        """加载所有发现的插件"""
        results = {}
        discovered_plugins = self._discovery.discover_plugins()

        for plugin_name, info in sorted(
            discovered_plugins.items(),
            key=lambda x: x[1].priority,
            reverse=True,
        ):
            results[plugin_name] = self.load_plugin(plugin_name, disabled_names)

        return results

    def set_plugin_enabled(self, plugin_name: str, enabled: bool):
        """设置插件启用状态（内存）"""
        if enabled:
            self.enable_plugin(plugin_name)
        else:
            self.disable_plugin(plugin_name)

    def get_disabled_plugin_names(self) -> set[str]:
        """获取所有禁用的插件名"""
        return {
            name for name, p in self._registry.get_all_plugins().items()
            if not p.is_enabled
        }

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


def reset_plugin_manager():
    """重置全局插件管理器（测试用）"""
    global _plugin_manager
    if _plugin_manager is not None:
        _plugin_manager.cleanup_all_plugins()
    _plugin_manager = None
