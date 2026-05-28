"""Legacy v1 config manager (simple JSON key-value).

.. deprecated::
    Use ``config.manager.ConfigManager`` (v2) instead.
    This module is kept for backward compatibility only.

Authoritative implementation: ``config/manager.py``
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from .logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Legacy v1 config manager — use ``config.manager.ConfigManager`` for new code."""

    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: dict[str, dict[str, Any]] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """加载所有配置文件"""
        for config_file in self.config_dir.glob("*.json"):
            try:
                self._load_config(config_file.stem)
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_file}: {e}")

    def _load_config(self, name: str) -> dict[str, Any]:
        """加载指定配置文件"""
        if name in self._configs:
            return self._configs[name]

        config_file = self.config_dir / f"{name}.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self._configs[name] = config
                return config
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_file}: {e}")

        # 返回默认配置
        default_config = self._get_default_config(name)
        self._configs[name] = default_config
        return default_config

    def _get_default_config(self, name: str) -> dict[str, Any]:
        """获取默认配置"""
        defaults = {
            'app': {
                'version': '1.0.0',
                'language': 'zh_CN',
                'theme': 'dark',
                'auto_save': True,
                'log_level': 'INFO'
            },
            'user': {
                'username': '',
                'remember_password': False,
                'auto_login': False,
                'last_tool': ''
            },
            'plugins': {
                'enabled': [],
                'disabled': []
            }
        }
        return defaults.get(name, {})

    def get(self, name: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self._load_config(name)
        return config.get(key, default)

    def set(self, name: str, key: str, value: Any) -> None:
        """设置配置值"""
        config = self._load_config(name)
        config[key] = value
        self._save_config(name)

    def _save_config(self, name: str) -> None:
        """保存配置到文件"""
        config_file = self.config_dir / f"{name}.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._configs[name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败 {config_file}: {e}")

    def reload(self, name: str) -> None:
        """重新加载配置"""
        if name in self._configs:
            del self._configs[name]
        self._load_config(name)

    def get_all(self, name: str) -> dict[str, Any]:
        """获取整个配置"""
        return self._load_config(name).copy()

    def update(self, name: str, updates: dict[str, Any]) -> None:
        """批量更新配置"""
        config = self._load_config(name)
        config.update(updates)
        self._save_config(name)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str | Path = "config") -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager
