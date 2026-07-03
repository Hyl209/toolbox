from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tauri_aiimage_api_types_and_result_shape_exist() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "api" / "tauri.ts").read_text(encoding="utf-8")

    for marker in (
        "export type AiImageProfile",
        "export type AiImageConfig",
        "export type AiImageArtifact",
        "images?: Array<AiImageArtifact>",
    ):
        assert marker in source


def test_tauri_aiimage_panel_is_registered() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "features" / "tools" / "panels.tsx").read_text(encoding="utf-8")

    for marker in (
        'import AiImageTool from "../../tools/AiImageTool";',
        'aiimage: () => <AiImageTool />',
    ):
        assert marker in source


def test_tauri_aiimage_tool_wires_config_generation_preview_and_export() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for marker in (
        'runTool("aiimage"',
        'action: "load_config"',
        'action: "save_config"',
        'action: "generate"',
        "negativePrompt",
        "downloadImage(",
        "downloadAllImages(",
        "open(",
        "image-grid",
    ):
        assert marker in source
