from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from toolbox_app.core.logger import get_logger

logger = get_logger(__name__)


class UserConfig:
    """用户配置"""

    DEFAULT_VALUES = {
        'preferences': {
            'remember_password': False,
            'auto_login': False,
            'last_tool': '',
            'last_directory': '',
            'recent_files': [],
            'favorite_tools': []
        },
        'ui': {
            'window_geometry': None,
            'window_state': None,
            'sidebar_collapsed': False,
            'active_tab': 0
        },
        'tools': {},
        'shortcuts': {
            'quit': 'Ctrl+Q',
            'settings': 'Ctrl+,',
            'help': 'F1',
            'new_window': 'Ctrl+N'
        }
    }

    def __init__(self, config_dir: str | Path, username: str):
        self.config_dir = Path(config_dir)
        self.username = username
        self.user_dir = self.config_dir / "users" / username
        self.config_file = self.user_dir / "user.json"
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug(f"用户配置加载成功: {self.username}")
            except Exception as e:
                logger.error(f"加载用户配置失败: {e}")
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
            if isinstance(values, dict):
                for key, value in values.items():
                    if key not in self._config[section]:
                        self._config[section][key] = value

    def save(self):
        """保存配置"""
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.debug(f"用户配置保存成功: {self.username}")
        except Exception as e:
            logger.error(f"保存用户配置失败: {e}")

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

    def get_preferences(self) -> dict[str, Any]:
        """获取偏好设置"""
        return self.get_section('preferences')

    def set_preference(self, key: str, value: Any):
        """设置偏好"""
        self.set('preferences', key, value)

    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取偏好"""
        return self.get('preferences', key, default)

    def is_remember_password(self) -> bool:
        """是否记住密码"""
        return self.get_preference('remember_password', False)

    def set_remember_password(self, value: bool):
        """设置记住密码"""
        self.set_preference('remember_password', value)

    def is_auto_login(self) -> bool:
        """是否自动登录"""
        return self.get_preference('auto_login', False)

    def set_auto_login(self, value: bool):
        """设置自动登录"""
        self.set_preference('auto_login', value)

    def get_last_tool(self) -> str:
        """获取上次使用的工具"""
        return self.get_preference('last_tool', '')

    def set_last_tool(self, tool_name: str):
        """设置上次使用的工具"""
        self.set_preference('last_tool', tool_name)

    def get_last_directory(self) -> str:
        """获取上次使用的目录"""
        return self.get_preference('last_directory', '')

    def set_last_directory(self, directory: str):
        """设置上次使用的目录"""
        self.set_preference('last_directory', directory)

    def get_recent_files(self, max_count: int = 10) -> list[str]:
        """获取最近文件"""
        recent = self.get_preference('recent_files', [])
        return recent[:max_count]

    def add_recent_file(self, file_path: str, max_count: int = 10):
        """添加最近文件"""
        recent = self.get_recent_files(max_count)
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.set_preference('recent_files', recent[:max_count])

    def clear_recent_files(self):
        """清空最近文件"""
        self.set_preference('recent_files', [])

    def get_favorite_tools(self) -> list[str]:
        """获取收藏的工具"""
        return self.get_preference('favorite_tools', [])

    def add_favorite_tool(self, tool_name: str):
        """添加收藏工具"""
        favorites = self.get_favorite_tools()
        if tool_name not in favorites:
            favorites.append(tool_name)
            self.set_preference('favorite_tools', favorites)

    def remove_favorite_tool(self, tool_name: str):
        """移除收藏工具"""
        favorites = self.get_favorite_tools()
        if tool_name in favorites:
            favorites.remove(tool_name)
            self.set_preference('favorite_tools', favorites)

    def get_tool_config(self, tool_name: str) -> dict[str, Any]:
        """获取工具配置"""
        return self.get('tools', tool_name, {})

    def set_tool_config(self, tool_name: str, config: dict[str, Any]):
        """设置工具配置"""
        self.set('tools', tool_name, config)

    def get_shortcut(self, action: str) -> str:
        """获取快捷键"""
        return self.get('shortcuts', action, '')

    def set_shortcut(self, action: str, shortcut: str):
        """设置快捷键"""
        self.set('shortcuts', action, shortcut)

    def get_window_geometry(self) -> Optional[dict]:
        """获取窗口几何信息"""
        return self.get('ui', 'window_geometry')

    def set_window_geometry(self, geometry: dict):
        """设置窗口几何信息"""
        self.set('ui', 'window_geometry', geometry)

    def get_window_state(self) -> Optional[dict]:
        """获取窗口状态"""
        return self.get('ui', 'window_state')

    def set_window_state(self, state: dict):
        """设置窗口状态"""
        self.set('ui', 'window_state', state)

    def is_sidebar_collapsed(self) -> bool:
        """侧边栏是否折叠"""
        return self.get('ui', 'sidebar_collapsed', False)

    def set_sidebar_collapsed(self, collapsed: bool):
        """设置侧边栏折叠状态"""
        self.set('ui', 'sidebar_collapsed', collapsed)

    def get_active_tab(self) -> int:
        """获取活动标签页"""
        return self.get('ui', 'active_tab', 0)

    def set_active_tab(self, tab_index: int):
        """设置活动标签页"""
        self.set('ui', 'active_tab', tab_index)
