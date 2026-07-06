from __future__ import annotations

import configparser
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from .tool_manifest import build_manifest, load_tool_definitions
except ImportError:  # direct script execution support
    from tool_manifest import build_manifest, load_tool_definitions


try:
    from .runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 1)
DEFAULT_SETTINGS = ROOT / "hyl_toolbox.ini"
DEFAULT_PLUGINS_DIR = ROOT / "plugins"
READY_PLUGIN_NAMES = {
    "archive_extractor",
    "csv_tools",
    "file_hasher",
    "json_tools",
    "regex_tools",
    "text_tools",
    "timestamp_tools",
    "url_tools",
    "uuid_tools",
}
_PLUGIN_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")

THEME_ZONES = (
    "window_bg",
    "surface_bg",
    "card_bg",
    "accent",
    "text_primary",
    "text_secondary",
    "input_bg",
)
TOOL_OUTPUT_DIR_KEYS = (
    "base64",
    "music",
    "zipandpng",
    "mp4mp3",
    "imageconvert",
    "pdftools",
    "directdownloader",
    "archive_extractor",
)
FILESORTER_CATEGORIES = ("图片", "视频", "音频", "文档", "压缩包", "程序", "其他")
TOOL_BEHAVIOR_STRING_DEFAULTS = {
    "batchrename/input_dir": "",
    "batchrename/prefix": "批量命名",
    "batchrename/group_mode": "按后缀",
    "batchrename/sort_mode": "按命名",
    "batchrename/sort_order": "从小到大",
    "filesorter/input_dir": "",
    "filesorter/mode": "按大类分类",
    "same/input_dir": "",
    "directdownloader/connections": "16",
    "directdownloader/proxy_url": "",
    "directdownloader/referer": "",
}
TOOL_BEHAVIOR_BOOL_DEFAULTS = {
    "same/recursive": True,
    "directdownloader/overwrite": False,
    "directdownloader/output_subdir_by_filename": False,
}
VIDEO_DOWNLOADER_SHARED_STRING_KEYS = {
    "video_downloader/api_id",
    "video_downloader/api_hash",
    "video_downloader/phone",
    "video_downloader/phone_code_hash",
}
VIDEO_DOWNLOADER_MODE_STRING_KEYS = {
    "output_dir",
    "proxy_host",
    "proxy_port",
    "proxy_url",
    "concurrent",
    "cover_dir",
    "recent_limit",
    "date_from",
    "date_to",
}
VIDEO_DOWNLOADER_MODE_BOOL_KEYS = {
    "overwrite",
    "output_subdir_by_title",
    "all_messages",
    "include_videos",
    "include_photos",
}
VIDEO_DOWNLOADER_MODES = {"web", "telegram"}
WORD_FORMATTER_CONVERTER = ROOT / "modules" / "word-formatter" / "converter.py"
WORD_FORMATTER_NUMERIC_STYLE_FIELDS = {
    "size_pt",
    "line_spacing",
    "space_before_pt",
    "space_after_pt",
    "first_line_indent_cm",
}
_WORD_FORMATTER_CONVERTER_CACHE: Any = None

DEFAULT_COLORS = {
    "dark": {
        "window_bg": "#1b1f25",
        "surface_bg": "#1f2329",
        "card_bg": "rgba(44, 50, 59, 0.70)",
        "accent": "#6f95c7",
        "text_primary": "#eef2f7",
        "text_secondary": "#9aa6b5",
        "input_bg": "#2a3038",
    },
    "light": {
        "window_bg": "#e5e9ef",
        "surface_bg": "#eef1f5",
        "card_bg": "rgba(255, 255, 255, 0.38)",
        "accent": "#e4efff",
        "text_primary": "#1f252d",
        "text_secondary": "#697586",
        "input_bg": "#eef1f5",
    },
}


def _validate_background_image_path(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    image_path = Path(cleaned).expanduser()
    if not image_path.is_absolute():
        raise SettingsUpdateError("ui/background_image must be an absolute path")
    appdata = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))).expanduser()
    allowed_dir = appdata / "hyl-toolbox" / "backgrounds"
    try:
        common = os.path.commonpath(
            [
                os.path.normcase(os.path.abspath(str(allowed_dir))),
                os.path.normcase(os.path.abspath(str(image_path))),
            ]
        )
    except ValueError as exc:
        raise SettingsUpdateError(f"ui/background_image must be under {allowed_dir}") from exc
    if common != os.path.normcase(os.path.abspath(str(allowed_dir))):
        raise SettingsUpdateError(f"ui/background_image must be under {allowed_dir}")
    return cleaned


class SettingsUpdateError(ValueError):
    pass


def _word_formatter_converter() -> Any:
    global _WORD_FORMATTER_CONVERTER_CACHE
    if _WORD_FORMATTER_CONVERTER_CACHE is not None:
        return _WORD_FORMATTER_CONVERTER_CACHE
    spec = importlib.util.spec_from_file_location("word_formatter_converter_settings", WORD_FORMATTER_CONVERTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {WORD_FORMATTER_CONVERTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _WORD_FORMATTER_CONVERTER_CACHE = module
    return module


def _word_formatter_defaults() -> dict[str, Any]:
    return _word_formatter_converter().get_default_config()


def _word_formatter_style_keys() -> set[str]:
    defaults = _word_formatter_defaults()
    return set(defaults["styles"].keys())


def _word_formatter_style_fields(style_key: str) -> set[str]:
    defaults = _word_formatter_defaults()
    return set(defaults["styles"][style_key].keys())


def _read_settings(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    if path.exists():
        parser.read(path, encoding="utf-8")
    return parser


def _write_settings(parser: configparser.ConfigParser, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
            temp_path = Path(f.name)
            parser.write(f, space_around_delimiters=False)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
    try:
        temp_path.replace(path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _value(parser: configparser.ConfigParser, section: str, option: str, default: str = "") -> str:
    if parser.has_section(section):
        for candidate in (option, option.replace("/", "\\"), option.replace("\\", "/")):
            if parser.has_option(section, candidate):
                return parser.get(section, candidate).strip().strip('"')
        wanted = _canonical_legacy_option(option)
        for candidate in parser.options(section):
            if _canonical_legacy_option(candidate) == wanted:
                return parser.get(section, candidate).strip().strip('"')
    return default.strip().strip('"')


def _canonical_legacy_option(option: str) -> str:
    return _decode_qt_percent_u(option).replace("\\", "/")


def _decode_qt_percent_u(value: str) -> str:
    return re.sub(r"%U([0-9A-Fa-f]{4})", lambda match: chr(int(match.group(1), 16)), value)


def _csv(value: str) -> list[str]:
    return [item.strip().strip('"') for item in value.split(",") if item.strip().strip('"')]


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_list(key: str, value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SettingsUpdateError(f"{key} must be a list of strings")
    items = [item.strip() for item in value]
    if any(not item or "," in item for item in items):
        raise SettingsUpdateError(f"{key} contains invalid item")
    return items


def _validate_number_setting(key: str, value: Any) -> str:
    if type(value) is bool:
        raise SettingsUpdateError(f"{key} must be a number")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise SettingsUpdateError(f"{key} must be a number")
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            number = float(text)
        except ValueError as exc:
            raise SettingsUpdateError(f"{key} must be a number") from exc
        if not math.isfinite(number):
            raise SettingsUpdateError(f"{key} must be a number")
        return text
    raise SettingsUpdateError(f"{key} must be a number")


def _validate_legacy_bool_setting(key: str, value: Any) -> str:
    if type(value) is bool:
        return "True" if value else "False"
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes"}:
            return "True"
        if text in {"false", "0", "no"}:
            return "False"
    raise SettingsUpdateError(f"{key} must be boolean")


def _validate_wordformatter_update(key: str, value: Any) -> str | None:
    if key == "wordformatter/output_dir":
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value
    if key.startswith("wordformatter/page/"):
        _, _, page_key = key.split("/", 2)
        if page_key not in _word_formatter_defaults()["page"]:
            raise SettingsUpdateError(f"unknown settings key: {key}")
        return _validate_number_setting(key, value)
    if key.startswith("wordformatter/styles/"):
        parts = key.split("/")
        if len(parts) != 4:
            raise SettingsUpdateError(f"unknown settings key: {key}")
        _, _, style_key, field = parts
        if style_key not in _word_formatter_style_keys() or field not in _word_formatter_style_fields(style_key):
            raise SettingsUpdateError(f"unknown settings key: {key}")
        if field == "font":
            if not isinstance(value, str):
                raise SettingsUpdateError(f"{key} must be a string")
            return value
        if field == "bold":
            return _validate_legacy_bool_setting(key, value)
        if field in WORD_FORMATTER_NUMERIC_STYLE_FIELDS:
            return _validate_number_setting(key, value)
    return None


def _validate_video_downloader_update(key: str, value: Any) -> str | None:
    if key in VIDEO_DOWNLOADER_SHARED_STRING_KEYS:
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value
    if not key.startswith("video_downloader/"):
        return None
    parts = key.split("/")
    if len(parts) != 3 or parts[1] not in VIDEO_DOWNLOADER_MODES:
        raise SettingsUpdateError(f"unknown settings key: {key}")
    setting = parts[2]
    if setting in VIDEO_DOWNLOADER_MODE_STRING_KEYS:
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value
    if setting in VIDEO_DOWNLOADER_MODE_BOOL_KEYS:
        if type(value) is not bool:
            raise SettingsUpdateError(f"{key} must be boolean")
        return "1" if value else "0"
    raise SettingsUpdateError(f"unknown settings key: {key}")


def _validate_filesorter_category_update(key: str, value: Any) -> str | None:
    prefix = "filesorter/category_"
    if not key.startswith(prefix):
        return None
    category = key[len(prefix):]
    if category not in FILESORTER_CATEGORIES:
        raise SettingsUpdateError(f"unknown settings key: {key}")
    if type(value) is not bool:
        raise SettingsUpdateError(f"{key} must be boolean")
    return "1" if value else "0"


def _validate_update(key: str, value: Any) -> str:
    wordformatter_value = _validate_wordformatter_update(key, value)
    if wordformatter_value is not None:
        return wordformatter_value
    video_downloader_value = _validate_video_downloader_update(key, value)
    if video_downloader_value is not None:
        return video_downloader_value
    filesorter_category_value = _validate_filesorter_category_update(key, value)
    if filesorter_category_value is not None:
        return filesorter_category_value
    if key == "ui/theme":
        if value not in {"dark", "light"}:
            raise SettingsUpdateError("ui/theme must be dark or light")
        return value
    if key == "ui/custom_theme_enabled":
        if type(value) is not bool:
            raise SettingsUpdateError("ui/custom_theme_enabled must be boolean")
        return "1" if value else "0"
    if key == "ui/background_enabled":
        if type(value) is not bool:
            raise SettingsUpdateError("ui/background_enabled must be boolean")
        return "1" if value else "0"
    if key == "ui/background_image":
        if not isinstance(value, str):
            raise SettingsUpdateError("ui/background_image must be a string")
        return _validate_background_image_path(value)
    if key == "ui/background_opacity":
        opacity = _validate_number_setting(key, value)
        number = float(opacity)
        if number < 0 or number > 100:
            raise SettingsUpdateError("ui/background_opacity must be between 0 and 100")
        return str(int(number))
    if key in {"auth/remember_password", "auth/auto_login"}:
        if type(value) is not bool:
            raise SettingsUpdateError(f"{key} must be boolean")
        return "1" if value else "0"
    if key in {"tools/disabled", "plugins/disabled"}:
        return ",".join(sorted(_validate_list(key, value)))
    if key == "sidebar/order":
        return ",".join(_validate_list(key, value))
    if key in {f"{tool}/output_dir" for tool in TOOL_OUTPUT_DIR_KEYS}:
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value
    if key in TOOL_BEHAVIOR_STRING_DEFAULTS:
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value
    if key in TOOL_BEHAVIOR_BOOL_DEFAULTS:
        if type(value) is not bool:
            raise SettingsUpdateError(f"{key} must be boolean")
        return "1" if value else "0"
    if key.startswith("theme/"):
        parts = key.split("/")
        if len(parts) != 3 or parts[1] not in {"dark", "light"} or parts[2] not in THEME_ZONES:
            raise SettingsUpdateError(f"unknown settings key: {key}")
        if not isinstance(value, str):
            raise SettingsUpdateError(f"{key} must be a string")
        return value.strip()
    raise SettingsUpdateError(f"unknown settings key: {key}")


def _set_legacy_key(parser: configparser.ConfigParser, key: str, value: str) -> None:
    if key.startswith("theme/"):
        _, theme, zone = key.split("/")
        section, option = "theme", f"{theme}\\{zone}"
    else:
        section, option = key.split("/", 1)
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, option, value)


def apply_settings_update(
    updates: dict[str, Any],
    settings_path: Path = DEFAULT_SETTINGS,
    plugins_dir: Path = DEFAULT_PLUGINS_DIR,
) -> dict[str, Any]:
    if not isinstance(updates, dict):
        raise SettingsUpdateError("updates must be an object")
    validated = {key: _validate_update(key, value) for key, value in updates.items()}
    if validated.get("auth/remember_password") == "0":
        validated["auth/auto_login"] = "0"
    elif validated.get("auth/auto_login") == "1":
        validated["auth/remember_password"] = "1"

    parser = _read_settings(settings_path)
    for key, value in validated.items():
        _set_legacy_key(parser, key, value)
    _write_settings(parser, settings_path)
    return build_settings_snapshot(settings_path=settings_path, plugins_dir=plugins_dir)


def _theme_colors(parser: configparser.ConfigParser, theme: str, custom_enabled: bool) -> dict[str, str]:
    colors = dict(DEFAULT_COLORS.get(theme, DEFAULT_COLORS["dark"]))
    if not custom_enabled:
        return colors
    for zone in THEME_ZONES:
        custom = _value(parser, "theme", f"{theme}\\{zone}", "")
        if custom:
            colors[zone] = custom
    return colors


def _custom_theme_colors(parser: configparser.ConfigParser) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for theme in ("dark", "light"):
        colors = dict(DEFAULT_COLORS[theme])
        for zone in THEME_ZONES:
            custom = _value(parser, "theme", f"{theme}\\{zone}", "")
            if custom:
                colors[zone] = custom
        result[theme] = colors
    return result


def _float_or_default(value: str, default: float) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int_range_or_default(value: str, default: int, minimum: int, maximum: int) -> int:
    if not value:
        return default
    try:
        number = int(float(value))
    except ValueError:
        return default
    return max(minimum, min(maximum, number))


def _legacy_bool_or_default(value: str, default: bool) -> bool:
    if not value:
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return default


def _normalize_proxy_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        cleaned = f"http://{cleaned}"
    return cleaned


def _build_proxy_url(host: str, port: str) -> str:
    clean_host = host.strip()
    clean_port = port.strip()
    if not clean_host:
        return ""
    if not clean_port:
        parsed = urlparse(_normalize_proxy_url(clean_host))
        if parsed.port:
            return _normalize_proxy_url(clean_host)
        return ""
    if "://" in clean_host:
        parsed = urlparse(clean_host)
        credentials = ""
        if parsed.username:
            credentials = parsed.username
            if parsed.password:
                credentials += f":{parsed.password}"
            credentials += "@"
        host_only = parsed.hostname or "127.0.0.1"
        return _normalize_proxy_url(f"{parsed.scheme}://{credentials}{host_only}:{clean_port}")
    host_only = clean_host.rsplit("@", 1)[-1].split(":", 1)[0].strip() or "127.0.0.1"
    return _normalize_proxy_url(f"{host_only}:{clean_port}")


def _split_proxy_url(value: str) -> tuple[str, str]:
    cleaned = _normalize_proxy_url(value)
    if not cleaned:
        return "127.0.0.1", ""
    parsed = urlparse(cleaned)
    if parsed.hostname:
        host = parsed.hostname
        if parsed.scheme and (parsed.scheme != "http" or parsed.username or parsed.password):
            credentials = ""
            if parsed.username:
                credentials = parsed.username
                if parsed.password:
                    credentials += f":{parsed.password}"
                credentials += "@"
            host = f"{parsed.scheme}://{credentials}{host}"
        return host, str(parsed.port or "")
    without_scheme = cleaned.split("://", 1)[-1]
    host, _, port = without_scheme.partition(":")
    return host or "127.0.0.1", port


def _video_bool(parser: configparser.ConfigParser, option: str, default: bool) -> bool:
    return _value(parser, "video_downloader", option, "1" if default else "0") == "1"


def _video_mode_settings(parser: configparser.ConfigParser, mode: str) -> dict[str, Any]:
    host = _value(parser, "video_downloader", f"{mode}/proxy_host", "")
    port = _value(parser, "video_downloader", f"{mode}/proxy_port", "")
    legacy_proxy_url = _value(parser, "video_downloader", f"{mode}/proxy_url", "")
    if not host and not port:
        host, port = _split_proxy_url(legacy_proxy_url)
        proxy_url = _normalize_proxy_url(legacy_proxy_url) if port else ""
    else:
        proxy_url = _build_proxy_url(host, port)
    settings = {
        "output_dir": _value(parser, "video_downloader", f"{mode}/output_dir", ""),
        "proxy_host": host or "127.0.0.1",
        "proxy_port": port,
        "proxy_url": proxy_url,
        "overwrite": _video_bool(parser, f"{mode}/overwrite", False),
        "output_subdir_by_title": _video_bool(parser, f"{mode}/output_subdir_by_title", False),
        "concurrent": _value(parser, "video_downloader", f"{mode}/concurrent", "1"),
        "cover_dir": _value(parser, "video_downloader", f"{mode}/cover_dir", ""),
    }
    if mode == "telegram":
        settings.update(
            {
                "recent_limit": _value(parser, "video_downloader", "telegram/recent_limit", "500"),
                "all_messages": _video_bool(parser, "telegram/all_messages", False),
                "date_from": _value(parser, "video_downloader", "telegram/date_from", ""),
                "date_to": _value(parser, "video_downloader", "telegram/date_to", ""),
                "include_videos": _video_bool(parser, "telegram/include_videos", True),
                "include_photos": _video_bool(parser, "telegram/include_photos", False),
            }
        )
    return settings


def _video_downloader_settings(parser: configparser.ConfigParser) -> tuple[dict[str, Any], dict[str, Any]]:
    shared = {
        "api_id": _value(parser, "video_downloader", "api_id", ""),
        "api_hash": _value(parser, "video_downloader", "api_hash", ""),
        "phone": _value(parser, "video_downloader", "phone", ""),
        "phone_code_hash": _value(parser, "video_downloader", "phone_code_hash", ""),
    }
    return _video_mode_settings(parser, "web"), {**shared, **_video_mode_settings(parser, "telegram")}


def _wordformatter_settings(parser: configparser.ConfigParser) -> dict[str, Any]:
    defaults = _word_formatter_defaults()
    page = {
        key: _float_or_default(_value(parser, "wordformatter", f"page/{key}", ""), float(default))
        for key, default in defaults["page"].items()
    }
    styles: dict[str, dict[str, Any]] = {}
    for style_key, default_style in defaults["styles"].items():
        style: dict[str, Any] = {}
        for field, default in default_style.items():
            saved = _value(parser, "wordformatter", f"styles/{style_key}/{field}", "")
            if field == "font":
                style[field] = saved or default
            elif field == "bold":
                style[field] = _legacy_bool_or_default(saved, bool(default))
            else:
                style[field] = _float_or_default(saved, float(default))
        styles[style_key] = style
    return {
        "output_dir": _value(parser, "wordformatter", "output_dir", ""),
        "page": page,
        "styles": styles,
    }


def _filesorter_categories(parser: configparser.ConfigParser) -> dict[str, bool]:
    return {
        category: _value(parser, "filesorter", f"category_{category}", "1") != "0"
        for category in FILESORTER_CATEGORIES
    }


def _plugin_dependencies(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(_non_empty_string(item) for item in value):
        return []
    return value


def _tool_settings(parser: configparser.ConfigParser) -> dict[str, dict[str, Any]]:
    settings: dict[str, dict[str, Any]] = {
        tool: {"output_dir": _value(parser, tool, "output_dir", "")}
        for tool in TOOL_OUTPUT_DIR_KEYS
    }
    web_video_settings, tg_settings = _video_downloader_settings(parser)
    settings["wordformatter"] = _wordformatter_settings(parser)
    settings["webvideodownloader"] = web_video_settings
    settings["tgdownloader"] = tg_settings
    settings["batchrename"] = {
        "input_dir": _value(parser, "batchrename", "input_dir", TOOL_BEHAVIOR_STRING_DEFAULTS["batchrename/input_dir"]),
        "prefix": _value(parser, "batchrename", "prefix", TOOL_BEHAVIOR_STRING_DEFAULTS["batchrename/prefix"]),
        "group_mode": _value(parser, "batchrename", "group_mode", TOOL_BEHAVIOR_STRING_DEFAULTS["batchrename/group_mode"]),
        "sort_mode": _value(parser, "batchrename", "sort_mode", TOOL_BEHAVIOR_STRING_DEFAULTS["batchrename/sort_mode"]),
        "sort_order": _value(parser, "batchrename", "sort_order", TOOL_BEHAVIOR_STRING_DEFAULTS["batchrename/sort_order"]),
    }
    settings["filesorter"] = {
        "input_dir": _value(parser, "filesorter", "input_dir", TOOL_BEHAVIOR_STRING_DEFAULTS["filesorter/input_dir"]),
        "mode": _value(parser, "filesorter", "mode", TOOL_BEHAVIOR_STRING_DEFAULTS["filesorter/mode"]),
        "categories": _filesorter_categories(parser),
    }
    settings["same"] = {
        "input_dir": _value(parser, "same", "input_dir", TOOL_BEHAVIOR_STRING_DEFAULTS["same/input_dir"]),
        "recursive": _value(parser, "same", "recursive", "1" if TOOL_BEHAVIOR_BOOL_DEFAULTS["same/recursive"] else "0") != "0",
    }
    settings["directdownloader"] = {
        **settings["directdownloader"],
        "connections": _value(parser, "directdownloader", "connections", TOOL_BEHAVIOR_STRING_DEFAULTS["directdownloader/connections"]),
        "overwrite": _value(parser, "directdownloader", "overwrite", "1" if TOOL_BEHAVIOR_BOOL_DEFAULTS["directdownloader/overwrite"] else "0") == "1",
        "output_subdir_by_filename": _value(
            parser,
            "directdownloader",
            "output_subdir_by_filename",
            "1" if TOOL_BEHAVIOR_BOOL_DEFAULTS["directdownloader/output_subdir_by_filename"] else "0",
        )
        == "1",
        "proxy_url": _value(parser, "directdownloader", "proxy_url", TOOL_BEHAVIOR_STRING_DEFAULTS["directdownloader/proxy_url"]),
        "referer": _value(parser, "directdownloader", "referer", TOOL_BEHAVIOR_STRING_DEFAULTS["directdownloader/referer"]),
    }
    return settings


def _plugin_items(plugins_dir: Path, disabled_plugins: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for manifest_path in sorted(plugins_dir.glob("*/manifest.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        name = data.get("name")
        if not isinstance(name, str) or not name or not _PLUGIN_NAME_RE.fullmatch(name):
            continue
        if not all(_non_empty_string(data.get(field)) for field in ("version", "description", "author", "entry")):
            continue
        plugin_type = data.get("type", "gui")
        if not isinstance(plugin_type, str) or plugin_type != "gui":
            continue
        raw_sidebar_label = data.get("sidebar_label", "")
        if not isinstance(raw_sidebar_label, str):
            continue
        raw_priority = data.get("priority", 0)
        if raw_priority is None:
            raw_priority = 0
        if type(raw_priority) is bool or not isinstance(raw_priority, int):
            continue
        enabled_by_manifest = data.get("enabled", True)
        if type(enabled_by_manifest) is not bool:
            continue
        ready = name in READY_PLUGIN_NAMES
        sidebar_label = raw_sidebar_label.strip() or name
        items.append(
            {
                "id": f"plugin:{name}",
                "title": sidebar_label,
                "category": "plugin",
                "supported_in_tauri": ready,
                "status": "ready" if ready else "pending",
                "source": "plugin",
                "enabled": enabled_by_manifest and name not in disabled_plugins,
                "manifest_enabled": enabled_by_manifest,
                "plugin_name": name,
                "sidebar_label": sidebar_label,
                "description": data["description"].strip(),
                "version": data["version"].strip(),
                "dependencies": _plugin_dependencies(data.get("dependencies", [])),
                "priority": raw_priority,
            }
        )
    items.sort(key=lambda item: (-item["priority"], item["plugin_name"], item["id"]))
    return items


def _ordered(items: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in items}
    result: list[dict[str, Any]] = []
    used: set[str] = set()
    for item_id in order:
        if item_id in by_id and item_id not in used:
            result.append(by_id[item_id])
            used.add(item_id)
    result.extend(item for item in items if item["id"] not in used)
    return result


def build_settings_snapshot(
    settings_path: Path = DEFAULT_SETTINGS,
    plugins_dir: Path = DEFAULT_PLUGINS_DIR,
) -> dict[str, Any]:
    parser = _read_settings(settings_path)
    theme = _value(parser, "ui", "theme", "dark")
    if theme not in {"dark", "light"}:
        theme = "dark"
    custom_enabled = _value(parser, "ui", "custom_theme_enabled", "0") == "1"
    disabled_tools = set(_csv(_value(parser, "tools", "disabled", "")))
    disabled_plugins = set(_csv(_value(parser, "plugins", "disabled", "")))

    builtins = []
    for item in build_manifest(load_tool_definitions()):
        builtins.append(
            {
                **item,
                "source": "builtin",
                "enabled": item["id"] not in disabled_tools,
            }
        )
    plugins = _plugin_items(plugins_dir, disabled_plugins)
    order = _csv(_value(parser, "sidebar", "order", ""))

    return {
        "settings_path": str(settings_path),
        "ui": {
            "theme": theme,
            "custom_theme_enabled": custom_enabled,
            "background_enabled": _value(parser, "ui", "background_enabled", "0") == "1",
            "background_image": _value(parser, "ui", "background_image", ""),
            "background_opacity": _int_range_or_default(_value(parser, "ui", "background_opacity", ""), 100, 0, 100),
        },
        "auth": {
            "remember_password": _value(parser, "auth", "remember_password", "0") == "1",
            "auto_login": _value(parser, "auth", "auto_login", "0") == "1",
            "last_user": _value(parser, "auth", "last_user", ""),
        },
        "theme": {
            "mode": "custom" if custom_enabled else theme,
            "colors": _theme_colors(parser, theme, custom_enabled),
            "custom_colors": _custom_theme_colors(parser),
        },
        "disabled_tools": sorted(disabled_tools),
        "disabled_plugins": sorted(disabled_plugins),
        "tool_settings": _tool_settings(parser),
        "sidebar_order": order,
        "tools": _ordered(builtins + plugins, order),
    }


if __name__ == "__main__":
    json.dump(build_settings_snapshot(), sys.stdout, ensure_ascii=False, indent=2)
