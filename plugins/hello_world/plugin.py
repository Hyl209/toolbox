"""示例 GUI 插件 — 在侧边栏添加一个 Hello World Tab"""
from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo


class HelloWorldPlugin(PluginBase):

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="hello_world",
            version="1.0.0",
            description="示例 GUI 插件 - Hello World",
            author="HylToolbox",
            plugin_type="gui",
        )

    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        return True

    def get_sidebar_label(self) -> str:
        return "Hello 插件"

    def get_tab_widget(self):
        QWidget = self._deps.get('QWidget')
        QVBoxLayout = self._deps.get('QVBoxLayout')
        QLabel = self._deps.get('QLabel')
        if QWidget is None:
            return None
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Hello from plugin!\n这是一个示例 GUI 插件。")
        label.setStyleSheet("font-size: 18px; padding: 40px;")
        layout.addWidget(label)
        return widget

    def on_app_start(self):
        pass

    def on_app_close(self):
        pass

    def on_theme_change(self, theme: str):
        pass

    def cleanup(self):
        pass
