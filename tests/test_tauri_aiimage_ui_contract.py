from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tauri_aiimage_api_types_and_result_shape_exist() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "api" / "tauri.ts").read_text(encoding="utf-8")

    for marker in (
        "export type AiImageProfile",
        "export type AiImageConfig",
        "export type AiImageArtifact",
        "export type AiImageHistoryItem",
        "images?: Array<AiImageArtifact>",
        "referenceImages?: string[]",
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
        "pickFiles",
        'runTool("aiimage"',
        'action: "load_config"',
        'action: "save_config"',
        'action: "generate"',
        "negativePrompt",
        "referenceImages",
        "reference_image_paths",
        "chooseReferenceImages",
        "removeReferenceImage",
        "function referenceImageSrc(path: string): string {\n  return localImageSrc(path);\n}",
        "downloadImage(",
        "downloadAllImages(",
        "open(",
        "image-grid",
    ):
        assert marker in source


def test_tauri_aiimage_reference_previews_use_asset_protocol_scope() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    tauri_config = (ROOT / "desktop-tauri" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")

    assert "function referenceImageSrc(path: string): string {\n  return localImageSrc(path);\n}" in source
    assert '"$HOME/**/*"' in tauri_config


def test_tauri_aiimage_reference_actions_stay_on_one_row() -> None:
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        ".aiimage-reference-head > span {\n  flex: 0 0 auto;\n  white-space: nowrap;",
        ".aiimage-reference-head .button-cluster {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(76px, 1fr));\n  width: min(100%, 176px);\n}",
        ".aiimage-control-rail .aiimage-reference-head .button-cluster button {\n  min-height: 34px;\n}",
        ".aiimage-control-rail .aiimage-reference-head .button-cluster {\n    grid-template-columns: repeat(2, minmax(0, 1fr));\n  }",
    ):
        assert marker in styles


def test_tauri_aiimage_tool_hides_profile_fields_in_modal_and_prioritizes_prompt_area() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        "isProfileModalOpen",
        "openCreateProfileModal",
        "openEditProfileModal",
        "profile-modal",
        "profileDraft",
        "saveProfileModal",
        "prompt-main-panel",
        "prompt-side-panel",
        "isSizeModalOpen",
        "sizeMode",
        "quality",
        "outputFormat",
        "background",
        "moderation",
        "generationTasks",
        "selectedTaskId",
        "reuseTaskConfig",
        "task-detail-modal",
        "generation-card",
    ):
        assert marker in source

    for marker in (
        ".profile-modal",
        ".profile-modal-card",
        ".prompt-main-panel",
        ".prompt-main-panel textarea",
        ".prompt-side-panel",
        ".size-modal",
        ".size-chip-grid",
        ".generation-history-grid",
        ".generation-card",
        ".task-detail-modal",
    ):
        assert marker in styles


def test_tauri_aiimage_profile_picker_sits_above_three_horizontal_actions() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        'className="file-mode-card compact-card aiimage-profile-strip"',
        'className="button-cluster aiimage-profile-actions"',
    ):
        assert marker in source

    for marker in (
        ".aiimage-profile-strip {\n  gap: 12px;\n  grid-template-columns: minmax(0, 1fr);\n}",
        ".aiimage-profile-actions {\n  display: grid;\n  grid-template-columns: repeat(3, minmax(0, 1fr));\n  width: 100%;\n}",
        "@media (max-width: 1180px)",
        ".aiimage-studio-grid {\n    grid-template-columns: minmax(320px, 380px) minmax(0, 1fr);\n  }",
        ".aiimage-control-rail .button-cluster {\n    grid-template-columns: 1fr;\n  }",
        ".aiimage-control-rail .aiimage-profile-actions {\n    grid-template-columns: repeat(3, minmax(0, 1fr));\n  }",
    ):
        assert marker in styles

    assert ".aiimage-profile-strip {\n  gap: 12px;\n  grid-template-columns: minmax(0, 1fr) auto;" not in styles


def test_tauri_aiimage_removes_static_helper_microcopy() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    shared_parts = (ROOT / "desktop-tauri" / "src" / "features" / "tools" / "components" / "CommonToolParts.tsx").read_text(encoding="utf-8")

    for stale_copy in (
        "参数区参考 GPT Image Playground 的工作台节奏",
        "生成成功后会自动保存到时间戳子目录",
        "先写提示词，再按需调参数",
        "右侧专注预览和历史结果",
        "低频配置项收在弹窗里",
        "不同模型传递具体分辨率参数",
        "任务详情",
    ):
        assert stale_copy not in source

    assert "{description ? <p>{description}</p> : null}" in shared_parts
    assert "{hint ? <div className=\"action-hint\">{hint}</div> : null}" in shared_parts


def test_tauri_aiimage_default_background_maps_to_backend_enum() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    assert 'background: taskInput.background === "true" ? "transparent" : "auto"' in source
    assert 'background: taskInput.background === "true" ? "transparent" : "false"' not in source


def test_tauri_aiimage_1k_ratio_presets_match_required_dimensions() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    expected_pairs = {
        '"1:1": "1024x1024"',
        '"3:2": "1536x1024"',
        '"2:3": "1024x1536"',
        '"16:9": "1280x720"',
        '"9:16": "720x1280"',
        '"4:3": "1024x768"',
        '"3:4": "768x1024"',
        '"21:9": "1920x816"',
    }
    for marker in expected_pairs:
        assert marker in source

    assert "const RATIO_SIZE_PRESETS" in source
    assert "sizeFromRatio(ratio: RatioOption): string" in source

    for unsupported in ("4096x4096", "BASE_RESOLUTION_PIXELS"):
        assert unsupported not in source


def test_tauri_aiimage_tool_exposes_compression_elapsed_and_task_summary() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        "outputCompression",
        "output_compression",
        "taskElapsedLabel",
        "taskParamSummary",
        "aiimage-task-footer",
    ):
        assert marker in source

    for marker in (
        ".aiimage-compression-field",
        ".aiimage-task-footer",
        ".generation-card-status",
    ):
        assert marker in styles


def test_tauri_aiimage_task_summary_has_no_visible_question_mark_placeholders() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for bad_marker in (
        '`${Math.floor(seconds / 60)}?${seconds % 60}?`',
        '`${seconds}?`',
        '` ? ?? ${task.outputCompression}`',
        'return `${task.size} ? ${task.quality}',
        'return "???..."',
        'task.error || "????"',
        'return `?? ? ${taskElapsedLabel(task)}`',
        '<span>??</span>',
        '`${task.images.length} ?`',
    ):
        assert bad_marker not in source

    for marker in (
        "秒",
        "分",
        "压缩",
        "耗时",
        'return `生成中 ${taskElapsedLabel(task, now)}`',
        "张",
    ):
        assert marker in source


def test_tauri_aiimage_tool_loads_and_manages_persistent_history() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for marker in (
        "historyId",
        "id: next.historyId || task.id",
        'action: "load_history"',
        'action: "delete_history"',
        'action: "clear_history"',
        "loadHistory",
        "deleteTask",
        "clearHistory",
        "AiImageHistoryItem",
    ):
        assert marker in source


def test_tauri_aiimage_size_modal_keeps_draft_state_until_confirmed() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for marker in (
        "draftSizeMode",
        "draftSelectedRatio",
        "draftSelectedBaseResolution",
        "draftCustomWidth",
        "draftCustomHeight",
        "setDraftSizeMode",
        "applyDraftRatioSize",
        "confirmSizeModal",
    ):
        assert marker in source

    for bad_marker in (
        'onClick={() => setSizeMode("auto")}',
        "onClick={() => applyRatioSize(selectedRatio, base)}",
        "onClick={() => applyRatioSize(preset.value, selectedBaseResolution)}",
    ):
        assert bad_marker not in source


def test_tauri_aiimage_tool_defaults_to_gpt_image_2_and_uses_reference_size_picker_shape() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for marker in (
        'model: "gpt-image-2"',
        "BASE_RESOLUTION_OPTIONS",
        "selectedBaseResolution",
        "sizeFromBaseAndRatio",
        "size-base-grid",
        "size-ratio-grid",
        '"2880x2880"',
    ):
        assert marker in source

    for bad_marker in ("const SIZE_PRESETS", "applyPresetSize"):
        assert bad_marker not in source


def test_tauri_aiimage_tool_matches_reference_source_size_table() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    for marker in (
        "SIZE_BY_BASE_AND_RATIO",
        '"2K": {',
        '"3:2": "2160x1440"',
        '"21:9": "3120x1344"',
        '"4K": {',
        '"1:1": "2880x2880"',
        '"3:2": "3456x2304"',
        '"4:3": "3200x2400"',
        '"21:9": "3840x1648"',
    ):
        assert marker in source

    for wrong_marker in ('"2K" ? "2048x2048"', 'MAX_4K_PIXELS * ratioWidth'):
        assert wrong_marker not in source


def test_tauri_aiimage_results_canvas_uses_compact_container_driven_thumbnail_grid() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    assert '<div className="aiimage-empty-state">\n              <div className="empty-orb" aria-hidden="true" />' not in source

    for marker in (
        "container-type: inline-size;",
        "@container (min-width: 720px)",
        "grid-template-columns: minmax(0, 1fr);",
        "grid-template-columns: repeat(2, minmax(0, 1fr));",
        "aspect-ratio: 1 / 1;",
    ):
        assert marker in styles


def test_tauri_aiimage_history_cards_use_compact_horizontal_thumbnail_layout() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        'className="generation-history-grid"',
        'className="generation-card"',
        'className="generation-card-preview"',
        'className="generation-card-body"',
    ):
        assert marker in source

    for marker in (
        ".generation-history-grid {\n  display: grid;\n  align-content: start;\n  gap: 12px;\n  grid-auto-rows: max-content;\n  grid-template-columns: minmax(0, 1fr);",
        ".aiimage-stage .generation-card {\n  display: grid;\n  grid-template-columns: 148px minmax(0, 1fr);",
        ".aiimage-stage .generation-card-preview {\n  position: relative;",
        ".generation-card-placeholder {\n  display: grid;\n  place-items: center;",
    ):
        assert marker in styles


def test_tauri_aiimage_history_preview_keeps_square_shape_when_text_is_long() -> None:
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        ".aiimage-stage .generation-card {\n  display: grid;\n  grid-template-columns: 148px minmax(0, 1fr);\n  height: 148px;",
        ".aiimage-stage .generation-card-preview {\n  position: relative;\n  width: 148px;\n  height: 148px;",
        ".aiimage-stage .generation-card-preview {\n  position: relative;\n  aspect-ratio: 1 / 1;",
    ):
        if "aspect-ratio" in marker:
            assert marker not in styles
        else:
            assert marker in styles


def test_tauri_aiimage_task_detail_adapts_preview_to_image_resolution() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        "imageDetailLayout",
        "--task-detail-image-aspect",
        "--task-detail-media-column",
        "data-image-orientation={taskDetailLayout.orientation}",
        "style={taskDetailLayout.style}",
    ):
        assert marker in source

    for marker in (
        ".task-detail-card {\n  display: grid;\n  grid-template-columns: minmax(260px, var(--task-detail-media-column, 440px)) minmax(320px, 1fr);\n  width: min(var(--task-detail-width, 960px), calc(100vw - 64px));\n  max-height: min(760px, calc(100vh - 64px));",
        ".task-detail-media {\n  min-height: 0;\n  max-height: min(760px, calc(100vh - 64px));\n  aspect-ratio: var(--task-detail-image-aspect, 1 / 1);",
        "  box-sizing: border-box;\n  padding: 15px;",
        ".task-detail-media img {\n  display: block;\n  width: 100%;\n  height: 100%;\n  object-fit: contain;",
        ".task-detail-content {\n  display: grid;\n  gap: 10px;\n  align-content: start;\n  min-height: 0;\n  overflow: auto;\n  padding: 16px;",
        ".task-detail-content > .result-card {\n  justify-content: flex-start;\n  min-height: 104px;\n  padding: 14px 16px;\n  border-radius: 12px;",
        ".aiimage-task-meta-grid .result-card {\n  min-height: 76px;\n  padding: 12px 14px;",
    ):
        assert marker in styles

    assert "grid-template-columns: minmax(280px, 360px)" not in styles
    assert "width: 360px;" not in styles
    assert "max-height: 320px;" not in styles


def test_tauri_aiimage_results_do_not_duplicate_history_with_large_image_grid() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")

    assert "{images.length && !generationTasks.length ? (" in source
    assert "{images.length ? (\n            <div className=\"image-grid\">" not in source


def test_tauri_aiimage_preview_uses_asset_protocol_for_local_files() -> None:
    source = (ROOT / "desktop-tauri" / "src" / "tools" / "AiImageTool.tsx").read_text(encoding="utf-8")
    tauri_conf = json.loads((ROOT / "desktop-tauri" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))

    assert 'import { convertFileSrc } from "@tauri-apps/api/core";' in source
    assert "convertFileSrc(path)" in source
    assert "src={localImageSrc(task.images[0].path)}" in source
    assert "src={localImageSrc(image.path)}" in source
    assert "fileUrl(task.images[0].path)" not in source
    assert "$HOME/Pictures/Hyl Toolbox/AI Images/**/*" in tauri_conf["app"]["security"]["assetProtocol"]["scope"]


def test_tauri_aiimage_history_grid_keeps_result_cards_tightly_stacked() -> None:
    styles = (ROOT / "desktop-tauri" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        ".generation-history-grid {\n  display: grid;\n  align-content: start;\n  gap: 12px;",
        "grid-auto-rows: max-content;",
    ):
        assert marker in styles
