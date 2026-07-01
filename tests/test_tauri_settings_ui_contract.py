from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "desktop-tauri" / "src" / "App.tsx"
BATCH_RENAME_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "BatchRenameTool.tsx"
DIRECT_DOWNLOADER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "DirectDownloaderTool.tsx"
FILE_SORTER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "FileSorterTool.tsx"
ARCHIVE_EXTRACTOR_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "ArchiveExtractorPluginTool.tsx"
WORD_FORMATTER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "WordFormatterTool.tsx"
TAURI_TS = ROOT / "desktop-tauri" / "src" / "api" / "tauri.ts"
README_MD = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
TAURI_SIDECAR_RS = ROOT / "desktop-tauri" / "src-tauri" / "src" / "sidecar.rs"


def _extract_function_body(source: str, function_name: str) -> str:
    signature_start = source.index(f"function {function_name}")
    body_start = source.index("{", signature_start)
    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start + 1 : index]
    raise AssertionError(f"{function_name} body not found")


def _run_sidebar_order_for_save(
    source: str,
    snapshot_order: list[str],
    visible_order: list[str],
    current_tool_ids: list[str],
) -> list[str]:
    body = _extract_function_body(source, "sidebarOrderForSave")
    script = f"""
const snapshot = {{ sidebar_order: {json.dumps(snapshot_order)} }};
const visibleOrder = {json.dumps(visible_order)};
const toolsById = new Map({json.dumps([[tool_id, {}] for tool_id in current_tool_ids])});
function sidebarOrderForSave(snapshot, visibleOrder, toolsById) {{
{body}
}}
process.stdout.write(JSON.stringify(sidebarOrderForSave(snapshot, visibleOrder, toolsById)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_batchrename_group_mode_uses_legacy_all_files_label() -> None:
    app_source = APP_TSX.read_text(encoding="utf-8")
    batch_source = BATCH_RENAME_TSX.read_text(encoding="utf-8")
    legacy_label = "\u5168\u6587\u4ef6"
    rejected_label = "\u5168\u90e8\u6587\u4ef6"

    assert '"\\u5168\\u6587\\u4ef6": "all"' in batch_source
    assert f'{{ value: "all", label: "{legacy_label}" }}' in batch_source
    assert '<option value="\\u5168\\u6587\\u4ef6">{"\\u5168\\u6587\\u4ef6"}</option>' in app_source
    for source in (app_source, batch_source):
        assert rejected_label not in source
        assert "\\u5168\\u90e8\\u6587\\u4ef6" not in source


def test_tauri_settings_save_does_not_force_disable_custom_theme() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert '"ui/custom_theme_enabled": false' not in source
    assert '"ui/custom_theme_enabled": customThemeDraft' in source


def test_tauri_settings_save_writes_current_theme_zone_values() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "THEME_ZONES" in source
    assert "`theme/${themeDraft}/${zone}`" in source
    assert "themeColorsDraft[themeDraft]?.[zone]" in source


def test_tauri_settings_drafts_prefer_snapshot_custom_colors() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "snapshot.theme.custom_colors" in source
    assert "customColors[theme]" in source
    assert "snapshot.theme.colors" in source


def test_tauri_settings_snapshot_type_and_browser_fallback_include_custom_colors() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")

    assert "custom_colors" in source
    assert "custom_colors: {" in source
    assert "browserCustomThemeColors" in source


def test_tauri_debug_sidecar_can_run_without_codex_test_venv() -> None:
    source = TAURI_SIDECAR_RS.read_text(encoding="utf-8")

    assert "HYL_SIDECAR_PYTHON" in source
    assert '.join(".venv")' in source
    assert 'PathBuf::from("python")' in source
    assert 'PathBuf::from("py")' in source


def test_readme_uses_repo_relative_tauri_commands() -> None:
    source = README_MD.read_text(encoding="utf-8")

    assert "E:\\hyl tools" not in source
    assert ".\\start-new-ui.bat" in source
    assert 'cd "desktop-tauri"' in source


def test_gitignore_excludes_codex_review_and_test_artifacts() -> None:
    source = GITIGNORE.read_text(encoding="utf-8")

    for pattern in (
        ".codex-pytest-tmp*/",
        ".codex-plugin-*/",
        ".codex-*-smoke*/",
        ".codex-*-settings*/",
        ".codex-review-tmp*/",
        ".codex-*.json",
        ".codex-*.ini",
        "*.log.*",
        "desktop-tauri/test-results/",
    ):
        assert pattern in source


def test_tauri_settings_ui_writes_legacy_plugin_disabled_key() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "disabledPluginDraft" in source
    assert '"plugins/disabled":' in source
    assert "setPluginEnabled" in source
    assert "\\u63d2\\u4ef6\\u542f\\u505c\\u4fdd\\u6301\\u53ea\\u8bfb" not in source


def test_tauri_settings_patch_and_browser_fallback_keep_plugin_disabled_key() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")

    assert '"plugins/disabled"?: string[]' in source
    assert 'patch.updates["plugins/disabled"]' in source
    assert "disabled_plugins: [...disabledPluginSet].sort()" in source


def test_tauri_settings_ui_has_auth_drafts_and_save_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "rememberPasswordDraft" in source
    assert "autoLoginDraft" in source
    assert '"auth/remember_password": rememberPasswordDraft' in source
    assert '"auth/auto_login": autoLoginDraft' in source


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_auth() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")

    assert "auth: {" in source
    assert "remember_password: boolean" in source
    assert "auto_login: boolean" in source
    assert "last_user: string" in source
    assert '"auth/remember_password"?: boolean' in source
    assert '"auth/auto_login"?: boolean' in source
    assert 'patch.updates["auth/remember_password"]' in source
    assert 'patch.updates["auth/auto_login"]' in source


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_tool_settings() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")
    keys = [
        "base64/output_dir",
        "music/output_dir",
        "zipandpng/output_dir",
        "mp4mp3/output_dir",
        "imageconvert/output_dir",
        "pdftools/output_dir",
        "directdownloader/output_dir",
    ]

    assert "tool_settings:" in source
    for key in keys:
        assert f'"{key}"?: string' in source
        assert f'patch.updates["{key}"]' in source


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_file_download_behavior_settings() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")
    string_keys = [
        "batchrename/input_dir",
        "batchrename/prefix",
        "batchrename/group_mode",
        "batchrename/sort_mode",
        "batchrename/sort_order",
        "filesorter/input_dir",
        "filesorter/mode",
        "same/input_dir",
        "directdownloader/connections",
        "directdownloader/proxy_url",
        "directdownloader/referer",
    ]
    boolean_keys = [
        "same/recursive",
        "directdownloader/overwrite",
        "directdownloader/output_subdir_by_filename",
    ]

    assert "prefix?: string" in source
    assert "recursive?: boolean" in source
    assert "output_subdir_by_filename?: boolean" in source
    for key in string_keys:
        assert f'"{key}"?: string' in source
        assert f'patchString(patch.updates, "{key}"' in source
    for key in boolean_keys:
        assert f'"{key}"?: boolean' in source
        assert f'"{key}"' in source
    assert "patchBoolean(patch.updates" in source


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_filesorter_categories_and_archive_output() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")

    assert "categories?: Record<string, boolean>" in source
    assert "[key: `filesorter/category_${string}`]: boolean | undefined" in source
    assert '"archive_extractor/output_dir"?: string' in source
    assert "FILESORTER_CATEGORIES" in source
    assert "patchFilesorterCategories(patch.updates" in source
    assert 'patchString(patch.updates, "archive_extractor/output_dir"' in source
    for category in ("图片", "视频", "音频", "文档", "压缩包", "程序", "其他"):
        assert "filesorter/category_${category}" in source
        assert category in source


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_wordformatter_settings() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")
    required = [
        "wordformatter/output_dir",
        "wordformatter/page/top_margin_cm",
        "wordformatter/page/footer_distance_cm",
        "wordformatter/styles/heading1/font",
        "wordformatter/styles/heading1/bold",
        "wordformatter/styles/body/line_spacing",
        "browserWordFormatterSettings",
        "patchWordFormatterSettings",
    ]

    for marker in required:
        assert marker in source
    assert "page?: Record<string, number | string>" in source
    assert "styles?: Record<string, WordFormatterStyleSettings>" in source


def test_tauri_settings_panel_has_tool_output_dir_card_and_save_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")
    keys = [
        "base64/output_dir",
        "music/output_dir",
        "zipandpng/output_dir",
        "mp4mp3/output_dir",
        "imageconvert/output_dir",
        "pdftools/output_dir",
        "directdownloader/output_dir",
    ]

    assert "toolOutputDirDraft" in source
    assert "\\u5de5\\u5177\\u9ed8\\u8ba4\\u76ee\\u5f55" in source
    for key in keys:
        assert f'"{key}": toolOutputDirDraft.' in source


def test_tauri_settings_panel_has_file_download_behavior_card_and_save_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")
    keys = [
        "batchrename/input_dir",
        "batchrename/prefix",
        "batchrename/group_mode",
        "batchrename/sort_mode",
        "batchrename/sort_order",
        "filesorter/input_dir",
        "filesorter/mode",
        "same/input_dir",
        "same/recursive",
        "directdownloader/connections",
        "directdownloader/overwrite",
        "directdownloader/output_subdir_by_filename",
        "directdownloader/proxy_url",
        "directdownloader/referer",
    ]

    assert "toolBehaviorDraft" in source
    assert "\\u5de5\\u5177\\u884c\\u4e3a\\u504f\\u597d" in source
    for key in keys:
        assert f'"{key}": toolBehaviorDraft.' in source


def test_tauri_settings_panel_has_filesorter_category_switches_and_archive_output_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "FILESORTER_CATEGORIES" in source
    assert "categories: filesorterCategoriesFromSnapshot" in source
    assert "updateFilesorterCategory" in source
    assert '"archive_extractor/output_dir": toolOutputDirDraft.archive_extractor' in source
    assert "updates[`filesorter/category_${category}`]" in source
    assert "toolBehaviorDraft.filesorter.categories[category]" in source
    assert "archive_extractor/output_dir" in source


def test_tauri_settings_panel_has_wordformatter_card_and_save_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")
    keys = [
        "wordformatter/output_dir",
        "wordformatter/page/top_margin_cm",
        "wordformatter/page/footer_distance_cm",
        "wordformatter/styles/heading1/font",
        "wordformatter/styles/heading1/bold",
        "wordformatter/styles/body/font",
        "wordformatter/styles/body/line_spacing",
    ]

    assert "wordFormatterDraft" in source
    assert "updateWordFormatterPage" in source
    assert "updateWordFormatterStyle" in source
    assert "Word Formatter" in source
    for key in keys:
        assert f'"{key}"' in source


def test_migrated_tools_receive_initial_output_dir_props() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "toolOutputDir(snapshot, \"base64\")" in source
    assert "<Base64Tool initialOutputDir=" in source
    assert "<MusicTool initialOutputDir=" in source
    assert "<ZipPngTool initialOutputDir=" in source
    assert "<ImageConvertTool initialOutputDir=" in source
    assert "<Mp4Mp3Tool initialOutputDir=" in source
    assert "<PdfToolsTool initialOutputDir=" in source
    assert "<DirectDownloaderTool initialOutputDir=" in source


def test_file_download_tools_receive_initial_behavior_props() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "toolBehaviorSettings(snapshot, \"batchrename\")" in source
    assert "toolBehaviorSettings(snapshot, \"filesorter\")" in source
    assert "toolBehaviorSettings(snapshot, \"same\")" in source
    assert "toolBehaviorSettings(snapshot, \"directdownloader\")" in source
    assert "<BatchRenameTool initialSettings=" in source
    assert "<FileSorterTool initialSettings=" in source
    assert "<SameTool initialSettings=" in source
    assert "<DirectDownloaderTool initialOutputDir=" in source
    assert "initialSettings={toolBehaviorSettings(snapshot, \"directdownloader\")}" in source


def test_archive_extractor_receives_initial_settings_from_snapshot() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "snapshot?.tool_settings?.archive_extractor ?? {}" in source
    assert "<ArchiveExtractorPluginTool initialSettings=" in source


def test_filesorter_tool_initializes_categories_without_overwriting_user_edits() -> None:
    source = FILE_SORTER_TSX.read_text(encoding="utf-8")

    assert "initialSettings.categories" in source
    assert "didApplyInitial" in source
    assert "setSelectedCategories(categoriesFromSettings(initialSettings.categories))" in source
    assert "categoriesFromSettings" in source


def test_archive_extractor_tool_initializes_output_dir_without_overwriting_user_edits() -> None:
    source = ARCHIVE_EXTRACTOR_TSX.read_text(encoding="utf-8")

    assert "initialSettings?: ToolSettings" in source
    assert "initialSettings.output_dir" in source
    assert "didApplyInitial" in source
    assert "outputDirTouchedRef" in source


def test_wordformatter_tool_receives_and_merges_initial_settings_without_overwriting_user_edits() -> None:
    app_source = APP_TSX.read_text(encoding="utf-8")
    tool_source = WORD_FORMATTER_TSX.read_text(encoding="utf-8")

    assert "wordFormatterSettings(snapshot)" in app_source
    assert "<WordFormatterTool initialSettings=" in app_source
    assert "initialSettings?: ToolSettings" in tool_source
    assert "mergeWordConfig" in tool_source
    assert "configTouchedRef" in tool_source
    assert "outputDirTouchedRef" in tool_source
    assert "default_config" in tool_source


def test_direct_downloader_proxy_split_preserves_auth_for_legacy_build_proxy_url() -> None:
    source = DIRECT_DOWNLOADER_TSX.read_text(encoding="utf-8")
    start = source.index("function splitProxyUrl")
    end = source.index("\n}\n\nfunction DirectDownloaderTool", start) + 2
    body = source[start:end]

    assert "new URL(" in body
    assert "parsed.protocol" in body
    assert "parsed.username" in body
    assert "parsed.password" in body
    assert "parsed.host" in body
    assert ".lastIndexOf(\":\")" in body
    assert "host: parsed.hostname" not in body


WEB_VIDEO_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "WebVideoDownloaderTool.tsx"
TG_DOWNLOADER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "TgDownloaderTool.tsx"


def test_tauri_settings_snapshot_patch_and_browser_fallback_include_video_downloader_settings() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")
    string_keys = [
        "video_downloader/api_id",
        "video_downloader/api_hash",
        "video_downloader/phone",
        "video_downloader/phone_code_hash",
        "video_downloader/web/output_dir",
        "video_downloader/web/proxy_host",
        "video_downloader/web/proxy_port",
        "video_downloader/web/proxy_url",
        "video_downloader/web/concurrent",
        "video_downloader/web/cover_dir",
        "video_downloader/telegram/output_dir",
        "video_downloader/telegram/proxy_host",
        "video_downloader/telegram/proxy_port",
        "video_downloader/telegram/proxy_url",
        "video_downloader/telegram/recent_limit",
        "video_downloader/telegram/date_from",
        "video_downloader/telegram/date_to",
        "video_downloader/telegram/concurrent",
        "video_downloader/telegram/cover_dir",
    ]
    boolean_keys = [
        "video_downloader/web/overwrite",
        "video_downloader/web/output_subdir_by_title",
        "video_downloader/telegram/all_messages",
        "video_downloader/telegram/include_videos",
        "video_downloader/telegram/include_photos",
        "video_downloader/telegram/overwrite",
        "video_downloader/telegram/output_subdir_by_title",
    ]

    assert "webvideodownloader:" in source
    assert "tgdownloader:" in source
    assert "patchVideoDownloaderSettings" in source
    for key in string_keys:
        assert f'"{key}"?: string' in source
        assert f'patchString(patch.updates, "{key}"' in source
    for key in boolean_keys:
        assert f'"{key}"?: boolean' in source
        assert f'patchBoolean(patch.updates, "{key}"' in source


def test_tauri_settings_panel_has_downloader_preferences_card_and_save_payload() -> None:
    source = APP_TSX.read_text(encoding="utf-8")
    keys = [
        "video_downloader/api_id",
        "video_downloader/api_hash",
        "video_downloader/phone",
        "video_downloader/web/output_dir",
        "video_downloader/web/proxy_host",
        "video_downloader/web/proxy_port",
        "video_downloader/web/overwrite",
        "video_downloader/web/output_subdir_by_title",
        "video_downloader/web/concurrent",
        "video_downloader/telegram/output_dir",
        "video_downloader/telegram/recent_limit",
        "video_downloader/telegram/all_messages",
        "video_downloader/telegram/date_from",
        "video_downloader/telegram/date_to",
        "video_downloader/telegram/include_videos",
        "video_downloader/telegram/include_photos",
        "video_downloader/telegram/proxy_host",
        "video_downloader/telegram/proxy_port",
        "video_downloader/telegram/concurrent",
        "video_downloader/telegram/overwrite",
    ]

    assert "DownloaderSettingsDraft" in source
    assert "downloaderDraft" in source
    assert "\\u4e0b\\u8f7d\\u5668\\u504f\\u597d" in source
    for key in keys:
        assert f'"{key}": downloaderDraft.' in source


def test_downloader_tools_receive_initial_settings_from_snapshot() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "downloaderSettings(snapshot, \"webvideodownloader\")" in source
    assert "downloaderSettings(snapshot, \"tgdownloader\")" in source
    assert "<WebVideoDownloaderTool initialSettings=" in source
    assert "<TgDownloaderTool initialSettings=" in source


def test_web_video_downloader_tool_initializes_legacy_settings_and_payload_options() -> None:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    required = [
        "initialSettings?: ToolSettings",
        "initialSettings.proxy_host",
        "initialSettings.proxy_port",
        "initialSettings.proxy_url",
        "outputDirTouchedRef",
        "settingsTouchedRef",
        "overwrite",
        "output_subdir_by_title",
        "max_concurrent_downloads",
        "proxy_host",
        "proxy_port",
        "proxy_url",
    ]

    for marker in required:
        assert marker in source


def test_tg_downloader_tool_initializes_legacy_settings_and_payload_credentials_options() -> None:
    source = TG_DOWNLOADER_TSX.read_text(encoding="utf-8")
    required = [
        "initialSettings?: ToolSettings",
        "initialSettings.api_id",
        "initialSettings.api_hash",
        "initialSettings.phone",
        "initialSettings.phone_code_hash",
        "credentialsTouchedRef",
        "optionsTouchedRef",
        "outputDirTouchedRef",
        "phone_code_hash: phoneCodeHash",
        "proxy_url",
        "proxy_host",
        "proxy_port",
        "max_concurrent_downloads",
        "overwrite",
        "outputSubdirByTitle",
        "initialSettings.output_subdir_by_title",
        "output_subdir_by_title: outputSubdirByTitle",
        "setOutputSubdirByTitle",
    ]

    for marker in required:
        assert marker in source



def test_settings_panel_does_not_expose_or_save_phone_code_hash_or_removed_web_candidate_options() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "video_downloader/phone_code_hash" not in source
    assert "phone_code_hash" not in source
    for removed in ("web_candidate", "web_all_candidates", "thumbnail_mode"):
        assert removed not in source



def test_tauri_toolitem_type_and_browser_fallback_keep_legacy_metadata() -> None:
    source = TAURI_TS.read_text(encoding="utf-8")

    for marker in (
        "sidebar_label?: string",
        "dir_name?: string",
        "converter_file?: string",
        "tab_file?: string",
        "extra_files?: readonly string[]",
        "tab_kwargs?: Record<string, unknown>",
        "priority?: number",
        "...tool",
        "orderTools(tools, sidebarOrder)",
    ):
        assert marker in source


def test_tool_shell_prefers_sidebar_label_without_backend_table_ui() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "components" / "ToolShell.tsx").read_text(encoding="utf-8")

    assert "tool.sidebar_label ?? tool.title" in source
    assert "activeTool?.sidebar_label ?? activeTool?.title" in source
    assert "<table" not in source.lower()


def test_tool_shell_sidebar_preserves_incoming_tool_order_without_regrouping() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "components" / "ToolShell.tsx").read_text(encoding="utf-8")

    assert "tools.reduce" not in source
    assert "groupedTools" not in source
    assert "Object.entries(" not in source
    assert "tools.map(" in source


def test_settings_panel_surfaces_legacy_builtin_and_plugin_metadata() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    for marker in (
        "tool.sidebar_label ?? tool.title",
        "tool.dir_name",
        "tool.converter_file",
        "tool.tab_file",
        "tool.extra_files",
        "tool.tab_kwargs",
        "tool.description",
        "tool.version",
        "tool.priority",
        "pluginConfigKey(tool)",
    ):
        assert marker in source


def test_tauri_settings_save_sidebar_order_preserves_unknown_legacy_ids() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert "function sidebarOrderForSave" in source
    assert "const currentOrder = visibleOrder.filter((toolId) => toolsById.has(toolId));" in source
    assert "snapshot.sidebar_order.forEach((legacyToolId) => {" in source
    assert "mergedOrder.push(legacyToolId);" in source
    assert "currentOrder.slice(currentIndex).forEach((toolId) => {" in source
    assert '"sidebar/order": sidebarOrderForSave(snapshot, orderDraft, toolsById)' in source


def test_tauri_settings_save_sidebar_order_preserves_unknown_legacy_id_slots() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    saved_order = _run_sidebar_order_for_save(
        source,
        snapshot_order=["music", "legacy:future", "base64"],
        visible_order=["base64", "music", "pdftools"],
        current_tool_ids=["music", "base64", "pdftools"],
    )

    assert saved_order == ["base64", "legacy:future", "music", "pdftools"]
