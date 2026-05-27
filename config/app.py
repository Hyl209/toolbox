from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from ..toolbox_app.core.logger import get_logger

logger = get_logger(__name__)


class AppConfig:
    """应用配置"""

    DEFAULT_VALUES = {
        'app': {
            'name': 'HylToolbox',
            'version': '2.0.0',
            'config_version': '2.0.0',
            'language': 'zh_CN',
            'theme': 'dark',
            'auto_save': True,
            'log_level': 'INFO',
            'check_updates': True,
            'startup_tool': '',
            'window_geometry': None,
            'window_state': None
        },
        'ui': {
            'sidebar_width': 196,
            'font_size': 12,
            'font_family': 'Microsoft YaHei',
            'animations_enabled': True,
            'show_tooltips': True,
            'compact_mode': False
        },
        'performance': {
            'max_concurrent_tasks': 5,
            'auto_cleanup_temp': True,
            'temp_max_age_hours': 24,
            'cache_enabled': True,
            'cache_max_size_mb': 100
        },
        'security': {
            'auto_lock_minutes': 30,
            'require_password_on_start': False,
            'encrypt_sensitive_data': True
        }
    }

    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "app.json"
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug("应用配置加载成功")
            except Exception as e:
                logger.error(f"加载应用配置失败: {e}")
                self._config = {}
        else:
            self._config = {}

        # 合并默认值
        self._merge_defaults()

    def _merge_defaults(self):
        """合并默认值"""
        for section, values in self.DEFAULT_VALUES.items():
            if section not in self._config:
                self._config[section] = {}
            for key, value in values.items():
                if key not in self._config[section]:
                    self._config[section][key] = value

    def save(self):
        """保存配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.debug("应用配置保存成功")
        except Exception as e:
            logger.error(f"保存应用配置失败: {e}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """设置配置值"""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save()

    def get_section(self, section: str) -> dict[str, Any]:
        """获取整个配置节"""
        return self._config.get(section, {}).copy()

    def set_section(self, section: str, values: dict[str, Any]):
        """设置整个配置节"""
        self._config[section] = values
        self.save()

    def remove(self, section: str, key: str):
        """删除配置项"""
        if section in self._config and key in self._config[section]:
            del self._config[section][key]
            self.save()

    def reset_to_defaults(self):
        """重置为默认值"""
        self._config = {}
        self._merge_defaults()
        self.save()

    def validate(self) -> bool:
        """验证配置"""
        try:
            # 检查必需字段
            for section, values in self.DEFAULT_VALUES.items():
                if section not in self._config:
                    return False
                for key in values:
                    if key not in self._config[section]:
                        return False

            # 检查值类型
            if not isinstance(self.get('app', 'version'), str):
                return False
            if not isinstance(self.get('ui', 'sidebar_width'), int):
                return False

            return True
        except Exception:
            return False

    def get_version(self) -> str:
        """获取应用版本"""
        return self.get('app', 'version', '2.0.0')

    def get_theme(self) -> str:
        """获取主题"""
        return self.get('app', 'theme', 'dark')

    def set_theme(self, theme: str):
        """设置主题"""
        self.set('app', 'theme', theme)

    def get_language(self) -> str:
        """获取语言"""
        return self.get('app', 'language', 'zh_CN')

    def set_language(self, language: str):
        """设置语言"""
        self.set('app', 'language', language)

    def is_auto_save_enabled(self) -> bool:
        """检查是否启用自动保存"""
        return self.get('app', 'auto_save', True)

    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get('app', 'log_level', 'INFO')

    def get_max_concurrent_tasks(self) -> int:
        """获取最大并发任务数"""
        return self.get('performance', 'max_concurrent_tasks', 5)

    def get_sidebar_width(self) -> int:
        """获取侧边栏宽度"""
        return self.get('ui', 'sidebar_width', 196)
