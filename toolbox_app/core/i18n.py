from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from .logger import get_logger

logger = get_logger(__name__)


class I18nManager:
    """国际化管理器"""

    def __init__(self, locale_dir: str | Path = None, default_locale: str = "zh_CN"):
        if locale_dir is None:
            locale_dir = Path(__file__).parent.parent / "locales"

        self.locale_dir = Path(locale_dir)
        self.locale_dir.mkdir(parents=True, exist_ok=True)

        self.default_locale = default_locale
        self.current_locale = default_locale
        self._translations: dict[str, dict[str, str]] = {}
        self._loaded_locales: set[str] = set()

    def load_locale(self, locale: str):
        """加载语言包"""
        if locale in self._loaded_locales:
            return

        locale_file = self.locale_dir / f"{locale}.json"
        if not locale_file.exists():
            logger.warning(f"语言包不存在: {locale_file}")
            return

        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)

            self._translations[locale] = translations
            self._loaded_locales.add(locale)
            logger.info(f"加载语言包: {locale}")

        except Exception as e:
            logger.error(f"加载语言包失败 {locale}: {e}")

    def set_locale(self, locale: str):
        """设置当前语言"""
        if locale not in self._loaded_locales:
            self.load_locale(locale)

        self.current_locale = locale
        logger.info(f"设置语言: {locale}")

    def get(self, key: str, default: str = None) -> str:
        """获取翻译"""
        # 尝试当前语言
        translation = self._get_translation(self.current_locale, key)
        if translation:
            return translation

        # 尝试默认语言
        if self.current_locale != self.default_locale:
            translation = self._get_translation(self.default_locale, key)
            if translation:
                return translation

        # 返回默认值或键名
        return default or key

    def _get_translation(self, locale: str, key: str) -> Optional[str]:
        """获取指定语言的翻译"""
        if locale not in self._translations:
            return None

        translations = self._translations[locale]

        # 支持嵌套键名 (如 "menu.file.open")
        keys = key.split('.')
        value = translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return str(value) if value is not None else None

    def get_available_locales(self) -> list[str]:
        """获取可用语言列表"""
        locales = []
        for locale_file in self.locale_dir.glob("*.json"):
            locales.append(locale_file.stem)
        return sorted(locales)

    def get_locale_info(self, locale: str) -> Optional[dict[str, str]]:
        """获取语言信息"""
        locale_file = self.locale_dir / f"{locale}.json"
        if not locale_file.exists():
            return None

        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                'code': locale,
                'name': data.get('_name', locale),
                'native_name': data.get('_native_name', locale)
            }
        except Exception:
            return {'code': locale, 'name': locale, 'native_name': locale}

    def format(self, key: str, **kwargs) -> str:
        """格式化翻译"""
        template = self.get(key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def has_translation(self, key: str) -> bool:
        """检查是否有翻译"""
        return self._get_translation(self.current_locale, key) is not None

    def get_translations(self, locale: str = None) -> dict[str, str]:
        """获取所有翻译"""
        locale = locale or self.current_locale
        return self._translations.get(locale, {}).copy()


# 全局国际化管理器实例
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager(locale_dir: str | Path = None, default_locale: str = "zh_CN") -> I18nManager:
    """获取全局国际化管理器实例"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager(locale_dir, default_locale)
    return _i18n_manager


def _(key: str, default: str = None) -> str:
    """翻译快捷函数"""
    return get_i18n_manager().get(key, default)
