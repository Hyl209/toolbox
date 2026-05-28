from __future__ import annotations

import sys
from pathlib import Path

from config_store import clear_default_output_dir, get_default_output_dir, set_default_output_dir
from converter import ConvertError, convert_mp4_to_mp3


def print_help() -> None:
    print(
        '用法:\n'
        '  直接拖拽转换: python app.py <input.mp4> [output.mp3或输出目录]\n'
        '  设置默认输出目录: python app.py --set-output-dir <目录>\n'
        '  查看默认输出目录: python app.py --show-output-dir\n'
        '  清除默认输出目录: python app.py --clear-output-dir\n'
    )


def main(argv: list[str]) -> int:
    if not argv:
        print_help()
        return 1

    cmd = argv[0]
    if cmd == '--set-output-dir':
        if len(argv) < 2:
            print('缺少目录参数')
            return 1
        out_dir = set_default_output_dir(argv[1])
        print(f'默认输出目录已设置为: {out_dir}')
        return 0

    if cmd == '--show-output-dir':
        out_dir = get_default_output_dir()
        print(out_dir if out_dir else '当前未设置默认输出目录')
        return 0

    if cmd == '--clear-output-dir':
        clear_default_output_dir()
        print('默认输出目录已清除')
        return 0

    input_path = argv[0]
    output_path = argv[1] if len(argv) > 1 else None

    try:
        result = convert_mp4_to_mp3(input_path, output_path)
    except ConvertError as e:
        print(f'转换失败: {e}')
        return 1
    except Exception as e:
        print(f'发生未知错误: {e}')
        return 1

    print(f'转换成功: {result}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
