from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from toolbox_app.core.logger import get_logger

logger = get_logger(__name__)


class PluginConfig:
    """插件配置"""

    def __init__(self, config_dir: str | Path, plugin_name: str):
        self.config_dir = Path(config_dir)
        self.plugin_name = plugin_name
        self.plugin_dir = self.config_dir / "plugins" / plugin_name
        self.config_file = self.plugin_dir / "config.json"
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug(f"插件配置加载成功: {self.plugin_name}")
            except Exception as e:
                logger.error(f"加载插件配置失败: {e}")
                self._config = {}
        else:
            self._config = {}

    def save(self):
        """保存配置"""
        try:
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.debug(f"插件配置保存成功: {self.plugin_name}")
        except Exception as e:
            logger.error(f"保存插件配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value
        self.save()

    def get_all(self) -> dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def set_all(self, config: dict[str, Any]):
        """设置所有配置"""
        self._config = config
        self.save()

    def remove(self, key: str):
        """删除配置项"""
        if key in self._config:
            del self._config[key]
            self.save()

    def clear(self):
        """清空配置"""
        self._config = {}
        self.save()

    def has(self, key: str) -> bool:
        """检查配置项是否存在"""
        return key in self._config

    def keys(self) -> list[str]:
        """获取所有配置键"""
        return list(self._config.keys())

    def values(self) -> list[Any]:
        """获取所有配置值"""
        return list(self._config.values())

    def items(self) -> list[tuple[str, Any]]:
        """获取所有配置项"""
        return list(self._config.items())

    def update(self, config: dict[str, Any]):
        """更新配置"""
        self._config.update(config)
        self.save()

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """获取嵌套配置值"""
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set_nested(self, *keys: str, value: Any):
        """设置嵌套配置值"""
        if len(keys) == 0:
            return

        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        self.save()

    def validate(self, schema: dict[str, Any] = None) -> bool:
        """验证配置"""
        if schema is None:
            return True

        try:
            for key, expected_type in schema.items():
                if key not in self._config:
                    return False
                if not isinstance(self._config[key], expected_type):
                    return False
            return True
        except Exception:
            return False

    def get_with_default(self, key: str, default_factory: callable) -> Any:
        """获取配置值，如果不存在则使用默认工厂函数"""
        if key not in self._config:
            self._config[key] = default_factory()
            self.save()
        return self._config[key]

    def increment(self, key: str, amount: int = 1) -> int:
        """递增配置值"""
        current = self.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def decrement(self, key: str, amount: int = 1) -> int:
        """递减配置值"""
        return self.increment(key, -amount)

    def toggle(self, key: str) -> bool:
        """切换布尔配置值"""
        current = self.get(key, False)
        new_value = not current
        self.set(key, new_value)
        return new_value

    def append_to_list(self, key: str, item: Any, max_length: int = None):
        """添加到列表配置"""
        current = self.get(key, [])
        if not isinstance(current, list):
            current = []

        if item in current:
            current.remove(item)

        current.insert(0, item)

        if max_length and len(current) > max_length:
            current = current[:max_length]

        self.set(key, current)

    def remove_from_list(self, key: str, item: Any):
        """从列表配置中移除"""
        current = self.get(key, [])
        if isinstance(current, list) and item in current:
            current.remove(item)
            self.set(key, current)

    def get_list_item(self, key: str, index: int, default: Any = None) -> Any:
        """获取列表配置中的指定项"""
        current = self.get(key, [])
        if isinstance(current, list) and 0 <= index < len(current):
            return current[index]
        return default

    def set_list_item(self, key: str, index: int, value: Any):
        """设置列表配置中的指定项"""
        current = self.get(key, [])
        if not isinstance(current, list):
            current = []

        while len(current) <= index:
            current.append(None)

        current[index] = value
        self.set(key, current)
