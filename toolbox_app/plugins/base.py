from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = None
    enabled: bool = True
    priority: int = 0

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginBase(ABC):
    """插件基类"""

    def __init__(self):
        self._is_initialized = False
        self._is_enabled = True
        self._plugin_info: Optional[PluginInfo] = None

    @property
    def plugin_info(self) -> PluginInfo:
        """获取插件信息"""
        if self._plugin_info is None:
            self._plugin_info = self.get_plugin_info()
        return self._plugin_info

    @property
    def name(self) -> str:
        return self.plugin_info.name

    @property
    def version(self) -> str:
        return self.plugin_info.version

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @abstractmethod
    def get_plugin_info(self) -> PluginInfo:
        """获取插件信息（子类实现）"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件（子类实现）"""
        pass

    @abstractmethod
    def cleanup(self):
        """清理插件（子类实现）"""
        pass

    def enable(self):
        """启用插件"""
        self._is_enabled = True
        logger.info(f"插件已启用: {self.name}")

    def disable(self):
        """禁用插件"""
        self._is_enabled = False
        logger.info(f"插件已禁用: {self.name}")

    def on_app_start(self):
        """应用启动时的钩子"""
        pass

    def on_app_close(self):
        """应用关闭时的钩子"""
        pass

    def on_theme_change(self, theme: str):
        """主题变更时的钩子"""
        pass

    def on_language_change(self, language: str):
        """语言变更时的钩子"""
        pass

    def get_settings(self) -> dict[str, Any]:
        """获取插件设置"""
        return {}

    def apply_settings(self, settings: dict[str, Any]):
        """应用插件设置"""
        pass

    def get_tab_widget(self) -> Optional[Any]:
        """获取插件提供的 Tab 控件"""
        return None

    def get_menu_items(self) -> list[dict[str, Any]]:
        """获取插件提供的菜单项"""
        return []

    def get_toolbar_items(self) -> list[dict[str, Any]]:
        """获取插件提供的工具栏项"""
        return []

    def handle_command(self, command: str, **kwargs) -> Any:
        """处理插件命令"""
        return None

    def __str__(self):
        return f"{self.name} v{self.version}"

    def __repr__(self):
        return f"<Plugin: {self.name} v{self.version}>"
