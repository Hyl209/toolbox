"""CLI entrypoint for the HYL Python sidecar."""
from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path

try:
    from .protocol import emit_error, emit_progress, emit_result
    from .settings_bridge import (
        DEFAULT_PLUGINS_DIR,
        DEFAULT_SETTINGS,
        SettingsUpdateError,
        apply_settings_update,
        build_settings_snapshot,
    )
    from .tools.batchrename_tool import run_batchrename
    from .tools.base64_tool import run_base64
    from .tools.directdownloader_tool import run_directdownloader
    from .tools.filesorter_tool import run_filesorter
    from .tools.imageconvert_tool import run_imageconvert
    from .tools.mp4mp3_tool import run_mp4mp3
    from .tools.music_tool import run_music
    from .tools.pdftools_tool import run_pdftools
    from .tools.plugin_archive_extractor import run_plugin_archive_extractor
    from .tools.plugin_file_hasher import run_plugin_file_hasher
    from .tools.plugin_json_tools import run_plugin_json_tools
    from .tools.plugin_csv_tools import run_plugin_csv_tools
    from .tools.plugin_regex_tools import run_plugin_regex_tools
    from .tools.plugin_text_tools import run_plugin_text_tools
    from .tools.plugin_timestamp_tools import run_plugin_timestamp_tools
    from .tools.plugin_url_tools import run_plugin_url_tools
    from .tools.plugin_uuid_tools import run_plugin_uuid_tools
    from .tools.same_tool import run_same
    from .tools.tgdownloader_tool import run_tgdownloader
    from .tools.webvideodownloader_tool import run_webvideodownloader
    from .tools.wordformatter_tool import run_wordformatter
    from .tools.zipandpng_tool import run_zipandpng
except ImportError:  # direct script execution: python sidecar\hyl_sidecar.py
    from protocol import emit_error, emit_progress, emit_result
    from settings_bridge import (
        DEFAULT_PLUGINS_DIR,
        DEFAULT_SETTINGS,
        SettingsUpdateError,
        apply_settings_update,
        build_settings_snapshot,
    )
    from tools.batchrename_tool import run_batchrename
    from tools.base64_tool import run_base64
    from tools.directdownloader_tool import run_directdownloader
    from tools.filesorter_tool import run_filesorter
    from tools.imageconvert_tool import run_imageconvert
    from tools.mp4mp3_tool import run_mp4mp3
    from tools.music_tool import run_music
    from tools.pdftools_tool import run_pdftools
    from tools.plugin_archive_extractor import run_plugin_archive_extractor
    from tools.plugin_file_hasher import run_plugin_file_hasher
    from tools.plugin_json_tools import run_plugin_json_tools
    from tools.plugin_csv_tools import run_plugin_csv_tools
    from tools.plugin_regex_tools import run_plugin_regex_tools
    from tools.plugin_text_tools import run_plugin_text_tools
    from tools.plugin_timestamp_tools import run_plugin_timestamp_tools
    from tools.plugin_url_tools import run_plugin_url_tools
    from tools.plugin_uuid_tools import run_plugin_uuid_tools
    from tools.same_tool import run_same
    from tools.tgdownloader_tool import run_tgdownloader
    from tools.webvideodownloader_tool import run_webvideodownloader
    from tools.wordformatter_tool import run_wordformatter
    from tools.zipandpng_tool import run_zipandpng


class SidecarError(Exception):
    def __init__(self, code: str, message: str, task_id: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.task_id = task_id


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="hyl_sidecar.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--tool", required=True)
    run.add_argument("--input", required=True)
    settings = subparsers.add_parser("settings")
    mode = settings.add_mutually_exclusive_group(required=True)
    mode.add_argument("--snapshot", action="store_true")
    mode.add_argument("--update", action="store_true")
    settings.add_argument("--input")
    settings.add_argument("--settings", default=str(DEFAULT_SETTINGS))
    settings.add_argument("--plugins-dir", default=str(DEFAULT_PLUGINS_DIR))
    return parser.parse_args(argv)


def load_task(path: Path) -> dict:
    if not path.exists():
        raise SidecarError("INPUT_NOT_FOUND", "input file not found")
    try:
        task = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SidecarError("INVALID_JSON", "invalid JSON input") from exc
    if not isinstance(task, dict):
        raise SidecarError("INVALID_JSON", "invalid JSON input")
    return task


def run_tool(tool_id: str, input_path: Path) -> int:
    task = load_task(input_path)
    task_id = task.get("task_id")
    runners = {
        "batchrename": run_batchrename,
        "base64": run_base64,
        "directdownloader": run_directdownloader,
        "filesorter": run_filesorter,
        "imageconvert": run_imageconvert,
        "mp4mp3": run_mp4mp3,
        "music": run_music,
        "pdftools": run_pdftools,
        "plugin:archive_extractor": run_plugin_archive_extractor,
        "plugin:csv_tools": run_plugin_csv_tools,
        "plugin:file_hasher": run_plugin_file_hasher,
        "plugin:json_tools": run_plugin_json_tools,
        "plugin:regex_tools": run_plugin_regex_tools,
        "plugin:text_tools": run_plugin_text_tools,
        "plugin:timestamp_tools": run_plugin_timestamp_tools,
        "plugin:url_tools": run_plugin_url_tools,
        "plugin:uuid_tools": run_plugin_uuid_tools,
        "same": run_same,
        "tgdownloader": run_tgdownloader,
        "webvideodownloader": run_webvideodownloader,
        "wordformatter": run_wordformatter,
        "zipandpng": run_zipandpng,
    }
    runner = runners.get(tool_id)
    if runner is None:
        emit_error(task_id, "UNKNOWN_TOOL", f"unknown tool: {tool_id}")
        return 1
    emit_progress(task_id, "started", 0)
    result = runner(task)
    if result.get("ok") is False:
        emit_error(task_id, result.get("code", "TOOL_ERROR"), result.get("message", "tool failed"))
        return 1
    emit_result(task_id, result.get("data", {}))
    return 0


def run_settings_update(input_path: Path, settings_path: Path, plugins_dir: Path) -> int:
    task = load_task(input_path)
    task_id = task.get("task_id")
    updates = task.get("updates", task)
    try:
        snapshot = apply_settings_update(
            updates,
            settings_path=settings_path,
            plugins_dir=plugins_dir,
        )
    except SettingsUpdateError as exc:
        emit_error(task_id, "INVALID_SETTINGS_UPDATE", str(exc))
        return 1
    emit_result(task_id, snapshot)
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        args = parse_args(argv if argv is not None else sys.argv[1:])
        if args.command == "run":
            return run_tool(args.tool, Path(args.input))
        if args.command == "settings":
            settings_path = Path(args.settings)
            plugins_dir = Path(args.plugins_dir)
            if args.update:
                if not args.input:
                    raise SidecarError("INPUT_REQUIRED", "settings update requires --input")
                return run_settings_update(Path(args.input), settings_path, plugins_dir)
            emit_result(
                None,
                build_settings_snapshot(
                    settings_path=settings_path,
                    plugins_dir=plugins_dir,
                ),
            )
            return 0
        emit_error(None, "UNKNOWN_COMMAND", f"unknown command: {args.command}")
        return 1
    except SidecarError as exc:
        emit_error(exc.task_id, exc.code, exc.message)
        return 1
    except Exception as exc:
        emit_error(None, "INTERNAL_ERROR", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
