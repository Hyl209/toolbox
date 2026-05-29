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
_PLUGIN_NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
IGNORED_PLUGIN_DIR_NAMES = {'__pycache__', 'logs', '.codex-pytest-tmp', '.pytest-tmp'}


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
        if not self.plugins_dir.exists():
            logger.info(f"插件目录不存在: {self.plugins_dir}")
            return {}
        if not self.plugins_dir.is_dir():
            logger.warning(f"插件路径不是目录: {self.plugins_dir}")
            return {}

        # 扫描插件目录
        for plugin_path in sorted(self.plugins_dir.iterdir(), key=lambda path: path.name.lower()):
            if self._should_skip_path(plugin_path):
                continue
            if plugin_path.is_dir():
                self._scan_plugin_directory(plugin_path)
            elif plugin_path.suffix == '.py' and not plugin_path.name.startswith('_'):
                self._scan_plugin_file(plugin_path)

        self._drop_cyclic_dependency_plugins()
        logger.info(f"发现 {len(self._discovered_plugins)} 个插件")
        return self._discovered_plugins.copy()

    @staticmethod
    def _should_skip_path(plugin_path: Path) -> bool:
        name = plugin_path.name
        return name in IGNORED_PLUGIN_DIR_NAMES or name.startswith('.')

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
                self._remember_plugin_info(info, plugin_path)

        except Exception as e:
            logger.error(f"扫描插件文件失败 {plugin_path}: {e}")

    def _remember_plugin_info(self, plugin_info: PluginInfo, plugin_path: Path) -> bool:
        if plugin_info.name in self._discovered_plugins:
            existing = self._discovered_plugins[plugin_info.name].plugin_path
            logger.error(
                f"插件名称重复，已跳过: {plugin_info.name} "
                f"({plugin_path}, existing={existing})"
            )
            return False
        self._discovered_plugins[plugin_info.name] = plugin_info
        return True

    @staticmethod
    def _extract_info_from_source(source: str, fallback_name: str) -> Optional[PluginInfo]:
        """Try to extract PluginInfo fields from source text via regex."""
        # 去掉注释行，避免注释中的字段被误匹配
        cleaned = re.sub(r'^\s*#.*$', '', source, flags=re.MULTILINE)

        # Match both dict style ("name": "val") and keyword arg style (name="val")
        def _field_re(field: str) -> re.Pattern:
            return re.compile(
                rf"""(?:['"]{field}['"]\s*:\s*|{field}\s*=\s*)['"]([^'"]+)['"]"""
            )

        name_match = _field_re('name').search(cleaned)
        version_match = _field_re('version').search(cleaned)
        desc_match = _field_re('description').search(cleaned)
        author_match = _field_re('author').search(cleaned)
        type_match = _field_re('plugin_type').search(cleaned)
        sidebar_match = _field_re('sidebar_label').search(cleaned)
        if not (name_match and version_match):
            return None
        plugin_name = PluginDiscovery._validate_plugin_name(
            (name_match.group(1) if name_match else fallback_name).strip(),
            fallback_name,
        )
        plugin_type = (type_match.group(1) if type_match else 'gui').strip()
        if plugin_type not in {'gui', 'hook'}:
            raise PluginError("source plugin_type must be gui or hook", plugin_name)
        return PluginInfo(
            name=plugin_name,
            version=(version_match.group(1) if version_match else '0.0.0').strip(),
            description=(desc_match.group(1) if desc_match else '').strip(),
            author=(author_match.group(1) if author_match else '').strip(),
            plugin_type=plugin_type,
            sidebar_label=(sidebar_match.group(1) if sidebar_match else '').strip(),
        )

    @staticmethod
    def _normalize_dependencies(raw, plugin_name: str) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            items = [raw]
        elif isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            items = raw
        else:
            raise PluginError(
                "manifest.json dependencies must be a string or list of strings",
                plugin_name,
            )
        normalized = [item.strip() for item in items]
        if any(not item for item in normalized):
            raise PluginError(
                "manifest.json dependencies cannot contain empty names",
                plugin_name,
            )
        for item in normalized:
            PluginDiscovery._validate_plugin_name(item, plugin_name, 'dependencies')
            if item == plugin_name:
                raise PluginError(
                    "manifest.json dependencies cannot reference the plugin itself",
                    plugin_name,
                )
        return normalized

    @staticmethod
    def _validate_plugin_name(value: str, plugin_name: str, field: str = 'name') -> str:
        if not _PLUGIN_NAME_RE.fullmatch(value):
            raise PluginError(
                f"manifest.json {field} must use letters, numbers, and underscores only",
                plugin_name,
            )
        return value

    @staticmethod
    def _required_manifest_text(manifest: dict, field: str) -> str:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PluginError(
                f"manifest.json field must be a non-empty string: {field}",
                manifest.get('name'),
            )
        return value.strip()

    @staticmethod
    def _optional_manifest_text(manifest: dict, field: str, default: str = '') -> str:
        value = manifest.get(field, default)
        if not isinstance(value, str):
            raise PluginError(
                f"manifest.json field must be a string: {field}",
                manifest.get('name'),
            )
        return value.strip()

    @staticmethod
    def _optional_manifest_bool(manifest: dict, field: str, default: bool) -> bool:
        value = manifest.get(field, default)
        if not isinstance(value, bool):
            raise PluginError(
                f"manifest.json field must be a boolean: {field}",
                manifest.get('name'),
            )
        return value

    @staticmethod
    def _optional_manifest_int(manifest: dict, field: str, default: int) -> int:
        value = manifest.get(field, default)
        if not isinstance(value, int) or isinstance(value, bool):
            raise PluginError(
                f"manifest.json field must be an integer: {field}",
                manifest.get('name'),
            )
        return value

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

            plugin_type = self._optional_manifest_text(manifest, 'type', 'gui')
            if plugin_type not in {'gui', 'hook'}:
                raise PluginError(
                    "manifest.json type must be gui or hook",
                    manifest.get('name'),
                )

            plugin_name = self._validate_plugin_name(
                self._required_manifest_text(manifest, 'name'),
                manifest.get('name'),
            )
            # 创建插件信息
            plugin_info = PluginInfo(
                name=plugin_name,
                version=self._required_manifest_text(manifest, 'version'),
                description=self._required_manifest_text(manifest, 'description'),
                author=self._required_manifest_text(manifest, 'author'),
                dependencies=self._normalize_dependencies(
                    manifest.get('dependencies'),
                    plugin_name,
                ),
                enabled=self._optional_manifest_bool(manifest, 'enabled', True),
                priority=self._optional_manifest_int(manifest, 'priority', 0),
                plugin_type=plugin_type,
                entry=self._required_manifest_text(manifest, 'entry'),
                plugin_path=str(plugin_path),
                sidebar_label=self._optional_manifest_text(manifest, 'sidebar_label', ''),
            )

            if self._remember_plugin_info(plugin_info, plugin_path):
                logger.debug(f"发现插件: {plugin_info.name} v{plugin_info.version}")

        except Exception as e:
            logger.error(f"加载 manifest.json 失败 {manifest_path}: {e}")

    def _drop_cyclic_dependency_plugins(self) -> None:
        cyclic_plugins: set[str] = set()
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(name: str):
            if name in visiting:
                cyclic_plugins.update(visiting[visiting.index(name):])
                return
            if name in visited:
                return
            info = self._discovered_plugins.get(name)
            if info is None:
                return
            visiting.append(name)
            for dep_name in info.dependencies:
                if dep_name in self._discovered_plugins:
                    visit(dep_name)
            visiting.pop()
            visited.add(name)

        for plugin_name in list(self._discovered_plugins):
            visit(plugin_name)
        for plugin_name in sorted(cyclic_plugins):
            logger.error(f"插件依赖存在循环，已跳过: {plugin_name}")
            self._discovered_plugins.pop(plugin_name, None)

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
