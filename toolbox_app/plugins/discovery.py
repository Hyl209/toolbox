from __future__ import annotations

import json
import importlib
import importlib.util
from pathlib import Path
from typing import Optional
from .base import PluginBase, PluginInfo
from ..core.logger import get_logger
from ..core.exceptions import PluginError

logger = get_logger(__name__)


class PluginDiscovery:
    """插件发现系统"""

    def __init__(self, plugins_dir: str | Path = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent
        self._discovered_plugins: dict[str, PluginInfo] = {}

    def discover_plugins(self) -> dict[str, PluginInfo]:
        """发现所有插件"""
        self._discovered_plugins.clear()

        # 扫描插件目录
        for plugin_path in self.plugins_dir.iterdir():
            if plugin_path.is_dir():
                self._scan_plugin_directory(plugin_path)
            elif plugin_path.suffix == '.py':
                self._scan_plugin_file(plugin_path)

        logger.info(f"发现 {len(self._discovered_plugins)} 个插件")
        return self._discovered_plugins.copy()

    def _scan_plugin_directory(self, plugin_path: Path):
        """扫描插件目录"""
        manifest_path = plugin_path / "manifest.json"
        if manifest_path.exists():
            self._load_manifest(plugin_path, manifest_path)
        else:
            # 尝试加载 __init__.py
            init_path = plugin_path / "__init__.py"
            if init_path.exists():
                self._scan_plugin_file(init_path, plugin_path.name)

    def _scan_plugin_file(self, plugin_path: Path, plugin_name: str = None):
        """扫描插件文件"""
        try:
            # 尝试导入模块
            module_name = plugin_name or plugin_path.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginBase) and
                    attr is not PluginBase):

                    # 创建临时实例获取插件信息
                    try:
                        temp_instance = attr()
                        plugin_info = temp_instance.get_plugin_info()
                        self._discovered_plugins[plugin_info.name] = plugin_info
                    except Exception as e:
                        logger.error(f"加载插件信息失败 {module_name}: {e}")

        except Exception as e:
            logger.error(f"扫描插件文件失败 {plugin_path}: {e}")

    def _load_manifest(self, plugin_path: Path, manifest_path: Path):
        """加载 manifest.json"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # 验证 manifest
            required_fields = ['name', 'version', 'description', 'author', 'entry']
            for field in required_fields:
                if field not in manifest:
                    raise PluginError(f"manifest.json 缺少必需字段: {field}", manifest.get('name'))

            # 创建插件信息
            plugin_info = PluginInfo(
                name=manifest['name'],
                version=manifest['version'],
                description=manifest['description'],
                author=manifest['author'],
                dependencies=manifest.get('dependencies', []),
                enabled=manifest.get('enabled', True),
                priority=manifest.get('priority', 0)
            )

            self._discovered_plugins[plugin_info.name] = plugin_info
            logger.debug(f"发现插件: {plugin_info.name} v{plugin_info.version}")

        except Exception as e:
            logger.error(f"加载 manifest.json 失败 {manifest_path}: {e}")

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取指定插件信息"""
        return self._discovered_plugins.get(plugin_name)

    def get_all_plugins(self) -> dict[str, PluginInfo]:
        """获取所有发现的插件"""
        return self._discovered_plugins.copy()

    def get_enabled_plugins(self) -> dict[str, PluginInfo]:
        """获取所有启用的插件"""
        return {
            name: info for name, info in self._discovered_plugins.items()
            if info.enabled
        }

    def validate_plugin(self, plugin_name: str) -> bool:
        """验证插件是否有效"""
        plugin_info = self._discovered_plugins.get(plugin_name)
        if plugin_info is None:
            return False

        # 检查依赖
        for dep in plugin_info.dependencies:
            if dep not in self._discovered_plugins:
                logger.warning(f"插件 {plugin_name} 缺少依赖: {dep}")
                return False

        return True
