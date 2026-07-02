from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sidecar.settings_bridge import build_settings_snapshot

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "desktop-tauri" / "src" / "App.tsx"
STYLES_CSS = ROOT / "desktop-tauri" / "src" / "styles.css"
BATCH_RENAME_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "BatchRenameTool.tsx"
DIRECT_DOWNLOADER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "DirectDownloaderTool.tsx"
FILE_SORTER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "FileSorterTool.tsx"
ARCHIVE_EXTRACTOR_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "ArchiveExtractorPluginTool.tsx"
WORD_FORMATTER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "WordFormatterTool.tsx"
WEB_VIDEO_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "WebVideoDownloaderTool.tsx"
TG_DOWNLOADER_TSX = ROOT / "desktop-tauri" / "src" / "tools" / "TgDownloaderTool.tsx"
TAURI_TS = ROOT / "desktop-tauri" / "src" / "api" / "tauri.ts"
BROWSER_FALLBACK_TS = ROOT / "desktop-tauri" / "src" / "api" / "browserSettingsFallback.ts"
BROWSER_PATCHERS_TS = ROOT / "desktop-tauri" / "src" / "api" / "browserSettingsPatchers.ts"
README_MD = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
PYPROJECT = ROOT / "pyproject.toml"
TAURI_SIDECAR_RS = ROOT / "desktop-tauri" / "src-tauri" / "src" / "sidecar.rs"
TOOL_SHELL_TSX = ROOT / "desktop-tauri" / "src" / "components" / "ToolShell.tsx"
TOOLS_PANELS_TSX = ROOT / "desktop-tauri" / "src" / "features" / "tools" / "panels.tsx"
SETTINGS_PANEL_TSX = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "SettingsPanel.tsx"
SETTINGS_HELPERS_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "helpers.ts"
SETTINGS_MODELS_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "models.ts"
SETTINGS_PATCH_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "patch.ts"
SETTINGS_SELECTORS_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "selectors.ts"
SETTINGS_CONTROLLER_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "useSettingsPanelController.ts"
VIEWSTATE_TS = ROOT / "desktop-tauri" / "src" / "features" / "settings" / "controller" / "viewState.ts"
SIDECAR_RS = ROOT / "desktop-tauri" / "src-tauri" / "src" / "sidecar.rs"
WEB_SIDECAR_TOOL = ROOT / "sidecar" / "tools" / "webvideodownloader_tool.py"
TG_SIDECAR_TOOL = ROOT / "sidecar" / "tools" / "tgdownloader_tool.py"
DOWNLOAD_RUNTIME_HOOK_TS = ROOT / "desktop-tauri" / "src" / "features" / "tools" / "hooks" / "useDownloadRuntimeSession.ts"
DOWNLOAD_QUEUE_STATE_TS = ROOT / "desktop-tauri" / "src" / "features" / "tools" / "downloadQueueState.ts"


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
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def _run_download_queue_rows_from_session(source_path: Path, tasks: list[dict], session: dict) -> list[dict]:
    source = source_path.read_text(encoding="utf-8")
    parse_progress_body = _extract_function_body(source, "parseProgressMarker")
    short_path_body = _extract_function_body(source, "shortPathName")
    percent_value_body = _extract_function_body(source, "percentValue")
    marker_index_body = _extract_function_body(source, "markerIndex")
    queue_rows_body = _extract_function_body(source, "queueRowsFromSession")
    script = f"""
const tasks = {json.dumps(tasks, ensure_ascii=False)};
const session = {json.dumps(session, ensure_ascii=False)};
const options = {{
  progressKinds: ["file", "web_status", "web_aria2", "web_percent", "tg_media"],
  applyCompletedResult(row, result) {{
    return {{ row, result }};
  }},
}};
function parseProgressMarker(message) {{
{parse_progress_body}
}}
function shortPathName(value) {{
{short_path_body}
}}
function percentValue(value) {{
{percent_value_body}
}}
function markerIndex(marker, fallbackIndex) {{
{marker_index_body}
}}
function queueRowsFromSession(tasks, session, options) {{
{queue_rows_body}
}}
process.stdout.write(JSON.stringify(queueRowsFromSession(tasks, session, options)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def _run_web_video_inspect_candidate_urls(results: list[dict]) -> list[str]:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    body = _extract_function_body(source, "inspectCandidateUrls")
    script = f"""
const results = {json.dumps(results, ensure_ascii=False)};
function inspectCandidateUrls(results) {{
{body}
}}
process.stdout.write(JSON.stringify(inspectCandidateUrls(results)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def _run_web_video_candidate_tasks(results: list[dict]) -> list[dict]:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    inspect_urls_body = _extract_function_body(source, "inspectCandidateUrls")
    source_title_body = _extract_function_body(source, "sourceTitleFromUrl")
    numbered_title_body = _extract_function_body(source, "numberedTitle")
    candidate_tasks_body = _extract_function_body(source, "candidateTasksFromInspectResults")
    script = f"""
const results = {json.dumps(results, ensure_ascii=False)};
function inspectCandidateUrls(results) {{
{inspect_urls_body}
}}
function sourceTitleFromUrl(url) {{
{source_title_body}
}}
function numberedTitle(base, index, total) {{
{numbered_title_body}
}}
function candidateTasksFromInspectResults(results) {{
{candidate_tasks_body}
}}
process.stdout.write(JSON.stringify(candidateTasksFromInspectResults(results)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def _run_web_video_task_helpers(function_name: str, tasks: list[dict], *args: object) -> list[dict]:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    source_title_body = _extract_function_body(source, "sourceTitleFromUrl")
    sanitize_body = _extract_function_body(source, "sanitizeTaskTitle")
    base_body = _extract_function_body(source, "taskTitleBase")
    group_key_body = _extract_function_body(source, "taskGroupKey")
    renumber_body = _extract_function_body(source, "reindexGroupedTasks")
    rename_body = _extract_function_body(source, "renameGroupedTaskTitles")
    remove_body = _extract_function_body(source, "removeQueuedTask")
    apply_subdir_body = _extract_function_body(source, "applyTaskOutputSubdirs")
    script = f"""
const tasks = {json.dumps(tasks, ensure_ascii=False)};
const fnName = {json.dumps(function_name)};
const args = {json.dumps(args, ensure_ascii=False)};
function sourceTitleFromUrl(url) {{
{source_title_body}
}}
function sanitizeTaskTitle(value, fallback = "video") {{
{sanitize_body}
}}
function taskTitleBase(title) {{
{base_body}
}}
function taskGroupKey(task) {{
{group_key_body}
}}
function numberedTitle(base, index, total) {{
  return total > 1 ? `${{base}}_${{String(index).padStart(3, "0")}}` : base;
}}
function reindexGroupedTasks(tasks) {{
{renumber_body}
}}
function renameGroupedTaskTitles(tasks, index, nextTitle) {{
{rename_body}
}}
function removeQueuedTask(tasks, index) {{
{remove_body}
}}
function applyTaskOutputSubdirs(tasks, enabled) {{
{apply_subdir_body}
}}
const mapping = {{
  renameGroupedTaskTitles,
  removeQueuedTask,
  applyTaskOutputSubdirs,
}};
process.stdout.write(JSON.stringify(mapping[fnName](tasks, ...args)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def _run_download_queue_overview(tasks: list[dict], session: dict | None) -> dict:
    source = DOWNLOAD_QUEUE_STATE_TS.read_text(encoding="utf-8")
    parse_progress_body = _extract_function_body(source, "parseProgressMarker")
    session_rows_body = _extract_function_body(source, "sessionResultRows")
    marker_index_body = _extract_function_body(source, "markerIndex")
    overview_body = _extract_function_body(source, "queueOverviewFromSession")
    script = f"""
const tasks = {json.dumps(tasks, ensure_ascii=False)};
const session = {json.dumps(session, ensure_ascii=False)};
function parseProgressMarker(message) {{
{parse_progress_body}
}}
function sessionResultRows(session) {{
{session_rows_body}
}}
function markerIndex(marker, fallbackIndex) {{
{marker_index_body}
}}
function queueOverviewFromSession(tasks, session) {{
{overview_body}
}}
process.stdout.write(JSON.stringify(queueOverviewFromSession(tasks, session)));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def test_pyproject_uses_writable_repo_local_basetemp() -> None:
    source = PYPROJECT.read_text(encoding="utf-8")

    assert "--basetemp=tests/pytest-tmp" not in source
    assert "--basetemp=.codex-pytest-tmp" not in source
    assert 'norecursedirs = ["pytest-tmp", ".codex-pytest-tmp"]' in source


def test_batchrename_group_mode_uses_legacy_all_files_label() -> None:
    batch_source = BATCH_RENAME_TSX.read_text(encoding="utf-8")
    assert '"\\u5168\\u6587\\u4ef6": "all"' in batch_source
    assert "label: \"\u5168\u6587\u4ef6\"" in batch_source
    assert "\u5168\u90e8\u6587\u4ef6" not in batch_source
    assert "\\u5168\\u90e8\\u6587\\u4ef6" not in batch_source


def test_settings_selectors_preserve_custom_theme_drafts_and_tool_settings() -> None:
    source = SETTINGS_SELECTORS_TS.read_text(encoding="utf-8")

    for marker in (
        "themeColorDraftsFromSnapshot",
        "snapshot.theme.custom_colors",
        "customColors[theme]",
        "snapshot.theme.colors",
        "toolOutputDirsFromSnapshot",
        "toolBehaviorDraftsFromSnapshot",
        "downloaderDraftFromSnapshot",
        "wordFormatterDraftFromSnapshot",
        "createSettingsDraftState",
        "export function wordFormatterSettings",
        "export function toolBehaviorSettings",
        "export function downloaderSettings",
    ):
        assert marker in source



def test_settings_models_define_expected_draft_structures() -> None:
    source = SETTINGS_MODELS_TS.read_text(encoding="utf-8")

    for marker in (
        "THEME_ZONES",
        "TOOL_OUTPUT_DIRS",
        "FILESORTER_CATEGORIES",
        "DownloaderSettingsDraft",
        "WordFormatterDraft",
        "DEFAULT_TOOL_OUTPUT_DIR_DRAFT",
        "DEFAULT_TOOL_BEHAVIOR_DRAFT",
        "DEFAULT_DOWNLOADER_SETTINGS_DRAFT",
        "DEFAULT_WORD_FORMATTER_DRAFT",
        "WORD_FORMATTER_PAGE_SETTING_KEYS",
        "WORD_FORMATTER_STYLE_SETTING_KEYS",
    ):
        assert marker in source



def test_settings_patch_builds_theme_auth_disabled_tool_and_sidebar_updates() -> None:
    source = SETTINGS_PATCH_TS.read_text(encoding="utf-8")

    for marker in (
        '"ui/custom_theme_enabled": drafts.customThemeEnabled',
        '"auth/remember_password": drafts.rememberPassword',
        '"auth/auto_login": drafts.autoLogin',
        '"tools/disabled": [...drafts.disabledTools].sort()',
        '"plugins/disabled": [...drafts.disabledPlugins].sort()',
        '"archive_extractor/output_dir": drafts.toolOutputDirs.archive_extractor',
        '"video_downloader/web/output_dir": drafts.downloader.webvideodownloader.output_dir',
        '"video_downloader/telegram/output_dir": drafts.downloader.tgdownloader.output_dir',
        '"wordformatter/output_dir": drafts.wordFormatter.output_dir',
        '"sidebar/order": sidebarOrderForSave(snapshot, drafts.sidebarOrder, toolsById)',
        "WORD_FORMATTER_PAGE_KEYS.forEach",
        "WORD_FORMATTER_STYLE_KEYS.forEach",
        "FILESORTER_CATEGORIES.forEach",
        "THEME_ZONES.forEach",
    ):
        assert marker in source



def test_browser_settings_fallback_keeps_custom_colors_auth_disabled_plugins_and_metadata() -> None:
    source = BROWSER_FALLBACK_TS.read_text(encoding="utf-8")

    for marker in (
        "custom_colors: {",
        "disabled_plugins: [...disabledPluginSet].sort()",
        'patch.updates["plugins/disabled"]',
        'patch.updates["auth/remember_password"]',
        'patch.updates["auth/auto_login"]',
        'patch.updates["base64/output_dir"]',
        'patchString(patch.updates, "archive_extractor/output_dir"',
        "browserWordFormatterSettings",
        "patchWordFormatterSettings",
        "patchVideoDownloaderSettings",
        "orderTools(tools, sidebarOrder)",
        "...tool",
    ):
        assert marker in source



def test_browser_settings_patchers_cover_tool_behavior_wordformatter_and_video_settings() -> None:
    source = BROWSER_PATCHERS_TS.read_text(encoding="utf-8")

    for marker in (
        "patchString",
        "patchBoolean",
        "patchWordFormatterSettings",
        "patchFilesorterCategories",
        "browserProxyUrl",
        "patchVideoDownloaderSettings",
        'updates: SettingsPatch["updates"]',
        'patchBoolean(patch.updates, "video_downloader/web/overwrite"',
        'patchString(patch.updates, "video_downloader/telegram/recent_limit"',
        'patchString(updates, "wordformatter/output_dir"',
    ):
        assert marker in source



def test_settings_panel_wires_sections_and_controller_callbacks() -> None:
    panel_source = SETTINGS_PANEL_TSX.read_text(encoding="utf-8")
    controller_source = SETTINGS_CONTROLLER_TS.read_text(encoding="utf-8")

    for marker in (
        "SettingsSummarySection",
        "AccountPreferencesSection",
        "ThemeModeSection",
        "ToolOutputDirsSection",
        "DownloaderSettingsSection",
        "WordFormatterSection",
        "ToolBehaviorSection",
        "BuiltinToolsSection",
        "SidebarOrderSection",
        "PluginStatusSection",
        "ThemePaletteSection",
        "saveSettings",
    ):
        assert marker in panel_source

    for marker in (
        "createSettingsDraftState",
        "saveSettingsSnapshot",
        "sidebarStatus",
        "toolDisplayName",
        "toolMetadata",
        "setPluginEnabled",
        "updateDownloader",
        "updateWordFormatterStyle",
    ):
        assert marker in controller_source



def test_settings_panel_uses_grouped_navigation_shell() -> None:
    panel_source = SETTINGS_PANEL_TSX.read_text(encoding="utf-8")
    styles_source = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        "const SETTINGS_SECTIONS =",
        'id: "general"',
        'id: "appearance"',
        'id: "paths"',
        'id: "downloaders"',
        'id: "wordformatter"',
        'id: "tools"',
        'id: "sidebar"',
        "settings-shell",
        "settings-nav",
        "settings-nav-button",
        "settings-content",
        "activeSection",
        "setActiveSection",
    ):
        assert marker in panel_source

    for marker in (
        ".settings-shell",
        ".settings-nav",
        ".settings-nav-button",
        ".settings-nav-button.active",
        ".settings-content",
        ".settings-section-hero",
        ".settings-two-column-grid",
    ):
        assert marker in styles_source


def test_theme_palette_section_exposes_color_picker_and_card_opacity_slider() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ThemePaletteSection.tsx").read_text(encoding="utf-8")

    for marker in (
        'type="color"',
        'type="range"',
        'aria-label="玻璃强度"',
        'className="theme-opacity-control"',
    ):
        assert marker in source


def test_glass_material_defaults_follow_selected_light_and_dark_directions() -> None:
    models_source = SETTINGS_MODELS_TS.read_text(encoding="utf-8")
    browser_source = BROWSER_FALLBACK_TS.read_text(encoding="utf-8")
    sidecar_source = (ROOT / "sidecar" / "settings_bridge.py").read_text(encoding="utf-8")

    for source in (models_source, browser_source, sidecar_source):
        assert "rgba(44, 50, 59, 0.70)" in source
        assert "rgba(255, 255, 255, 0.38)" in source
        assert "rgba(44, 50, 59, 0.88)" not in source
        assert "rgba(255, 255, 255, 0.76)" not in source


def test_theme_style_derives_glass_strength_variables_from_card_alpha() -> None:
    source = SETTINGS_HELPERS_TS.read_text(encoding="utf-8")

    for marker in (
        "const GLASS_MIN_ALPHA = 10",
        "const GLASS_MAX_ALPHA = 70",
        "const GLASS_MIN_BLUR = 4",
        "const GLASS_MAX_BLUR = 24",
        "function cardColorAlphaPercent",
        "function glassBlurPx",
        "const glassAlphaPercent = cardColorAlphaPercent(colors.card_bg)",
        '"--glass-alpha"',
        '"--glass-blur": `${glassBlurPx(glassAlphaPercent)}px`',
        '"--glass-edge-alpha"',
        '"--glass-shadow-alpha"',
        '"--glass-panel-bg"',
    ):
        assert marker in source


def test_settings_panel_applies_draft_theme_style_for_live_preview() -> None:
    source = SETTINGS_PANEL_TSX.read_text(encoding="utf-8")
    app_source = APP_TSX.read_text(encoding="utf-8")

    for marker in (
        "onPreviewThemeChange",
        "useEffect(() => {",
        "drafts.customThemeEnabled ? drafts.themeColors[drafts.theme] : DEFAULT_THEME_COLORS[drafts.theme]",
        "drafts.themeColors[drafts.theme]",
    ):
        assert marker in source

    for marker in (
        "previewTheme",
        "themeStyleFromColors",
        "handlePreviewThemeChange",
        "setPreviewTheme(null)",
        "previewTheme?.style ?? themeStyle(snapshot)",
        'data-theme-mode={previewTheme?.mode ?? snapshot?.ui.theme ?? "light"}',
    ):
        assert marker in app_source


def test_theme_palette_section_exposes_glass_strength_slider_contract() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ThemePaletteSection.tsx").read_text(encoding="utf-8")

    for marker in (
        "玻璃强度",
        "Alpha",
        "Blur",
        "clampGlassAlpha",
        'min="10"',
        'max="70"',
        'step="1"',
        'aria-label="玻璃强度"',
    ):
        assert marker in source


def test_styles_use_glass_variables_for_material_layers() -> None:
    source = STYLES_CSS.read_text(encoding="utf-8")

    for marker in (
        "repeating-linear-gradient(135deg",
        "var(--glass-panel-bg)",
        "blur(var(--glass-window-blur))",
        "blur(var(--glass-blur)) saturate(var(--glass-saturation))",
        "var(--glass-card-shadow)",
        "var(--glass-panel-shadow)",
        "var(--glass-edge)",
        "var(--glass-soft-bg)",
    ):
        assert marker in source


def test_settings_sections_present_human_readable_labels_and_word_details() -> None:
    downloader_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "DownloaderSettingsSection.tsx").read_text(encoding="utf-8")
    word_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "WordFormatterSection.tsx").read_text(encoding="utf-8")
    behavior_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ToolBehaviorSection.tsx").read_text(encoding="utf-8")
    palette_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ThemePaletteSection.tsx").read_text(encoding="utf-8")
    models_source = SETTINGS_MODELS_TS.read_text(encoding="utf-8")

    for marker in (
        "Web 下载",
        "Telegram 下载",
        "Web 输出目录",
        "代理主机",
        "代理端口",
        "兼容代理 URL",
        "并发下载数",
        "按标题创建子目录",
        "最近消息数",
        "起始日期",
        "结束日期",
    ):
        assert marker in downloader_source

    assert 'label="video_downloader/web/output_dir"' not in downloader_source
    assert 'label="video_downloader/telegram/output_dir"' not in downloader_source

    for marker in (
        "页面设置",
        "样式设置",
        '<details className="settings-detail-card"',
    ):
        assert marker in word_source

    for marker in (
        "标题 1",
        "标题 2",
        "标题 3",
        "标题 4",
        "正文",
        "表格",
        "字体",
        "字号（pt）",
        "是否加粗",
    ):
        assert marker in models_source

    for marker in (
        "批量命名",
        "文件分类",
        "重复文件",
        "直链下载",
        "分类模式",
        "命名前缀",
    ):
        assert marker in behavior_source

    for marker in (
        "主题配色",
    ):
        assert marker in palette_source

    for marker in (
        "窗口背景",
        "卡片背景",
        "主强调色",
        "主文字",
    ):
        assert marker in models_source


def test_settings_path_fields_use_directory_picker() -> None:
    primitives_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "primitives.tsx").read_text(encoding="utf-8")
    output_dirs_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ToolOutputDirsSection.tsx").read_text(encoding="utf-8")
    behavior_source = (ROOT / "desktop-tauri" / "src" / "features" / "settings" / "sections" / "ToolBehaviorSection.tsx").read_text(encoding="utf-8")

    for marker in (
        'from "../../../api/tauri"',
        "pickDirectory(",
        'type="button"',
        "path-pick-button",
    ):
        assert marker in primitives_source

    assert "SettingOutputDirRow" in output_dirs_source
    assert "SettingDirectoryField" in behavior_source


def test_settings_helpers_export_sidebar_order_and_metadata_helpers() -> None:
    source = SETTINGS_HELPERS_TS.read_text(encoding="utf-8")

    for marker in (
        "firstSelectableTool",
        "pluginConfigKey",
        "function sidebarOrderForSave",
        "toolDisplayName",
        "toolMetadata",
        "themeStyle",
    ):
        assert marker in source



def test_theme_style_feeds_new_ui_theme_variables() -> None:
    source = SETTINGS_HELPERS_TS.read_text(encoding="utf-8")

    for marker in (
        "DEFAULT_THEME_COLORS",
        "function themeColor",
        "CSS.supports(\"color\", value)",
        '"--ink": colors.text_primary',
        '"--ink-muted": colors.text_secondary',
        '"--surface": colors.surface_bg',
        '"--surface-strong": colors.card_bg',
        '"--surface-soft": colors.input_bg',
        '"--hairline"',
        '"--accent": colors.accent',
        '"--accent-strong": colors.accent',
        '"--scroll-thumb"',
        '"--scroll-thumb-hover"',
    ):
        assert marker in source



def test_new_ui_has_dark_mode_material_overrides() -> None:
    source = STYLES_CSS.read_text(encoding="utf-8")

    for marker in (
        '.theme-root[data-theme-mode="dark"] .window-surface',
        '.theme-root[data-theme-mode="dark"] .tool-list',
        '.theme-root[data-theme-mode="dark"] .tool-panel',
        '.theme-root[data-theme-mode="dark"] .settings-panel',
        '.theme-root[data-theme-mode="dark"] .settings-card',
        '.theme-root[data-theme-mode="dark"] .settings-save-sticky',
        '.theme-root[data-theme-mode="dark"] .theme-swatch',
        '.theme-root[data-theme-mode="dark"] input',
        "width: 148px;",
        "margin-left: -8px;",
    ):
        assert marker in source



def test_app_keeps_dark_selector_active_when_custom_theme_is_enabled() -> None:
    source = APP_TSX.read_text(encoding="utf-8")

    assert 'data-theme-mode={previewTheme?.mode ?? snapshot?.ui.theme ?? "light"}' in source
    assert 'data-theme-mode={snapshot?.theme.mode ?? "light"}' not in source



def test_sidebar_order_for_save_preserves_unknown_legacy_id_slots() -> None:
    source = SETTINGS_HELPERS_TS.read_text(encoding="utf-8")

    saved_order = _run_sidebar_order_for_save(
        source,
        snapshot_order=["music", "legacy:future", "base64"],
        visible_order=["base64", "music", "pdftools"],
        current_tool_ids=["music", "base64", "pdftools"],
    )

    assert saved_order == ["base64", "legacy:future", "music", "pdftools"]



def test_panels_wire_initial_output_dirs_for_builtin_tools() -> None:
    source = TOOLS_PANELS_TSX.read_text(encoding="utf-8")

    for marker in (
        'toolOutputDir(snapshot, "music")',
        'toolOutputDir(snapshot, "imageconvert")',
        'toolOutputDir(snapshot, "mp4mp3")',
        'toolOutputDir(snapshot, "pdftools")',
        'toolOutputDir(snapshot, "base64")',
        'toolOutputDir(snapshot, "directdownloader")',
        'toolOutputDir(snapshot, "zipandpng")',
        "<MusicTool initialOutputDir=",
        "<ImageConvertTool initialOutputDir=",
        "<Mp4Mp3Tool initialOutputDir=",
        "<PdfToolsTool initialOutputDir=",
        "<Base64Tool initialOutputDir=",
        "<DirectDownloaderTool",
        "<ZipPngTool initialOutputDir=",
    ):
        assert marker in source



def test_panels_wire_initial_behavior_and_downloader_settings() -> None:
    source = TOOLS_PANELS_TSX.read_text(encoding="utf-8")

    for marker in (
        'toolBehaviorSettings(snapshot, "batchrename")',
        'toolBehaviorSettings(snapshot, "filesorter")',
        'toolBehaviorSettings(snapshot, "same")',
        'toolBehaviorSettings(snapshot, "directdownloader")',
        'downloaderSettings(snapshot, "webvideodownloader")',
        'downloaderSettings(snapshot, "tgdownloader")',
        'wordFormatterSettings(snapshot)',
        "<BatchRenameTool initialSettings=",
        "<FileSorterTool initialSettings=",
        "<SameTool initialSettings=",
        "<WebVideoDownloaderTool initialSettings=",
        "<TgDownloaderTool initialSettings=",
        "<WordFormatterTool initialSettings=",
    ):
        assert marker in source



def test_ready_builtin_and_plugin_tools_all_have_panel_renderers() -> None:
    panels_source = TOOLS_PANELS_TSX.read_text(encoding="utf-8")
    snapshot = build_settings_snapshot()

    for tool in snapshot["tools"]:
        if tool["source"] == "builtin" and tool["status"] == "ready":
            assert f'{tool["id"]}:' in panels_source
        if tool["source"] == "plugin" and tool["status"] == "ready" and tool.get("manifest_enabled") is not False:
            assert f'"{tool["id"]}":' in panels_source



def test_plugin_hello_world_remains_manifest_disabled_placeholder() -> None:
    snapshot = build_settings_snapshot()
    hello = next(item for item in snapshot["tools"] if item["id"] == "plugin:hello_world")

    assert hello["manifest_enabled"] is False
    assert hello["enabled"] is False
    assert hello["status"] == "pending"



def test_view_state_and_tool_shell_use_sidebar_label_and_status_text() -> None:
    view_state = VIEWSTATE_TS.read_text(encoding="utf-8")
    shell_source = TOOL_SHELL_TSX.read_text(encoding="utf-8")

    for marker in (
        "tool.sidebar_label ?? tool.title",
        "toolTitle(activeTool, settingsOpen)",
        "return tool?.sidebar_label ?? tool?.title",
        "CAPABILITY_NOTES",
        "tool.status === \"ready\" ?",
    ):
        assert marker in view_state or marker in shell_source

    assert "<table" not in shell_source.lower()
    assert "tools.reduce" not in shell_source
    assert "groupedTools" not in shell_source
    assert "tools.map(" in shell_source



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



def test_gitignore_excludes_codex_artifacts_and_pytest_tmp() -> None:
    source = GITIGNORE.read_text(encoding="utf-8")

    for pattern in (
        "\u6d4b\u8bd5/",
        "task_plan.md",
        "findings.md",
        "progress.md",
        ".codex-pytest-tmp*/",
        ".codex-plugin-*/",
        ".codex-*-smoke*/",
        ".codex-*-settings*/",
        ".codex-review-tmp*/",
        ".codex-*.json",
        ".codex-*.ini",
        "desktop-tauri/test-results/",
    ):
        assert pattern in source
    assert "\u5a34\u5b2d\u762f/" not in source


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
    panels_source = TOOLS_PANELS_TSX.read_text(encoding="utf-8")
    tool_source = WORD_FORMATTER_TSX.read_text(encoding="utf-8")

    assert "wordFormatterSettings(snapshot)" in panels_source
    assert "<WordFormatterTool initialSettings=" in panels_source
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



def test_direct_downloader_tool_uses_collapsible_advanced_options_and_removes_debug_panels() -> None:
    source = DIRECT_DOWNLOADER_TSX.read_text(encoding="utf-8")

    assert '<details className="file-mode-card direct-advanced-options"' in source
    assert "<summary>高级选项</summary>" in source
    assert "ResultCards" not in source
    assert "handleBuildCommands" not in source
    assert "命令预览" not in source


def test_direct_downloader_streams_runtime_progress_into_queue_table() -> None:
    source = DIRECT_DOWNLOADER_TSX.read_text(encoding="utf-8")

    for marker in (
        'useDownloadRuntimeSession("directdownloader")',
        "DownloadQueueTable",
        "queueOverviewFromSession(",
        'progressKinds: ["direct_aria2"]',
        "runtime.start(input)",
        'onCancel={() => void runtime.control("cancel")}',
    ):
        assert marker in source


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


def test_web_video_downloader_inspect_expands_all_detected_candidates() -> None:
    results = [
        {
            "source_url": "https://example.com/course",
            "success": True,
            "candidate_count": 3,
            "candidates": [
                "https://cdn.example.com/a.mp4",
                "",
                "https://cdn.example.com/b.mp4",
                "https://cdn.example.com/a.mp4",
                "https://cdn.example.com/c.mp4",
            ],
            "source": "yt-dlp",
            "error": "",
        }
    ]
    urls = _run_web_video_inspect_candidate_urls(results)

    assert urls == [
        "https://cdn.example.com/a.mp4",
        "https://cdn.example.com/b.mp4",
        "https://cdn.example.com/c.mp4",
    ]
    assert _run_web_video_candidate_tasks(results) == [
        {
            "source_url": "https://cdn.example.com/a.mp4",
            "source_kind": "web",
            "target_title": "course_001",
            "source_page_url": "https://example.com/course",
            "candidate_index": 1,
            "candidate_total": 3,
        },
        {
            "source_url": "https://cdn.example.com/b.mp4",
            "source_kind": "web",
            "target_title": "course_002",
            "source_page_url": "https://example.com/course",
            "candidate_index": 2,
            "candidate_total": 3,
        },
        {
            "source_url": "https://cdn.example.com/c.mp4",
            "source_kind": "web",
            "target_title": "course_003",
            "source_page_url": "https://example.com/course",
            "candidate_index": 3,
            "candidate_total": 3,
        },
    ]

    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    assert "applyQueuedTasks(candidateTasks)" in source


def test_web_video_downloader_download_auto_inspects_page_candidates() -> None:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    body = _extract_function_body(source, "handleDownload")

    assert "await inspectAndApplyCandidates()" in body
    assert "downloadPayload = { ...payload, text: candidateUrls.join(\"\\n\") }" in body
    assert "const queuedTasks = applyTaskOutputSubdirs(candidateTasks, outputSubdirByTitle)" in body
    assert "tasks: queuedTasks" in body
    assert "payload: downloadPayload" in body


def test_web_video_downloader_validate_auto_expands_page_candidates() -> None:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    body = _extract_function_body(source, "handleParseValidate")

    assert "if (checked.valid) {" in body
    assert "await inspectAndApplyCandidates()" in body


def test_web_video_downloader_queue_supports_renaming_candidate_titles() -> None:
    web_source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    queue_source = (ROOT / "desktop-tauri" / "src" / "features" / "tools" / "components" / "DownloadQueueTable.tsx").read_text(encoding="utf-8")

    assert "function renameTaskTitle" in web_source
    assert "onRename={renameTaskTitle}" in web_source
    assert "function removeQueuedTask" in web_source
    assert "onDelete={removeQueuedTask}" in web_source
    assert "onDoubleClick" in queue_source
    assert "onRename?.(index" in queue_source
    assert 'type="button"' in queue_source
    assert "×" in queue_source


def test_web_video_downloader_grouped_rename_delete_and_subdir_follow_legacy_rules() -> None:
    renamed = _run_web_video_task_helpers(
        "renameGroupedTaskTitles",
        [
            {
                "source_url": "https://cdn.example.com/a.mp4",
                "source_kind": "web",
                "target_title": "29274_001",
                "source_page_url": "https://example.com/course",
            },
            {
                "source_url": "https://cdn.example.com/b.mp4",
                "source_kind": "web",
                "target_title": "29274_002",
                "source_page_url": "https://example.com/course",
            },
        ],
        0,
        "课程",
    )
    assert [item["target_title"] for item in renamed] == ["课程_001", "课程_002"]

    rejected_blank = _run_web_video_task_helpers("renameGroupedTaskTitles", renamed, 0, "   ")
    assert [item["target_title"] for item in rejected_blank] == ["课程_001", "课程_002"]

    removed = _run_web_video_task_helpers(
        "removeQueuedTask",
        [
            {
                "source_url": "https://cdn.example.com/a.mp4",
                "source_kind": "web",
                "target_title": "课程_001",
                "source_page_url": "https://example.com/course",
            },
            {
                "source_url": "https://cdn.example.com/b.mp4",
                "source_kind": "web",
                "target_title": "课程_002",
                "source_page_url": "https://example.com/course",
            },
            {
                "source_url": "https://cdn.example.com/c.mp4",
                "source_kind": "web",
                "target_title": "课程_003",
                "source_page_url": "https://example.com/course",
            },
        ],
        1,
    )
    assert [item["source_url"] for item in removed] == [
        "https://cdn.example.com/a.mp4",
        "https://cdn.example.com/c.mp4",
    ]
    assert [item["target_title"] for item in removed] == ["课程_001", "课程_002"]

    subdirs = _run_web_video_task_helpers("applyTaskOutputSubdirs", renamed, True)
    assert [item["output_subdir"] for item in subdirs] == ["课程", "课程"]


def test_web_video_downloader_cover_entry_and_embed_thumbnail_action_are_wired() -> None:
    source = WEB_VIDEO_TSX.read_text(encoding="utf-8")

    for marker in (
        "pickFiles(",
        'action: "embed_thumbnail"',
        "thumbnail_mode",
        "candidate_index",
        "source_page_url",
        "function handleEmbedThumbnail",
    ):
        assert marker in source

    sidecar_source = WEB_SIDECAR_TOOL.read_text(encoding="utf-8")
    for marker in (
        'if action == "embed_thumbnail"',
        "module.embed_thumbnail(",
        "thumbnail_mode",
        "candidate_index",
    ):
        assert marker in sidecar_source


def test_download_queue_overview_uses_runtime_markers_and_results() -> None:
    running = _run_download_queue_overview(
        [
            {"source_url": "https://example.com/a", "target_title": "Task A"},
            {"source_url": "https://example.com/b", "target_title": "Task B"},
            {"source_url": "https://example.com/c", "target_title": "Task C"},
        ],
        {
            "status": "running",
            "progress_events": [
                {"message": "__HYL_PROGRESS__|task_start|index=0|total=3|url=https://example.com/a"},
                {"message": "__HYL_PROGRESS__|task_done|index=0|completed=1|total=3"},
                {"message": "__HYL_PROGRESS__|task_start|index=1|total=3|url=https://example.com/b"},
                {"message": "__HYL_PROGRESS__|web_percent|index=1|percent=40"},
            ],
            "result": None,
        },
    )
    assert running == {
        "total": 3,
        "current": 2,
        "completed": 1,
        "failed": 0,
        "summary": "1/3 完成，当前第 2 项",
    }

    completed = _run_download_queue_overview(
        [
            {"source_url": "https://example.com/a", "target_title": "Task A"},
            {"source_url": "https://example.com/b", "target_title": "Task B"},
        ],
        {
            "status": "completed",
            "progress_events": [],
            "result": {
                "data": {
                    "results": [
                        {"success": True},
                        {"success": False, "error": "boom"},
                    ]
                }
            },
        },
    )
    assert completed == {
        "total": 2,
        "current": 2,
        "completed": 1,
        "failed": 1,
        "summary": "1/2 完成，1 失败",
    }


def test_tg_downloader_all_messages_disables_recent_limit_input() -> None:
    source = TG_DOWNLOADER_TSX.read_text(encoding="utf-8")

    assert "disabled={busy || downloadAllMessages}" in source
    assert "setDownloadAllMessages(event.currentTarget.checked)" in source



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


def test_tauri_api_and_rust_register_download_runtime_session_commands() -> None:
    api_source = TAURI_TS.read_text(encoding="utf-8")
    rust_lib_source = (ROOT / "desktop-tauri" / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    rust_sidecar_source = SIDECAR_RS.read_text(encoding="utf-8")

    for marker in (
        "export type ToolSessionControlAction",
        "export type ToolSessionSnapshot",
        "export function startToolSession(",
        "export function pollToolSession(",
        "export function controlToolSession(",
        "export function cleanupToolSession(",
    ):
        assert marker in api_source

    for marker in (
        "sidecar::start_tool_session",
        "sidecar::poll_tool_session",
        "sidecar::control_tool_session",
        "sidecar::cleanup_tool_session",
    ):
        assert marker in rust_lib_source

    for marker in (
        "pub async fn start_tool_session(",
        "pub async fn poll_tool_session(",
        "pub async fn control_tool_session(",
        "pub async fn cleanup_tool_session(",
        'OsString::from("--control")',
        "write_control_state(",
        "temp_control_path()",
    ):
        assert marker in rust_sidecar_source


def test_video_downloaders_stream_runtime_progress_and_render_queue_controls() -> None:
    web_tool_source = WEB_VIDEO_TSX.read_text(encoding="utf-8")
    tg_tool_source = TG_DOWNLOADER_TSX.read_text(encoding="utf-8")
    queue_state_source = DOWNLOAD_QUEUE_STATE_TS.read_text(encoding="utf-8")
    queue_table_source = (ROOT / "desktop-tauri" / "src" / "features" / "tools" / "components" / "DownloadQueueTable.tsx").read_text(encoding="utf-8")
    hook_source = DOWNLOAD_RUNTIME_HOOK_TS.read_text(encoding="utf-8")
    web_sidecar_source = WEB_SIDECAR_TOOL.read_text(encoding="utf-8")
    tg_sidecar_source = TG_SIDECAR_TOOL.read_text(encoding="utf-8")

    for marker in (
        "startToolSession(",
        "pollToolSession(",
        "controlToolSession(",
        "cleanupToolSession(",
        "const sessionIdRef = useRef<string | null>(null)",
        "const sessionId = sessionIdRef.current",
    ):
        assert marker in hook_source

    for marker in (
        "useDownloadRuntimeSession(",
        "queueRows",
        "queueOverviewFromSession(",
        "进度总览",
        "paused",
        "buildQueueRows(tasks, session, {",
        'progressKinds: ["file", "web_status", "web_aria2", "web_percent"]',
    ):
        assert marker in web_tool_source

    for marker in (
        "useDownloadRuntimeSession(",
        "queueRows",
        "queueOverviewFromSession(",
        "进度总览",
        "paused",
        "buildQueueRows(tasks, session, {",
        'progressKinds: ["file", "tg_media"]',
    ):
        assert marker in tg_tool_source

    for marker in (
        "function markerIndex(",
        "function queueOverviewFromSession(",
        'Number.parseInt(marker.payload.index ?? "", 10)',
        "options.progressKinds.includes(marker.kind)",
        'row.detail = "已完成"',
        'rows[activeIndex].detail = "已暂停"',
        'rows[activeIndex].detail = "已取消"',
    ):
        assert marker in queue_state_source

    assert '"???"' not in web_tool_source
    assert '"???"' not in tg_tool_source

    for marker in (
        "\u53d6\u6d88",
        "\u6682\u505c",
        "\u7ee7\u7eed",
        "\u4e0b\u8f7d\u961f\u5217",
    ):
        assert marker in queue_table_source

    for marker in (
        "emit_runtime_progress",
        "current_download_token",
        "_progress(",
        'kwargs["token"] = current_download_token()',
    ):
        assert marker in web_sidecar_source
        assert marker in tg_sidecar_source


def test_download_queue_state_routes_indexed_progress_to_the_correct_row() -> None:
    rows = _run_download_queue_rows_from_session(
        DOWNLOAD_QUEUE_STATE_TS,
        tasks=[
            {"source_url": "https://example.com/a", "target_title": "Task A"},
            {"source_url": "https://example.com/b", "target_title": "Task B"},
        ],
        session={
            "status": "running",
            "progress_events": [
                {"message": "__HYL_PROGRESS__|task_start|index=0|total=2|url=https://example.com/a"},
                {"message": "__HYL_PROGRESS__|task_start|index=1|total=2|url=https://example.com/b"},
                {"message": "__HYL_PROGRESS__|web_status|index=0|name=a.mp4|percent=25|speed=1.2 MiB/s|eta=00:10"},
                {"message": "__HYL_PROGRESS__|task_done|index=0|completed=1|total=2"},
            ],
        },
    )

    assert rows[0]["fileName"] == "a.mp4"
    assert rows[0]["status"] == "success"
    assert rows[0]["percent"] == 100
    assert rows[1]["status"] == "running"
    assert rows[1]["detail"] == "https://example.com/b"
