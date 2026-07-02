"""Generate the Tauri tool manifest from the Python tool registry."""
from __future__ import annotations

import ast
import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


try:
    from .runtime_paths import project_root
except ImportError:  # direct script execution support
    from runtime_paths import project_root


ROOT = project_root(__file__, 1)
REGISTRY_PATH = ROOT / "toolbox_app" / "tool_registry.py"
TS_MANIFEST_PATH = ROOT / "desktop-tauri" / "src" / "tools" / "manifest.ts"

TAURI_READY_TOOL_IDS = {
    "base64",
    "batchrename",
    "directdownloader",
    "filesorter",
    "imageconvert",
    "mp4mp3",
    "music",
    "pdftools",
    "same",
    "tgdownloader",
    "webvideodownloader",
    "wordformatter",
    "zipandpng",
}

MANIFEST_METADATA_FIELDS = (
    "sidebar_label",
    "dir_name",
    "converter_file",
    "tab_file",
)


def resolve_tauri_status(tool_id: str) -> str:
    return "ready" if tool_id in TAURI_READY_TOOL_IDS else "pending"


def _load_registry_by_import() -> list[Any]:
    spec = importlib.util.spec_from_file_location("toolbox_app.tool_registry", REGISTRY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load spec for {REGISTRY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return list(module.TOOL_DEFINITIONS)


def _load_registry_by_ast() -> list[dict[str, Any]]:
    source = REGISTRY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(REGISTRY_PATH))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "TOOL_DEFINITIONS" for t in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            break
        tools: list[dict[str, Any]] = []
        fields = ("id", "title", "sidebar_label", "dir_name", "converter_file", "tab_file")
        for item in node.value.elts:
            if not isinstance(item, ast.Call):
                continue
            data: dict[str, Any] = {}
            for name, arg in zip(fields, item.args):
                data[name] = ast.literal_eval(arg)
            for keyword in item.keywords:
                if keyword.arg:
                    data[keyword.arg] = ast.literal_eval(keyword.value)
            tools.append(data)
        return tools
    raise ValueError("TOOL_DEFINITIONS list not found")


def load_tool_definitions() -> list[dict[str, Any]]:
    try:
        tools = _load_registry_by_import()
    except Exception as exc:
        print(f"registry import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return _load_registry_by_ast()
    result: list[dict[str, Any]] = []
    for tool in tools:
        if is_dataclass(tool):
            result.append(asdict(tool))
        elif isinstance(tool, dict):
            result.append(dict(tool))
        else:
            result.append(vars(tool))
    return result


def infer_category(tool: dict[str, Any]) -> str:
    tool_id = str(tool["id"])
    dir_name = str(tool.get("dir_name", ""))
    if tool_id in {"base64", "wordformatter"}:
        return "text"
    if "pdf" in dir_name:
        return "document"
    if "image" in dir_name or "disguise" in dir_name:
        return "image"
    if "audio" in dir_name or "ncm" in dir_name:
        return "audio"
    if "downloader" in dir_name or "video-downloader" in dir_name:
        return "download"
    if any(part in dir_name for part in ("file-sorter", "duplicate-finder", "batch-rename")):
        return "file"
    return "utility"


def build_manifest(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = []
    for tool in tools:
        status = resolve_tauri_status(str(tool["id"]))
        metadata = {field: tool[field] for field in MANIFEST_METADATA_FIELDS if field in tool}
        metadata["extra_files"] = list(tool.get("extra_files") or ())
        metadata["tab_kwargs"] = dict(tool.get("tab_kwargs") or {})
        manifest.append(
            {
                "id": tool["id"],
                "title": tool["title"],
                "category": infer_category(tool),
                "supported_in_tauri": status == "ready",
                "status": status,
                **metadata,
            }
        )
    return manifest


def generate_ts(manifest: list[dict[str, Any]]) -> str:
    body = json.dumps(manifest, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "export type ToolManifestItem = {",
            "  id: string;",
            "  title: string;",
            "  category: string;",
            "  supported_in_tauri: boolean;",
            "  status: 'ready' | 'pending' | 'planned';",
            "  sidebar_label?: string;",
            "  dir_name?: string;",
            "  converter_file?: string;",
            "  tab_file?: string;",
            "  extra_files?: readonly string[];",
            "  tab_kwargs?: Record<string, unknown>;",
            "};",
            "",
            f"export const toolManifest = {body} as const satisfies readonly ToolManifestItem[];",
            "",
            "export default toolManifest;",
            "",
        ]
    )


def write_ts_manifest(manifest: list[dict[str, Any]]) -> None:
    TS_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TS_MANIFEST_PATH.write_text(generate_ts(manifest), encoding="utf-8")


def check_ts_manifest(manifest: list[dict[str, Any]]) -> bool:
    expected = generate_ts(manifest)
    current = TS_MANIFEST_PATH.read_text(encoding="utf-8") if TS_MANIFEST_PATH.exists() else ""
    if current == expected:
        return True
    print(f"stale TypeScript manifest: {TS_MANIFEST_PATH}; run sidecar/tool_manifest.py --write", file=sys.stderr)
    return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tool_manifest.py")
    parser.add_argument("--check", action="store_true", help="print manifest JSON without rewriting TypeScript")
    parser.add_argument("--write", action="store_true", help="rewrite TypeScript manifest")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    manifest = build_manifest(load_tool_definitions())
    if args.write or not args.check:
        write_ts_manifest(manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if args.check and not check_ts_manifest(manifest):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
