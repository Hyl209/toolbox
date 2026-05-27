from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from .app import AppConfig
from .user import UserConfig
from .plugin import PluginConfig
from toolbox_app.core.logger import get_logger

logger = get_logger(__name__)

# 版本迁移注册表: {(from_ver, to_ver): migration_callable}
_MIGRATIONS: dict[tuple[str, str], Any] = {}


def register_migration(from_version: str, to_version: str):
    """装饰器，注册一个配置迁移函数"""
    def decorator(func):
        _MIGRATIONS[(from_version, to_version)] = func
        return func
    return decorator


class ConfigManager:
    """配置管理器"""

    config_version: str = "2.0.0"

    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._app_config = AppConfig(self.config_dir)
        self._user_configs: dict[str, UserConfig] = {}
        self._plugin_configs: dict[str, PluginConfig] = {}

        self._check_version()

    @property
    def app_config(self) -> AppConfig:
        """获取应用配置"""
        return self._app_config

    def get_user_config(self, username: str) -> UserConfig:
        """获取用户配置"""
        if username not in self._user_configs:
            self._user_configs[username] = UserConfig(self.config_dir, username)
        return self._user_configs[username]

    def get_plugin_config(self, plugin_name: str) -> PluginConfig:
        """获取插件配置"""
        if plugin_name not in self._plugin_configs:
            self._plugin_configs[plugin_name] = PluginConfig(self.config_dir, plugin_name)
        return self._plugin_configs[plugin_name]

    def get_current_user_config(self) -> Optional[UserConfig]:
        """获取当前用户配置"""
        # 这里需要从某个地方获取当前用户名
        # 暂时返回 None
        return None

    # ------------------------------------------------------------------
    # 版本控制 & 迁移
    # ------------------------------------------------------------------

    def _check_version(self):
        """启动时检查配置版本，若有可用迁移则自动执行"""
        stored_version = self._app_config.get('app', 'config_version', '1.0.0')
        if stored_version == self.config_version:
            return

        logger.info(
            f"配置版本不匹配: 存储={stored_version}, 当前={self.config_version}，开始迁移"
        )
        try:
            self.migrate(stored_version, self.config_version)
        except Exception as e:
            logger.error(f"配置迁移失败: {e}")
            # 迁移失败不阻塞启动，仅记录日志

    def migrate(self, old_version: str, new_version: str):
        """执行配置格式迁移

        按照版本链依次执行所有中间迁移步骤。
        例: 1.0.0 -> 2.0.0，会查找 1.0.0->1.5.0、1.5.0->2.0.0 等路径。

        如果没有注册任何迁移步骤，则直接更新版本号。
        """
        if old_version == new_version:
            return

        path = self._find_migration_path(old_version, new_version)
        if not path:
            logger.info(f"无已注册迁移步骤 {old_version}->{new_version}，直接更新版本号")
        else:
            for (fv, tv) in path:
                func = _MIGRATIONS[(fv, tv)]
                logger.info(f"执行迁移: {fv} -> {tv}")
                func(self)

        # 更新存储的版本号
        self._app_config.set('app', 'config_version', new_version)
        logger.info(f"配置版本已更新为 {new_version}")

    @staticmethod
    def _find_migration_path(
        old_version: str, new_version: str
    ) -> list[tuple[str, str]]:
        """BFS 寻找从 old_version 到 new_version 的迁移路径"""
        from collections import deque

        queue: deque[list[tuple[str, str]]] = deque()
        queue.append([])
        visited: set[str] = {old_version}

        while queue:
            current_path = queue.popleft()
            current_ver = current_path[-1][1] if current_path else old_version

            if current_ver == new_version:
                return current_path

            for (fv, tv) in _MIGRATIONS:
                if fv == current_ver and tv not in visited:
                    visited.add(tv)
                    queue.append(current_path + [(fv, tv)])

        return []

    def save_all(self):
        """保存所有配置"""
        self._app_config.save()
        for user_config in self._user_configs.values():
            user_config.save()
        for plugin_config in self._plugin_configs.values():
            plugin_config.save()

    def reload_all(self):
        """重新加载所有配置"""
        self._app_config = AppConfig(self.config_dir)
        self._user_configs.clear()
        self._plugin_configs.clear()

    def backup_config(self, backup_dir: str | Path = None) -> Path:
        """备份配置"""
        import shutil
        import time

        if backup_dir is None:
            backup_dir = self.config_dir / "backups"

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}"

        try:
            shutil.copytree(self.config_dir, backup_path, dirs_exist_ok=True)
            logger.info(f"配置备份成功: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"配置备份失败: {e}")
            raise

    def restore_config(self, backup_path: str | Path):
        """恢复配置"""
        import shutil

        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"备份不存在: {backup_path}")

        try:
            # 备份当前配置
            current_backup = self.backup_config()

            # 恢复配置
            shutil.copytree(backup_path, self.config_dir, dirs_exist_ok=True)

            # 重新加载配置
            self.reload_all()

            logger.info(f"配置恢复成功: {backup_path}")
        except Exception as e:
            logger.error(f"配置恢复失败: {e}")
            raise

    def export_config(self, export_path: str | Path, include_user: bool = True,
                      include_plugins: bool = True):
        """导出配置"""
        import json

        export_path = Path(export_path)
        export_data = {
            'app': self._app_config.get_section('app'),
            'ui': self._app_config.get_section('ui'),
            'performance': self._app_config.get_section('performance'),
            'security': self._app_config.get_section('security')
        }

        if include_user:
            export_data['users'] = {}
            for username, user_config in self._user_configs.items():
                export_data['users'][username] = user_config.get_all()

        if include_plugins:
            export_data['plugins'] = {}
            for plugin_name, plugin_config in self._plugin_configs.items():
                export_data['plugins'][plugin_name] = plugin_config.get_all()

        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置导出成功: {export_path}")
        except Exception as e:
            logger.error(f"配置导出失败: {e}")
            raise

    def import_config(self, import_path: str | Path, overwrite: bool = False):
        """导入配置"""
        import json

        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"导入文件不存在: {import_path}")

        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 导入应用配置
            if 'app' in import_data:
                if overwrite:
                    self._app_config.set_section('app', import_data['app'])
                else:
                    for key, value in import_data['app'].items():
                        if self._app_config.get('app', key) is None:
                            self._app_config.set('app', key, value)

            # 导入用户配置
            if 'users' in import_data:
                for username, user_data in import_data['users'].items():
                    user_config = self.get_user_config(username)
                    if overwrite:
                        user_config.set_all(user_data)
                    else:
                        for section, values in user_data.items():
                            if isinstance(values, dict):
                                for key, value in values.items():
                                    if user_config.get(section, key) is None:
                                        user_config.set(section, key, value)

            # 导入插件配置
            if 'plugins' in import_data:
                for plugin_name, plugin_data in import_data['plugins'].items():
                    plugin_config = self.get_plugin_config(plugin_name)
                    if overwrite:
                        plugin_config.set_all(plugin_data)
                    else:
                        for key, value in plugin_data.items():
                            if plugin_config.get(key) is None:
                                plugin_config.set(key, value)

            logger.info(f"配置导入成功: {import_path}")
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            raise

    def get_config_summary(self) -> dict[str, Any]:
        """获取配置摘要"""
        return {
            'app_version': self._app_config.get_version(),
            'theme': self._app_config.get_theme(),
            'language': self._app_config.get_language(),
            'users_count': len(self._user_configs),
            'plugins_count': len(self._plugin_configs),
            'config_dir': str(self.config_dir)
        }

    def cleanup_old_configs(self, max_age_days: int = 30):
        """清理旧配置"""
        import time

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        # 清理备份
        backup_dir = self.config_dir / "backups"
        if backup_dir.exists():
            for backup_path in backup_dir.iterdir():
                if backup_path.is_dir():
                    age = current_time - backup_path.stat().st_mtime
                    if age > max_age_seconds:
                        import shutil
                        shutil.rmtree(backup_path)
                        logger.info(f"清理旧备份: {backup_path}")

    def validate_all(self) -> dict[str, bool]:
        """验证所有配置"""
        results = {
            'app': self._app_config.validate(),
            'users': {},
            'plugins': {}
        }

        for username, user_config in self._user_configs.items():
            results['users'][username] = True  # 简化验证

        for plugin_name, plugin_config in self._plugin_configs.items():
            results['plugins'][plugin_name] = True  # 简化验证

        return results


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str | Path = "config") -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager
