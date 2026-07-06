from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "desktop-tauri" / "src" / "tools"
COMMON_PARTS = ROOT / "desktop-tauri" / "src" / "features" / "tools" / "components" / "CommonToolParts.tsx"


def test_tauri_tool_pages_do_not_render_static_helper_microcopy() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in TOOLS_DIR.glob("*.tsx"))
    shared_parts = COMMON_PARTS.read_text(encoding="utf-8")

    stale_copy = (
        "文本和文件互转。",
        "识别并解压压缩包。",
        "预览后批量重命名。",
        "格式化和转换 CSV。",
        "计算并校验。",
        "粘贴真实直链，先校验，再直接下载。",
        "批量转换图片格式。",
        "按类别整理文件。",
        "格式化和校验 JSON。",
        "将 NCM 转为 MP3。",
        "从 MP4 提取音频。",
        "合并、拆分和导出 PDF。",
        "测试正则并提取文本。",
        "查找重复文件。",
        "清理和转换文本。",
        "下载 Telegram 链接。",
        "转换时间和时间戳。",
        "处理 URL 和参数。",
        "生成和校验 UUID。",
        "把文件藏进图片。",
        "下载网页视频。",
        "统一 Word 文档排版。",
        "先校验，再下载。",
        "选择图片和格式后开始。",
        "预览只读取摘要；执行会创建分类目录并移动文件。",
        "文件后转换。",
        "每个 MP4 输出同名 MP3。",
        "按当前模式处理 PDF。",
        "选择文档和输出方式。",
        "预览不会改动文件；执行前请确认目标名。",
        "重复结果以旧 converter 的 keeper / duplicates 为准。",
        "任意文件 → 图片伪装",
        "伪装图片 → 原始文件",
        "Plain text → Base64",
        "Base64 → Plain text",
    )
    for copy in stale_copy:
        assert copy not in combined

    assert "{description ? <p>{description}</p> : null}" in shared_parts
    assert "{hint ? <div className=\"action-hint\">{hint}</div> : null}" in shared_parts
