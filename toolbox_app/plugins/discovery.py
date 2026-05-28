from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional
from .base import PluginBase, PluginInfo
from ..core.logger import get_logger
from ..core.exceptions import PluginError

logger = get_logger(__name__)

# Regex to find class names that inherit from PluginBase
_CLASS_RE = re.compile(r'class\s+(\w+)\s*\(.*PluginBase.*\)')


class PluginDiscovery:
    """插件发现系统

    Discovery is manifest-first: only ``manifest.json`` metadata is read.
    Bare ``.py`` files are scanned with a lightweight regex (no ``exec_module``).
    Actual import/instantiation happens only when a plugin is *enabled*.
    """

    def __init__(self, plugins_dir: str | Path = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent
        self._discovered_plugins: dict[str, PluginInfo] = {}

    def discover_plugins(self) -> dict[str, PluginInfo]:
        """发现所有插件（只读 metadata，不执行插件代码）"""
        self._discovered_plugins.clear()

        # 扫描插件目录
        for plugin_path in self.plugins_dir.iterdir():
            if plugin_path.is_dir():
                self._scan_plugin_directory(plugin_path)
            elif plugin_path.suffix == '.py' and not plugin_path.name.startswith('_'):
                self._scan_plugin_file(plugin_path)

        logger.info(f"发现 {len(self._discovered_plugins)} 个插件")
        return self._discovered_plugins.copy()

    def _scan_plugin_directory(self, plugin_path: Path):
        """扫描插件目录 — 优先读 manifest.json"""
        manifest_path = plugin_path / "manifest.json"
        if manifest_path.exists():
            self._load_manifest(plugin_path, manifest_path)
        else:
            # 无 manifest 的目录：仅做文本扫描，不执行代码
            init_path = plugin_path / "__init__.py"
            if init_path.exists():
                self._scan_plugin_file(init_path, plugin_path.name)

    def _scan_plugin_file(self, plugin_path: Path, plugin_name: str = None):
        """扫描插件文件 — 只读文本查找 PluginBase 子类，不执行模块"""
        try:
            module_name = plugin_name or plugin_path.stem
            source = plugin_path.read_text(encoding='utf-8', errors='ignore')
            matches = _CLASS_RE.findall(source)
            if not matches:
                return

            # 用正则提取 plugin_info（name/version/description/author）
            info = self._extract_info_from_source(source, module_name)
            if info:
                info.plugin_path = str(plugin_path)
                # entry 格式: 文件名:类名 (用第一个匹配的 PluginBase 子类)
                info.entry = f"{plugin_path.name}:{matches[0]}"
                self._discovered_plugins[info.name] = info

        except Exception as e:
            logger.error(f"扫描插件文件失败 {plugin_path}: {e}")

    @staticmethod
    def _extract_info_from_source(source: str, fallback_name: str) -> Optional[PluginInfo]:
        """Try to extract PluginInfo fields from source text via regex."""
        # Match both dict style ("name": "val") and keyword arg style (name="val")
        def _field_re(field: str) -> re.Pattern:
            return re.compile(
                rf"""(?:['"]{field}['"]\s*:\s*|{field}\s*=\s*)['"]([^'"]+)['"]"""
            )

        name_match = _field_re('name').search(source)
        version_match = _field_re('version').search(source)
        desc_match = _field_re('description').search(source)
        author_match = _field_re('author').search(source)
        type_match = _field_re('plugin_type').search(source)
        if not (name_match and version_match):
            return None
        return PluginInfo(
            name=name_match.group(1) if name_match else fallback_name,
            version=version_match.group(1) if version_match else '0.0.0',
            description=desc_match.group(1) if desc_match else '',
            author=author_match.group(1) if author_match else '',
            plugin_type=type_match.group(1) if type_match else 'gui',
        )

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
                priority=manifest.get('priority', 0),
                plugin_type=manifest.get('type', 'gui'),
                entry=manifest.get('entry', ''),
                plugin_path=str(plugin_path),
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
