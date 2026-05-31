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
                logger.debug('预加载模块: %s', mod_name)
            except ImportError as e:
                logger.warning('预加载失败 %s: %s', mod_name, e)

    def check_dependencies(self) -> list[str]:
        """检查依赖是否满足，返回缺失依赖列表"""
        missing: list[str] = []
        optional_deps = {
            'PySide6': ('PySide6', 'GUI 框架'),
            'Pillow': ('PIL', '图片处理'),
            'pypdf': ('pypdf', 'PDF 处理'),
        }
        for package, (import_name, desc) in optional_deps.items():
            try:
                importlib.import_module(import_name)
            except ImportError:
                missing.append(f'{package} ({desc})')
                logger.warning('缺失依赖: %s', package)
        if missing:
            logger.warning('缺失 %s 个依赖', len(missing))
        else:
            logger.info('所有依赖检查通过')
        return missing

    def close_splash(self) -> None:
        """关闭启动画面"""
        if self._splash is not None:
            self._splash.close()
            self._splash = None
