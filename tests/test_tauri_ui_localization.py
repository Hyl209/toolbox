from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS: dict[str, tuple[str, ...]] = {
    "desktop-tauri/src/App.tsx": ("Hyl Toolbox",),
    "desktop-tauri/src/features/settings/sections/SettingsSummarySection.tsx": ("browser-preview",),
    "desktop-tauri/src/features/tools/components/CommonToolParts.tsx": ('<span>Runtime</span>',),
    "desktop-tauri/src/tools/ArchiveExtractorPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/CsvToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/FileHasherPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/ImageConvertTool.tsx": ("Converted files", "Detected files"),
    "desktop-tauri/src/tools/JsonToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/Mp4Mp3Tool.tsx": ("Converted files", "Detected files"),
    "desktop-tauri/src/tools/MusicTool.tsx": ("Converted files", "Detected files"),
    "desktop-tauri/src/tools/RegexToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/TextToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/TgDownloaderTool.tsx": ('<span>Session path</span>', '>Files</div>', 'aria-label="Runtime"', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/TimestampToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/UrlToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/UuidToolsPluginTool.tsx": ('<p className="eyebrow">Plugin - ', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/WebVideoDownloaderTool.tsx": ('{"Proxy Host"}', '{"Proxy Port"}', '{"Concurrent"}', 'aria-label="Runtime"', '<div className="panel-title">Runtime</div>'),
    "desktop-tauri/src/tools/WordFormatterTool.tsx": ("Word outputs",),
    "desktop-tauri/src/tools/ZipPngTool.tsx": ('<div className="panel-title">Runtime</div>',),
}

LOG_LOCALIZATION_TARGETS: dict[str, tuple[str, ...]] = {
    "desktop-tauri/src/features/tools/components/CommonToolParts.tsx": (
        "有错误",
        "暂无日志",
        "选择",
    ),
    "desktop-tauri/src/tools/BatchRenameTool.tsx": (
        'aria-label="运行日志"',
        "最近 5 条",
        "暂无日志",
    ),
    "desktop-tauri/src/tools/SameTool.tsx": (
        '<div className="panel-title">Runtime</div>',
        "最近 5 条",
        "暂无日志",
    ),
    "desktop-tauri/src/tools/TgDownloaderTool.tsx": (
        "暂无日志",
        "最近的 TG sidecar 调用记录",
    ),
    "desktop-tauri/src/tools/WebVideoDownloaderTool.tsx": (
        "暂无日志",
        "未知来源",
    ),
    "desktop-tauri/src/tools/ZipPngTool.tsx": (
        'aria-label="运行日志"',
        "最近 5 条",
        "暂无日志",
    ),
}


def test_tauri_ui_visible_english_residue_is_removed() -> None:
    residues: list[str] = []

    for relative_path, banned_strings in TARGETS.items():
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        for item in banned_strings:
            if item in text:
                residues.append(f"{relative_path} -> {item}")

    assert not residues, "仍有可见英文残留:\n" + "\n".join(residues)


def test_tauri_ui_log_panels_are_localized() -> None:
    residues: list[str] = []

    for relative_path, banned_strings in LOG_LOCALIZATION_TARGETS.items():
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        for item in banned_strings:
            if item in text:
                residues.append(f"{relative_path} -> {item}")

    assert not residues, "日志面板仍有未汉化/乱码文案:\n" + "\n".join(residues)
