"""动态 Tab 加载器 — 按名称按需加载 tab 组件"""
from __future__ import annotations

from typing import Any, Callable, Optional

from ..core.logger import get_logger

logger = get_logger(__name__)

# tab 名称 -> builder 函数 的默认注册表
_BUILTIN_TABS: dict[str, str] = {
    'image-convert': 'image-convert.tab.build_image_convert_tab_class',
    'pdf-tools': 'pdf-tools.tab.build_pdf_tools_tab_class',
    'zipandpng': 'zipandpng.tab.build_zip_tab_class',
    'mp4-mp3': 'mp4-mp3.tab.build_mp4_tab_class',
    'music': 'music.tab.build_music_tab_class',
    'video-downloader': 'video-downloader.tab.build_video_downloader_tab_class',
    'same': 'same.tab.build_same_tab_class',
    'name': 'name.tab.build_name_tab_class',
}


class DynamicTabLoader:
    """根据名称动态加载 tab widget"""

    def __init__(self):
        self._registry: dict[str, Callable[..., Any]] = {}
        self._cache: dict[str, Any] = {}

    def register_tab(self, name: str, builder: Callable[..., Any]) -> None:
        """注册 tab builder 函数"""
        self._registry[name] = builder
        logger.debug(f'注册 tab: {name}')

    def register_tabs(self, mapping: dict[str, Callable[..., Any]]) -> None:
        """批量注册 tab"""
        for name, builder in mapping.items():
            self.register_tab(name, builder)

    def load_tab(self, tab_name: str, deps: dict) -> Any:
        """根据名称动态加载 tab

        Args:
            tab_name: tab 名称，如 'image-convert'
            deps: Qt 依赖字典，传给 builder 函数

        Returns:
            QWidget 实例
        """
        if tab_name in self._cache:
            return self._cache[tab_name]

        builder = self._registry.get(tab_name)
        if builder is None:
            raise KeyError(f'未注册的 tab: {tab_name}')

        logger.info(f'动态加载 tab: {tab_name}')
        tab_class = builder(deps)
        tab_instance = tab_class(deps.get('settings'))
        self._cache[tab_name] = tab_instance
        return tab_instance

    def list_available_tabs(self) -> list[str]:
        """列出所有可用的 tab 名称"""
        return list(self._registry.keys())

    def has_tab(self, name: str) -> bool:
        """检查 tab 是否已注册"""
        return name in self._registry

    def clear_cache(self) -> None:
        """清除已加载的 tab 缓存"""
        self._cache.clear()


def create_default_loader() -> DynamicTabLoader:
    """创建默认的 DynamicTabLoader 并注册内置 tab"""
    loader = DynamicTabLoader()
    for name, module_path in _BUILTIN_TABS.items():
        def _make_builder(mp=module_path):
            def _builder(deps: dict):
                import importlib
                parts = mp.rsplit('.', 1)
                mod = importlib.import_module(parts[0])
                return getattr(mod, parts[1])
            return _builder
        loader.register_tab(name, _make_builder())
    return loader
