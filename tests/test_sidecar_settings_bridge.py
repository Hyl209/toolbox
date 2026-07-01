from __future__ import annotations

import json
import subprocess
import sys
import configparser
import importlib.util
from pathlib import Path

import pytest

from sidecar.settings_bridge import SettingsUpdateError, _write_settings, apply_settings_update, build_settings_snapshot


ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "sidecar" / "hyl_sidecar.py"


def load_word_converter_defaults() -> dict[str, object]:
    module_path = ROOT / "modules" / "word-formatter" / "converter.py"
    spec = importlib.util.spec_from_file_location("word_formatter_converter_defaults", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_default_config()


def test_fixture_text_has_no_known_corruption_markers() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    bad_markers = ["?" * 2, "\ubb8f"]

    assert not any(marker in source for marker in bad_markers)


def write_ini(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "[ui]",
                "theme=dark",
                "custom_theme_enabled=1",
                "",
                "[tools]",
                "disabled=base64",
                "",
                "[plugins]",
                "disabled=json_tools",
                "",
                "[sidebar]",
                "order=zipandpng,plugin:json_tools,base64",
                "",
                "[theme]",
                "dark\\accent=#123456",
                "dark\\window_bg=#101820",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "json_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "json_tools",
                "version": "1.0.0",
                "description": "JSON tools",
                "author": "Hyl",
                "sidebar_label": "JSON Tools",
                "entry": "plugin.py:JsonToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_uuid_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "uuid_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "uuid_tools",
                "version": "1.0.0",
                "description": "UUID tools",
                "author": "Hyl",
                "sidebar_label": "UUID Tools",
                "entry": "plugin.py:UuidToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_text_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "text_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "text_tools",
                "version": "1.0.0",
                "description": "Text tools",
                "author": "Hyl",
                "sidebar_label": "文本工具",
                "entry": "plugin.py:TextToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_url_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "url_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "url_tools",
                "version": "1.0.0",
                "description": "URL tools",
                "author": "Hyl",
                "sidebar_label": "URL 工具",
                "entry": "plugin.py:UrlToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_timestamp_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "timestamp_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "timestamp_tools",
                "version": "1.0.0",
                "description": "Timestamp tools",
                "author": "Hyl",
                "sidebar_label": "Timestamp Tools",
                "entry": "plugin.py:TimestampToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_csv_plugin(root: Path) -> None:
    plugin_dir = root / "plugins" / "csv_tools"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "csv_tools",
                "version": "1.0.0",
                "description": "CSV tools",
                "author": "Hyl",
                "sidebar_label": "CSV Tools",
                "entry": "plugin.py:CsvToolsPlugin",
                "type": "gui",
                "enabled": True,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_file_hasher_plugin(root: Path, *, enabled: bool = True) -> None:
    plugin_dir = root / "plugins" / "file_hasher"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "file_hasher",
                "version": "1.0.0",
                "description": "File hash tools",
                "author": "Hyl",
                "sidebar_label": "File Hasher",
                "entry": "plugin.py:FileHasherPlugin",
                "type": "gui",
                "enabled": enabled,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_archive_extractor_plugin(root: Path, *, enabled: bool = True) -> None:
    plugin_dir = root / "plugins" / "archive_extractor"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "archive_extractor",
                "version": "1.0.0",
                "description": "Archive extractor",
                "author": "Hyl",
                "sidebar_label": "Archive Extractor",
                "entry": "plugin.py:ArchiveExtractorPlugin",
                "type": "gui",
                "enabled": enabled,
                "priority": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_priority_plugin(root: Path, name: str, priority: object) -> None:
    plugin_dir = root / "plugins" / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "1.0.0",
                "description": f"{name} plugin",
                "author": "Hyl",
                "sidebar_label": name.replace("_", " ").title(),
                "entry": "plugin.py:Plugin",
                "type": "gui",
                "enabled": True,
                "priority": priority,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_raw_plugin_manifest(root: Path, dirname: str, manifest: dict[str, object]) -> None:
    plugin_dir = root / "plugins" / dirname
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


def test_snapshot_maps_legacy_theme_sidebar_disabled_and_plugins(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    write_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["ui"]["theme"] == "dark"
    assert snapshot["ui"]["custom_theme_enabled"] is True
    assert snapshot["theme"]["colors"]["accent"] == "#123456"
    assert snapshot["theme"]["colors"]["window_bg"] == "#101820"
    assert snapshot["disabled_tools"] == ["base64"]
    assert snapshot["disabled_plugins"] == ["json_tools"]

    ordered_ids = [item["id"] for item in snapshot["tools"][:3]]
    assert ordered_ids == ["zipandpng", "plugin:json_tools", "base64"]
    plugin = snapshot["tools"][1]
    assert plugin["source"] == "plugin"
    assert plugin["enabled"] is False
    assert plugin["manifest_enabled"] is True
    assert plugin["title"] == "JSON Tools"


def test_snapshot_deduplicates_legacy_sidebar_order_ids(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[sidebar]\norder=music,music,base64\n", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    ordered_ids = [item["id"] for item in snapshot["tools"]]
    assert ordered_ids[:2] == ["music", "base64"]
    assert ordered_ids.count("music") == 1


def test_snapshot_maps_legacy_auth_preferences(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[auth]",
                "remember_password=1",
                "auto_login=0",
                "last_user=ligo",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["auth"] == {
        "remember_password": True,
        "auto_login": False,
        "last_user": "ligo",
    }


def test_snapshot_maps_legacy_tool_output_dirs(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[base64]",
                "output_dir=E:\\\\out\\\\base64",
                "[music]",
                "output_dir=E:\\\\out\\\\music",
                "[zipandpng]",
                "output_dir=E:\\\\out\\\\zip",
                "[mp4mp3]",
                "output_dir=E:\\\\out\\\\mp3",
                "[imageconvert]",
                "output_dir=E:\\\\out\\\\images",
                "[pdftools]",
                "output_dir=E:\\\\out\\\\pdf",
                "[directdownloader]",
                "output_dir=E:\\\\out\\\\direct",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert {tool: snapshot["tool_settings"][tool] for tool in ("base64", "music", "zipandpng", "mp4mp3", "imageconvert", "pdftools")} == {
        "base64": {"output_dir": "E:\\\\out\\\\base64"},
        "music": {"output_dir": "E:\\\\out\\\\music"},
        "zipandpng": {"output_dir": "E:\\\\out\\\\zip"},
        "mp4mp3": {"output_dir": "E:\\\\out\\\\mp3"},
        "imageconvert": {"output_dir": "E:\\\\out\\\\images"},
        "pdftools": {"output_dir": "E:\\\\out\\\\pdf"},
    }
    assert snapshot["tool_settings"]["directdownloader"]["output_dir"] == "E:\\\\out\\\\direct"


def test_snapshot_maps_legacy_file_download_behavior_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[batchrename]",
                "input_dir=E:\\\\in\\\\batch",
                "prefix=BR",
                "group_mode=按类型",
                "sort_mode=按大小",
                "sort_order=从大到小",
                "[filesorter]",
                "input_dir=E:\\\\in\\\\sort",
                "mode=按分辨率分类",
                "category_图片=1",
                "category_视频=0",
                "category_音频=1",
                "category_文档=0",
                "category_压缩包=1",
                "category_程序=0",
                "category_其他=1",
                "[same]",
                "input_dir=E:\\\\in\\\\same",
                "recursive=0",
                "[archive_extractor]",
                "output_dir=E:\\\\out\\\\archives",
                "[directdownloader]",
                "output_dir=E:\\\\out\\\\direct",
                "connections=32",
                "overwrite=1",
                "output_subdir_by_filename=1",
                "proxy_url=http://127.0.0.1:7890",
                "referer=https://example.test/",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["batchrename"] == {
        "input_dir": "E:\\\\in\\\\batch",
        "prefix": "BR",
        "group_mode": "按类型",
        "sort_mode": "按大小",
        "sort_order": "从大到小",
    }
    assert snapshot["tool_settings"]["filesorter"] == {
        "input_dir": "E:\\\\in\\\\sort",
        "mode": "按分辨率分类",
        "categories": {
            "图片": True,
            "视频": False,
            "音频": True,
            "文档": False,
            "压缩包": True,
            "程序": False,
            "其他": True,
        },
    }
    assert snapshot["tool_settings"]["archive_extractor"] == {"output_dir": "E:\\\\out\\\\archives"}
    assert snapshot["tool_settings"]["same"] == {
        "input_dir": "E:\\\\in\\\\same",
        "recursive": False,
    }
    assert snapshot["tool_settings"]["directdownloader"] == {
        "output_dir": "E:\\\\out\\\\direct",
        "connections": "32",
        "overwrite": True,
        "output_subdir_by_filename": True,
        "proxy_url": "http://127.0.0.1:7890",
        "referer": "https://example.test/",
    }


def test_snapshot_uses_legacy_file_download_behavior_defaults(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["batchrename"] == {
        "input_dir": "",
        "prefix": "批量命名",
        "group_mode": "按后缀",
        "sort_mode": "按命名",
        "sort_order": "从小到大",
    }
    assert snapshot["tool_settings"]["filesorter"] == {
        "input_dir": "",
        "mode": "按大类分类",
        "categories": {
            "图片": True,
            "视频": True,
            "音频": True,
            "文档": True,
            "压缩包": True,
            "程序": True,
            "其他": True,
        },
    }
    assert snapshot["tool_settings"]["archive_extractor"] == {"output_dir": ""}
    assert snapshot["tool_settings"]["same"] == {"input_dir": "", "recursive": True}
    assert snapshot["tool_settings"]["directdownloader"] == {
        "output_dir": "",
        "connections": "16",
        "overwrite": False,
        "output_subdir_by_filename": False,
        "proxy_url": "",
        "referer": "",
    }


def test_snapshot_maps_legacy_wordformatter_settings_with_converter_defaults(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[wordformatter]",
                "output_dir=E:\\\\out\\\\word",
                "page/top_margin_cm=1.25",
                "styles/heading1/font=SimHei",
                "styles/heading1/bold=False",
                "styles/body/first_line_indent_cm=0.88",
                "",
            ]
        ),
        encoding="utf-8",
    )
    defaults = load_word_converter_defaults()

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    word = snapshot["tool_settings"]["wordformatter"]

    assert word["output_dir"] == "E:\\\\out\\\\word"
    assert word["page"]["top_margin_cm"] == 1.25
    assert word["page"]["bottom_margin_cm"] == defaults["page"]["bottom_margin_cm"]
    assert word["styles"]["heading1"]["font"] == "SimHei"
    assert word["styles"]["heading1"]["bold"] is False
    assert word["styles"]["body"]["first_line_indent_cm"] == 0.88
    assert word["styles"]["table"]["size_pt"] == defaults["styles"]["table"]["size_pt"]


def test_settings_update_writes_legacy_wordformatter_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")

    snapshot = apply_settings_update(
        {
            "wordformatter/output_dir": "E:\\\\word",
            "wordformatter/page/top_margin_cm": 1.2,
            "wordformatter/page/footer_distance_cm": "1.66",
            "wordformatter/styles/heading1/font": "Microsoft YaHei UI",
            "wordformatter/styles/heading1/bold": "yes",
            "wordformatter/styles/body/bold": False,
            "wordformatter/styles/body/line_spacing": "1.8",
        },
        settings_path=settings_path,
        plugins_dir=tmp_path / "plugins",
    )

    word = snapshot["tool_settings"]["wordformatter"]
    assert word["output_dir"] == "E:\\\\word"
    assert word["page"]["top_margin_cm"] == 1.2
    assert word["page"]["footer_distance_cm"] == 1.66
    assert word["styles"]["heading1"]["font"] == "Microsoft YaHei UI"
    assert word["styles"]["heading1"]["bold"] is True
    assert word["styles"]["body"]["bold"] is False
    assert word["styles"]["body"]["line_spacing"] == 1.8

    parser_text = settings_path.read_text(encoding="utf-8")
    assert "output_dir=E:\\\\word" in parser_text
    assert "page/top_margin_cm=1.2" in parser_text
    assert "page/footer_distance_cm=1.66" in parser_text
    assert "styles/heading1/font=Microsoft YaHei UI" in parser_text
    assert "styles/heading1/bold=True" in parser_text
    assert "styles/body/bold=False" in parser_text
    assert "styles/body/line_spacing=1.8" in parser_text


def test_wordformatter_output_dir_preserves_percent_literals_in_snapshot_and_update(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    percent_path = r"C:\%USERPROFILE%\word"
    settings_path.write_text(f"[wordformatter]\noutput_dir={percent_path}\n", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["wordformatter"]["output_dir"] == percent_path

    updated_path = r"D:\100% done\word"
    snapshot = apply_settings_update(
        {"wordformatter/output_dir": updated_path},
        settings_path=settings_path,
        plugins_dir=tmp_path / "plugins",
    )

    assert snapshot["tool_settings"]["wordformatter"]["output_dir"] == updated_path
    assert f"output_dir={updated_path}" in settings_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("wordformatter/page/not_a_page_key", 1, "unknown settings key"),
        ("wordformatter/page/top_margin_cm", "wide", "must be a number"),
        ("wordformatter/styles/heading9/font", "Arial", "unknown settings key"),
        ("wordformatter/styles/body/bold", "maybe", "must be boolean"),
        ("wordformatter/styles/body/line_spacing", True, "must be a number"),
    ],
)
def test_settings_update_rejects_invalid_wordformatter_settings_without_writing(tmp_path: Path, key: str, value: object, message: str) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[wordformatter]\noutput_dir=E:\\\\old\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match=message):
        apply_settings_update({key: value}, settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert settings_path.read_text(encoding="utf-8") == before


def test_settings_update_writes_legacy_tool_output_dirs_and_allows_empty_string(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[base64]\noutput_dir=E:\\\\old\n", encoding="utf-8")

    snapshot = apply_settings_update(
        {
            "base64/output_dir": "E:\\\\new\\\\base64",
            "music/output_dir": "",
            "directdownloader/output_dir": "E:\\\\new\\\\direct",
        },
        settings_path=settings_path,
        plugins_dir=tmp_path / "plugins",
    )

    assert snapshot["tool_settings"]["base64"]["output_dir"] == "E:\\\\new\\\\base64"
    assert snapshot["tool_settings"]["music"]["output_dir"] == ""
    assert snapshot["tool_settings"]["directdownloader"]["output_dir"] == "E:\\\\new\\\\direct"
    parser_text = settings_path.read_text(encoding="utf-8")
    assert "output_dir=E:\\\\new\\\\base64" in parser_text
    assert "[music]" in parser_text
    assert "output_dir=" in parser_text


def test_settings_update_writes_legacy_file_download_behavior_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[same]\nrecursive=1\n", encoding="utf-8")

    snapshot = apply_settings_update(
        {
            "batchrename/input_dir": "E:\\\\batch",
            "batchrename/prefix": "BR",
            "batchrename/group_mode": "按类型",
            "batchrename/sort_mode": "按大小",
            "batchrename/sort_order": "从大到小",
            "filesorter/input_dir": "E:\\\\sort",
            "filesorter/mode": "按分辨率分类",
            "filesorter/category_图片": True,
            "filesorter/category_视频": False,
            "archive_extractor/output_dir": "E:\\\\archives",
            "same/input_dir": "E:\\\\same",
            "same/recursive": False,
            "directdownloader/connections": "24",
            "directdownloader/overwrite": True,
            "directdownloader/output_subdir_by_filename": True,
            "directdownloader/proxy_url": "http://127.0.0.1:7890",
            "directdownloader/referer": "https://example.test/",
        },
        settings_path=settings_path,
        plugins_dir=tmp_path / "plugins",
    )

    assert snapshot["tool_settings"]["same"]["recursive"] is False
    assert snapshot["tool_settings"]["filesorter"]["categories"]["图片"] is True
    assert snapshot["tool_settings"]["filesorter"]["categories"]["视频"] is False
    assert snapshot["tool_settings"]["archive_extractor"]["output_dir"] == "E:\\\\archives"
    assert snapshot["tool_settings"]["directdownloader"]["overwrite"] is True
    assert snapshot["tool_settings"]["directdownloader"]["output_subdir_by_filename"] is True
    parser_text = settings_path.read_text(encoding="utf-8")
    assert "prefix=BR" in parser_text
    assert "mode=按分辨率分类" in parser_text
    assert "category_图片=1" in parser_text
    assert "category_视频=0" in parser_text
    assert "output_dir=E:\\\\archives" in parser_text
    assert "recursive=0" in parser_text
    assert "connections=24" in parser_text
    assert "overwrite=1" in parser_text
    assert "output_subdir_by_filename=1" in parser_text
    assert "proxy_url=http://127.0.0.1:7890" in parser_text
    assert "referer=https://example.test/" in parser_text


def test_settings_update_rejects_unknown_tool_setting_without_writing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[base64]\noutput_dir=E:\\\\old\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match="unknown settings key"):
        apply_settings_update(
            {"base64/other": "E:\\\\bad"},
            settings_path=settings_path,
            plugins_dir=tmp_path / "plugins",
        )

    assert settings_path.read_text(encoding="utf-8") == before


def test_settings_update_rejects_invalid_behavior_type_without_writing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[directdownloader]\noverwrite=0\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match="directdownloader/overwrite must be boolean"):
        apply_settings_update(
            {"directdownloader/overwrite": "1"},
            settings_path=settings_path,
            plugins_dir=tmp_path / "plugins",
        )

    assert settings_path.read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("filesorter/category_未知", True, "unknown settings key"),
        ("filesorter/category_图片", "1", "must be boolean"),
        ("archive_extractor/output_dir", False, "must be a string"),
    ],
)
def test_settings_update_rejects_invalid_filesorter_archive_settings_without_writing(tmp_path: Path, key: str, value: object, message: str) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[filesorter]\ncategory_图片=1\n[archive_extractor]\noutput_dir=E:\\\\old\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match=message):
        apply_settings_update({key: value}, settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert settings_path.read_text(encoding="utf-8") == before


def test_settings_update_rejects_non_string_behavior_value_without_writing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[batchrename]\ninput_dir=E:\\\\old\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match="batchrename/input_dir must be a string"):
        apply_settings_update(
            {"batchrename/input_dir": True},
            settings_path=settings_path,
            plugins_dir=tmp_path / "plugins",
        )

    assert settings_path.read_text(encoding="utf-8") == before


def test_snapshot_preserves_custom_theme_drafts_when_custom_theme_disabled(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[ui]",
                "theme=dark",
                "custom_theme_enabled=0",
                "",
                "[theme]",
                "dark\\accent=#123456",
                "light\\accent=#abcdef",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["theme"]["colors"]["accent"] == "#6f95c7"
    assert snapshot["theme"]["custom_colors"]["dark"]["accent"] == "#123456"
    assert snapshot["theme"]["custom_colors"]["light"]["accent"] == "#abcdef"


def test_snapshot_uses_legacy_light_accent_when_custom_theme_disabled(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[ui]",
                "theme=light",
                "custom_theme_enabled=0",
                "",
                "[theme]",
                "light\\accent=#abcdef",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["theme"]["colors"]["accent"] == "#e4efff"
    assert snapshot["theme"]["custom_colors"]["light"]["accent"] == "#abcdef"


def test_snapshot_marks_json_and_uuid_plugins_ready_but_respects_disabled_state(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    write_plugin(tmp_path)
    write_uuid_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugins = {item["id"]: item for item in snapshot["tools"] if item["source"] == "plugin"}

    assert plugins["plugin:json_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:json_tools"]["status"] == "ready"
    assert plugins["plugin:json_tools"]["enabled"] is False
    assert plugins["plugin:uuid_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:uuid_tools"]["status"] == "ready"
    assert plugins["plugin:uuid_tools"]["enabled"] is True


def test_snapshot_ready_plugin_still_respects_manifest_disabled(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=\n", encoding="utf-8")
    write_uuid_plugin(tmp_path)
    manifest_path = tmp_path / "plugins" / "uuid_tools" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["enabled"] = False
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    uuid_plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:uuid_tools")

    assert uuid_plugin["supported_in_tauri"] is True
    assert uuid_plugin["status"] == "ready"
    assert uuid_plugin["enabled"] is False
    assert uuid_plugin["manifest_enabled"] is False


def test_snapshot_marks_text_and_url_plugins_ready_but_respects_disabled_state(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=url_tools\n", encoding="utf-8")
    write_text_plugin(tmp_path)
    write_url_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugins = {item["id"]: item for item in snapshot["tools"] if item["source"] == "plugin"}

    assert plugins["plugin:text_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:text_tools"]["status"] == "ready"
    assert plugins["plugin:text_tools"]["enabled"] is True
    assert plugins["plugin:url_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:url_tools"]["status"] == "ready"
    assert plugins["plugin:url_tools"]["enabled"] is False


def test_snapshot_marks_timestamp_and_csv_plugins_ready_but_respects_disabled_state(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=csv_tools\n", encoding="utf-8")
    write_timestamp_plugin(tmp_path)
    write_csv_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugins = {item["id"]: item for item in snapshot["tools"] if item["source"] == "plugin"}

    assert plugins["plugin:timestamp_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:timestamp_tools"]["status"] == "ready"
    assert plugins["plugin:timestamp_tools"]["enabled"] is True
    assert plugins["plugin:csv_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:csv_tools"]["status"] == "ready"
    assert plugins["plugin:csv_tools"]["enabled"] is False


def test_snapshot_ready_timestamp_and_csv_plugins_still_respect_manifest_disabled(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=\n", encoding="utf-8")
    write_timestamp_plugin(tmp_path)
    write_csv_plugin(tmp_path)
    for name in ("timestamp_tools", "csv_tools"):
        manifest_path = tmp_path / "plugins" / name / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["enabled"] = False
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugins = {item["id"]: item for item in snapshot["tools"] if item["source"] == "plugin"}

    assert plugins["plugin:timestamp_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:timestamp_tools"]["status"] == "ready"
    assert plugins["plugin:timestamp_tools"]["enabled"] is False
    assert plugins["plugin:csv_tools"]["supported_in_tauri"] is True
    assert plugins["plugin:csv_tools"]["status"] == "ready"
    assert plugins["plugin:csv_tools"]["enabled"] is False


def test_snapshot_marks_file_hasher_ready_but_respects_disabled_sources(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=file_hasher\n", encoding="utf-8")
    write_file_hasher_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:file_hasher")

    assert plugin["supported_in_tauri"] is True
    assert plugin["status"] == "ready"
    assert plugin["enabled"] is False


def test_snapshot_marks_archive_extractor_ready_but_respects_disabled_sources(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=archive_extractor\n", encoding="utf-8")
    write_archive_extractor_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:archive_extractor")

    assert plugin["supported_in_tauri"] is True
    assert plugin["status"] == "ready"
    assert plugin["enabled"] is False

    settings_path.write_text("[plugins]\ndisabled=\n", encoding="utf-8")
    write_archive_extractor_plugin(tmp_path, enabled=False)
    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:archive_extractor")

    assert plugin["supported_in_tauri"] is True
    assert plugin["status"] == "ready"
    assert plugin["enabled"] is False

    settings_path.write_text("[plugins]\ndisabled=\n", encoding="utf-8")
    write_file_hasher_plugin(tmp_path, enabled=False)
    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:file_hasher")

    assert plugin["supported_in_tauri"] is True
    assert plugin["status"] == "ready"
    assert plugin["enabled"] is False


def test_sidecar_settings_snapshot_cli_emits_result_json_line(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    write_plugin(tmp_path)

    proc = subprocess.run(
        [
            sys.executable,
            str(SIDECAR),
            "settings",
            "--snapshot",
            "--settings",
            str(settings_path),
            "--plugins-dir",
            str(tmp_path / "plugins"),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
    events = [json.loads(line) for line in proc.stdout.splitlines() if line]
    assert len(events) == 1
    assert events[0]["type"] == "result"
    assert events[0]["data"]["ui"]["theme"] == "dark"


def test_sidecar_settings_update_cli_writes_legacy_keys_and_snapshot_reflects_them(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    write_plugin(tmp_path)
    input_path = tmp_path / "task.json"
    input_path.write_text(
        json.dumps(
            {
                "task_id": "settings-update-001",
                "updates": {
                    "ui/theme": "light",
                    "ui/custom_theme_enabled": False,
                    "tools/disabled": ["music", "base64"],
                    "plugins/disabled": ["json_tools", "hello_world"],
                    "sidebar/order": ["music", "plugin:json_tools", "base64"],
                    "theme/light/accent": "#abcdef",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(SIDECAR),
            "settings",
            "--update",
            "--input",
            str(input_path),
            "--settings",
            str(settings_path),
            "--plugins-dir",
            str(tmp_path / "plugins"),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
    events = [json.loads(line) for line in proc.stdout.splitlines() if line]
    assert len(events) == 1
    assert events[0]["type"] == "result"
    snapshot = events[0]["data"]
    assert snapshot["ui"] == {"theme": "light", "custom_theme_enabled": False}
    assert snapshot["disabled_tools"] == ["base64", "music"]
    assert snapshot["disabled_plugins"] == ["hello_world", "json_tools"]
    assert snapshot["sidebar_order"] == ["music", "plugin:json_tools", "base64"]

    parser_text = settings_path.read_text(encoding="utf-8")
    assert "theme=light" in parser_text
    assert "custom_theme_enabled=0" in parser_text
    assert "disabled=base64,music" in parser_text
    assert "order=music,plugin:json_tools,base64" in parser_text
    assert "light\\accent=#abcdef" in parser_text


def test_apply_settings_update_auto_login_true_also_writes_remember_password(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[auth]\nremember_password=0\nauto_login=0\n", encoding="utf-8")

    apply_settings_update({"auth/auto_login": True}, settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding="utf-8")
    assert parser.get("auth", "auto_login") == "1"
    assert parser.get("auth", "remember_password") == "1"


def test_apply_settings_update_remember_password_false_also_writes_auto_login_false(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[auth]\nremember_password=1\nauto_login=1\n", encoding="utf-8")

    apply_settings_update({"auth/remember_password": False}, settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding="utf-8")
    assert parser.get("auth", "remember_password") == "0"
    assert parser.get("auth", "auto_login") == "0"


def test_sidecar_settings_update_cli_can_update_sidebar_order_only(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    write_plugin(tmp_path)
    input_path = tmp_path / "task.json"
    input_path.write_text(
        json.dumps(
            {
                "task_id": "settings-sidebar-order-001",
                "updates": {
                    "sidebar/order": ["plugin:json_tools", "zipandpng", "base64"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(SIDECAR),
            "settings",
            "--update",
            "--input",
            str(input_path),
            "--settings",
            str(settings_path),
            "--plugins-dir",
            str(tmp_path / "plugins"),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    events = [json.loads(line) for line in proc.stdout.splitlines() if line]
    snapshot = events[0]["data"]
    assert snapshot["sidebar_order"] == ["plugin:json_tools", "zipandpng", "base64"]
    assert [item["id"] for item in snapshot["tools"][:3]] == ["plugin:json_tools", "zipandpng", "base64"]
    assert snapshot["disabled_tools"] == ["base64"]
    assert snapshot["disabled_plugins"] == ["json_tools"]
    assert "order=plugin:json_tools,zipandpng,base64" in settings_path.read_text(encoding="utf-8")


def test_sidecar_settings_update_cli_rejects_unknown_key_without_writing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    input_path = tmp_path / "task.json"
    input_path.write_text(
        json.dumps({"updates": {"auth/unknown": True}}, ensure_ascii=False),
        encoding="utf-8",
    )
    before = settings_path.read_text(encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SIDECAR),
            "settings",
            "--update",
            "--input",
            str(input_path),
            "--settings",
            str(settings_path),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    events = [json.loads(line) for line in proc.stdout.splitlines() if line]
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "INVALID_SETTINGS_UPDATE"
    assert settings_path.read_text(encoding="utf-8") == before


def test_sidecar_settings_update_cli_rejects_invalid_type_without_writing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    write_ini(settings_path)
    input_path = tmp_path / "task.json"
    input_path.write_text(
        json.dumps({"updates": {"tools/disabled": "base64"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    before = settings_path.read_text(encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SIDECAR),
            "settings",
            "--update",
            "--input",
            str(input_path),
            "--settings",
            str(settings_path),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    events = [json.loads(line) for line in proc.stdout.splitlines() if line]
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "INVALID_SETTINGS_UPDATE"
    assert settings_path.read_text(encoding="utf-8") == before


def test_write_settings_keeps_original_when_write_fails(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[ui]\ntheme=dark\n", encoding="utf-8")
    parser = configparser.ConfigParser()

    def fail_after_partial_write(file, **_kwargs):
        file.write("[ui]\n")
        raise RuntimeError("simulated partial write")

    parser.write = fail_after_partial_write

    with pytest.raises(RuntimeError, match="simulated partial write"):
        _write_settings(parser, settings_path)

    assert settings_path.read_text(encoding="utf-8") == "[ui]\ntheme=dark\n"




def test_snapshot_reads_qsettings_escaped_legacy_keys(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[ui]",
                "custom_theme_enabled=1",
                "",
                "[theme]",
                "dark\\accent=#abcdef",
                "",
                "[video_downloader]",
                "web\\output_dir=E:/legacy-web",
                "telegram\\all_messages=1",
                "",
                "[filesorter]",
                "category_%U97F3%U9891=0",
                "",
                "[wordformatter]",
                "page\\top_margin_cm=9",
                "styles\\body\\font=Arial",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["webvideodownloader"]["output_dir"] == "E:/legacy-web"
    assert snapshot["tool_settings"]["tgdownloader"]["all_messages"] is True
    assert snapshot["tool_settings"]["filesorter"]["categories"]["\u97f3\u9891"] is False
    assert snapshot["tool_settings"]["wordformatter"]["page"]["top_margin_cm"] == 9.0
    assert snapshot["tool_settings"]["wordformatter"]["styles"]["body"]["font"] == "Arial"
    assert snapshot["theme"]["custom_colors"]["dark"]["accent"] == "#abcdef"

def test_snapshot_maps_legacy_video_downloader_web_and_tg_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text(
        "\n".join(
            [
                "[video_downloader]",
                "api_id=12345",
                "api_hash=hash-value",
                "phone=+15550001111",
                "phone_code_hash=code-hash",
                "web/output_dir=E:\\\\web-out",
                "web/proxy_host=socks5://user:pass@10.0.0.2",
                "web/proxy_port=1080",
                "web/overwrite=1",
                "web/output_subdir_by_title=1",
                "web/concurrent=0",
                "web/cover_dir=E:\\\\covers",
                "web/proxy_url=http://stale.example:8080",
                "telegram/output_dir=E:\\\\tg-out",
                "telegram/proxy_url=http://127.0.0.1:7890",
                "telegram/recent_limit=250",
                "telegram/all_messages=1",
                "telegram/date_from=2026-06-01",
                "telegram/date_to=2026-06-30",
                "telegram/include_videos=0",
                "telegram/include_photos=1",
                "telegram/overwrite=1",
                "telegram/output_subdir_by_title=1",
                "telegram/concurrent=5",
                "telegram/cover_dir=E:\\\\tg-covers",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["webvideodownloader"] == {
        "output_dir": "E:\\\\web-out",
        "proxy_host": "socks5://user:pass@10.0.0.2",
        "proxy_port": "1080",
        "proxy_url": "socks5://user:pass@10.0.0.2:1080",
        "overwrite": True,
        "output_subdir_by_title": True,
        "concurrent": "0",
        "cover_dir": "E:\\\\covers",
    }
    assert snapshot["tool_settings"]["tgdownloader"] == {
        "api_id": "12345",
        "api_hash": "hash-value",
        "phone": "+15550001111",
        "phone_code_hash": "code-hash",
        "output_dir": "E:\\\\tg-out",
        "proxy_host": "127.0.0.1",
        "proxy_port": "7890",
        "proxy_url": "http://127.0.0.1:7890",
        "recent_limit": "250",
        "all_messages": True,
        "date_from": "2026-06-01",
        "date_to": "2026-06-30",
        "include_videos": False,
        "include_photos": True,
        "overwrite": True,
        "output_subdir_by_title": True,
        "concurrent": "5",
        "cover_dir": "E:\\\\tg-covers",
    }


def test_snapshot_uses_video_downloader_defaults_and_proxy_url_fallback(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[video_downloader]\nweb/proxy_url=127.0.0.1:8888\n", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_host"] == "127.0.0.1"
    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_port"] == "8888"
    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_url"] == "http://127.0.0.1:8888"
    assert snapshot["tool_settings"]["tgdownloader"]["recent_limit"] == "500"
    assert snapshot["tool_settings"]["tgdownloader"]["include_videos"] is True
    assert snapshot["tool_settings"]["tgdownloader"]["include_photos"] is False
    assert snapshot["tool_settings"]["tgdownloader"]["proxy_host"] == "127.0.0.1"
    assert snapshot["tool_settings"]["tgdownloader"]["proxy_port"] == ""
    assert snapshot["tool_settings"]["tgdownloader"]["proxy_url"] == ""


def test_video_downloader_proxy_host_default_without_port_does_not_enable_proxy(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[video_downloader]\nweb/proxy_host=127.0.0.1\nweb/proxy_port=\n", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_host"] == "127.0.0.1"
    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_port"] == ""
    assert snapshot["tool_settings"]["webvideodownloader"]["proxy_url"] == ""


def test_settings_update_writes_legacy_video_downloader_keys(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")

    snapshot = apply_settings_update(
        {
            "video_downloader/api_id": "12345",
            "video_downloader/api_hash": "hash-value",
            "video_downloader/phone": "+15550001111",
            "video_downloader/phone_code_hash": "code-hash",
            "video_downloader/web/output_dir": "E:\\\\web-out",
            "video_downloader/web/proxy_host": "127.0.0.1",
            "video_downloader/web/proxy_port": "7890",
            "video_downloader/web/proxy_url": "http://legacy.proxy:8080",
            "video_downloader/web/overwrite": True,
            "video_downloader/web/output_subdir_by_title": False,
            "video_downloader/web/concurrent": "0",
            "video_downloader/web/cover_dir": "E:\\\\covers",
            "video_downloader/telegram/output_dir": "E:\\\\tg-out",
            "video_downloader/telegram/recent_limit": "500",
            "video_downloader/telegram/all_messages": True,
            "video_downloader/telegram/date_from": "2026-06-01",
            "video_downloader/telegram/date_to": "2026-06-30",
            "video_downloader/telegram/include_videos": False,
            "video_downloader/telegram/include_photos": True,
            "video_downloader/telegram/overwrite": True,
            "video_downloader/telegram/output_subdir_by_title": True,
            "video_downloader/telegram/concurrent": "3",
            "video_downloader/telegram/cover_dir": "E:\\\\tg-covers",
        },
        settings_path=settings_path,
        plugins_dir=tmp_path / "plugins",
    )

    assert snapshot["tool_settings"]["webvideodownloader"]["overwrite"] is True
    assert snapshot["tool_settings"]["tgdownloader"]["include_videos"] is False
    parser_text = settings_path.read_text(encoding="utf-8")
    assert "api_id=12345" in parser_text
    assert "web/output_dir=E:\\\\web-out" in parser_text
    assert "web/proxy_host=127.0.0.1" in parser_text
    assert "web/proxy_port=7890" in parser_text
    assert "web/proxy_url=http://legacy.proxy:8080" in parser_text
    assert "web/overwrite=1" in parser_text
    assert "web/output_subdir_by_title=0" in parser_text
    assert "telegram/all_messages=1" in parser_text
    assert "telegram/include_videos=0" in parser_text
    assert "telegram/include_photos=1" in parser_text
    assert "telegram/concurrent=3" in parser_text


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("video_downloader/web/overwrite", "1", "must be boolean"),
        ("video_downloader/telegram/include_photos", 1, "must be boolean"),
        ("video_downloader/web/not_a_key", "x", "unknown settings key"),
        ("video_downloader/api_id", 12345, "must be a string"),
    ],
)
def test_settings_update_rejects_invalid_video_downloader_settings_without_writing(tmp_path: Path, key: str, value: object, message: str) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[video_downloader]\nweb/output_dir=E:\\\\old\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(SettingsUpdateError, match=message):
        apply_settings_update({key: value}, settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    assert settings_path.read_text(encoding="utf-8") == before



def test_snapshot_builtin_tools_keep_manifest_metadata(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    tools = {item["id"]: item for item in snapshot["tools"]}

    from sidecar.tool_manifest import load_tool_definitions

    definitions = {item["id"]: item for item in load_tool_definitions()}
    word = tools["wordformatter"]
    assert word["source"] == "builtin"
    assert word["sidebar_label"] == definitions["wordformatter"]["sidebar_label"]
    assert word["dir_name"] == "modules/word-formatter"
    assert word["converter_file"] == "converter.py"
    assert word["tab_file"] == "tab.py"
    assert word["extra_files"] == []
    assert word["tab_kwargs"] == {}

    web = tools["webvideodownloader"]
    assert web["tab_kwargs"] == {"source_mode": "web"}


def test_snapshot_plugin_tools_keep_manifest_metadata(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[plugins]\ndisabled=json_tools\n", encoding="utf-8")
    write_plugin(tmp_path)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")
    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:json_tools")

    assert plugin["source"] == "plugin"
    assert plugin["title"] == "JSON Tools"
    assert plugin["sidebar_label"] == "JSON Tools"
    assert plugin["description"] == "JSON tools"
    assert plugin["version"] == "1.0.0"
    assert plugin["priority"] == 0
    assert plugin["plugin_name"] == "json_tools"
    assert plugin["manifest_enabled"] is True
    assert plugin["enabled"] is False


def test_snapshot_default_plugin_order_uses_priority_desc_then_stable_name(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "low_priority", 1)
    write_priority_plugin(tmp_path, "z_high_priority", 9)
    write_priority_plugin(tmp_path, "a_high_priority", 9)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert plugin_ids == ["plugin:a_high_priority", "plugin:z_high_priority", "plugin:low_priority"]


def test_snapshot_maps_plugin_manifest_null_priority_to_default_zero(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "null_priority", None)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin = next(item for item in snapshot["tools"] if item["id"] == "plugin:null_priority")
    assert plugin["priority"] == 0


def test_snapshot_skips_plugin_manifest_with_invalid_priority_without_crashing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "valid_plugin", 3)
    write_priority_plugin(tmp_path, "bad_priority", "high")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert "plugin:bad_priority" not in plugin_ids


@pytest.mark.parametrize("bad_name", ["bad,name", "bad name", "bad-name"])
def test_snapshot_skips_plugin_manifest_with_invalid_name_without_crashing(tmp_path: Path, bad_name: str) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "valid_plugin", 3)
    write_raw_plugin_manifest(
        tmp_path,
        "bad_name",
        {
            "name": bad_name,
            "version": "1.0.0",
            "description": "Bad plugin",
            "author": "Hyl",
            "sidebar_label": "Bad Plugin",
            "entry": "plugin.py:Plugin",
            "type": "gui",
            "enabled": True,
            "priority": 0,
        },
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert f"plugin:{bad_name}" not in plugin_ids


def test_snapshot_skips_plugin_manifest_with_non_bool_enabled_without_crashing(tmp_path: Path) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "valid_plugin", 3)
    write_raw_plugin_manifest(
        tmp_path,
        "bad_enabled",
        {
            "name": "bad_enabled",
            "version": "1.0.0",
            "description": "Bad plugin",
            "author": "Hyl",
            "sidebar_label": "Bad Plugin",
            "entry": "plugin.py:Plugin",
            "type": "gui",
            "enabled": "false",
            "priority": 0,
        },
    )

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert "plugin:bad_enabled" not in plugin_ids


@pytest.mark.parametrize(
    ("dirname", "manifest"),
    [
        ("missing_version", {"name": "missing_version", "description": "Bad plugin", "author": "Hyl", "entry": "plugin.py:Plugin", "type": "gui", "enabled": True, "priority": 0}),
        ("blank_description", {"name": "blank_description", "version": "1.0.0", "description": " ", "author": "Hyl", "entry": "plugin.py:Plugin", "type": "gui", "enabled": True, "priority": 0}),
        ("missing_author", {"name": "missing_author", "version": "1.0.0", "description": "Bad plugin", "entry": "plugin.py:Plugin", "type": "gui", "enabled": True, "priority": 0}),
        ("blank_entry", {"name": "blank_entry", "version": "1.0.0", "description": "Bad plugin", "author": "Hyl", "entry": "", "type": "gui", "enabled": True, "priority": 0}),
        ("bad_sidebar", {"name": "bad_sidebar", "version": "1.0.0", "description": "Bad plugin", "author": "Hyl", "entry": "plugin.py:Plugin", "sidebar_label": 123, "type": "gui", "enabled": True, "priority": 0}),
    ],
)
def test_snapshot_skips_plugin_manifest_without_legacy_required_metadata(
    tmp_path: Path, dirname: str, manifest: dict[str, object]
) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_raw_plugin_manifest(
        tmp_path,
        "valid_plugin",
        {
            "name": "valid_plugin",
            "version": "1.0.0",
            "description": "Valid plugin",
            "author": "Hyl",
            "entry": "plugin.py:Plugin",
            "type": "gui",
            "enabled": True,
            "priority": 0,
        },
    )
    write_raw_plugin_manifest(tmp_path, dirname, manifest)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert f"plugin:{dirname}" not in plugin_ids


@pytest.mark.parametrize("invalid_manifest", [[], None])
def test_snapshot_skips_non_object_plugin_manifest_without_crashing(tmp_path: Path, invalid_manifest: object) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "valid_plugin", 3)
    plugin_dir = tmp_path / "plugins" / "bad_manifest"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(json.dumps(invalid_manifest), encoding="utf-8")

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert "plugin:bad_manifest" not in plugin_ids


@pytest.mark.parametrize("bool_priority", [True, False])
def test_snapshot_skips_plugin_manifest_with_bool_priority_without_crashing(
    tmp_path: Path, bool_priority: bool
) -> None:
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("", encoding="utf-8")
    write_priority_plugin(tmp_path, "valid_plugin", 3)
    write_priority_plugin(tmp_path, "bool_priority", bool_priority)

    snapshot = build_settings_snapshot(settings_path=settings_path, plugins_dir=tmp_path / "plugins")

    plugin_ids = [item["id"] for item in snapshot["tools"] if item["source"] == "plugin"]
    assert "plugin:valid_plugin" in plugin_ids
    assert "plugin:bool_priority" not in plugin_ids
