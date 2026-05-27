"""配置兼容层 — 提供 IniSettings 兼容接口，内部使用 AppConfig"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class IniSettingsAdapter:
    """兼容 IniSettings 接口的适配器，内部委托给 AppConfig

    用法：
        adapter = IniSettingsAdapter('/path/to/config_dir')
        adapter.setValue('ui/theme', 'dark')
        theme = adapter.value('ui/theme', 'dark')
        adapter.sync()
    """

    def __init__(self, config_dir: str | Path):
        from .app import AppConfig
        self._app_config = AppConfig(config_dir)

    def setValue(self, key: str, value: str) -> None:
        """设置配置值（兼容 IniSettings.setValue）"""
        section, option = self._split_key(key)
        self._app_config.set(section, option, value)

    def value(self, key: str, default: str = '') -> str:
        """获取配置值（兼容 IniSettings.value）"""
        section, option = self._split_key(key)
        result = self._app_config.get(section, option, default)
        return str(result) if result is not None else default

    def sync(self) -> None:
        """持久化配置（兼容 IniSettings.sync）"""
        self._app_config.save()

    def get_app_config(self) -> AppConfig:
        """获取内部 AppConfig 实例"""
        return self._app_config

    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:
        if '/' in key:
            section, option = key.split('/', 1)
            return section, option
        return 'default', key
