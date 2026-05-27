"""启动管理器 — 管理应用启动流程"""
from __future__ import annotations

import importlib
import sys
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)

# 启动时预加载的模块列表
_PRELOAD_MODULES = [
    'toolbox_app.utils',
    'toolbox_app.tab_utils',
    'toolbox_app.loaders',
]


class StartupManager:
    """应用启动管理器"""

    def __init__(self):
        self._splash = None

    def show_splash(self) -> None:
        """显示启动画面（预留接口）"""
        logger.info('启动画面（预留接口）')
        # TODO: 实际实现时创建 QSplashScreen
        self._splash = None

    def preload_modules(self) -> None:
        """预加载常用模块"""
        for mod_name in _PRELOAD_MODULES:
            try:
                importlib.import_module(mod_name)
                logger.debug(f'预加载模块: {mod_name}')
            except ImportError as e:
                logger.warning(f'预加载失败 {mod_name}: {e}')

    def check_dependencies(self) -> list[str]:
        """检查依赖是否满足，返回缺失依赖列表"""
        missing: list[str] = []
        optional_deps = {
            'PySide6': 'GUI 框架',
            'Pillow': '图片处理',
            'pypdf': 'PDF 处理',
        }
        for package, desc in optional_deps.items():
            try:
                importlib.import_module(package.lower().replace('-', '_'))
            except ImportError:
                missing.append(f'{package} ({desc})')
                logger.warning(f'缺失依赖: {package}')
        if missing:
            logger.warning(f'缺失 {len(missing)} 个依赖')
        else:
            logger.info('所有依赖检查通过')
        return missing

    def close_splash(self) -> None:
        """关闭启动画面"""
        if self._splash is not None:
            self._splash.close()
            self._splash = None
