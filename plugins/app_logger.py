"""示例非 GUI 插件 — 应用生命周期日志钩子"""
from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo


class AppLoggerPlugin(PluginBase):

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="app_logger",
            version="1.0.0",
            description="示例非 GUI 插件 - 记录应用生命周期事件",
            author="HylToolbox",
            plugin_type="hook",
        )

    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        return True

    def on_app_start(self):
        pass

    def on_app_close(self):
        pass

    def on_theme_change(self, theme: str):
        pass

    def handle_command(self, command: str, **kwargs):
        if command == "ping":
            return "pong"
        return None

    def cleanup(self):
        super().cleanup()
