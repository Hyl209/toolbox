#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

try:
    from ncmdump import dump
except ModuleNotFoundError:
    dump = None


def probe_converter_backend() -> tuple[bool, str]:
    if dump is None:
        return False, 'ncmdump is not installed in this Python environment'
    return True, ''


def collect_ncm_files(input_path: Path) -> list[Path]:
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    if input_path.is_file():
        if input_path.suffix.lower() != ".ncm":
            raise ValueError(f"Input file is not .ncm: {input_path}")
        return [input_path]
    return sorted(p.resolve() for p in input_path.rglob("*.ncm") if p.is_file())


def collect_input_paths(paths: list[Path]) -> list[Path]:
    unique: dict[Path, None] = {}
    for path in paths:
        for item in collect_ncm_files(Path(path)):
            unique[item.resolve()] = None
    return sorted(unique.keys())


def convert_file(src: Path, output_dir: Path | None = None, overwrite: bool = False) -> Path:
    available, message = probe_converter_backend()
    if not available:
        raise RuntimeError(message)
    src = src.resolve()
    if output_dir is None:
        target = src.with_suffix('.mp3')
    else:
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / f"{src.stem}.mp3"
    if target.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {target}")
    result = dump(str(src), str(target), skip=False)
    return Path(result or target)


def convert_many(files: list[Path], output_dir: Path, overwrite: bool = False) -> list[tuple[Path, Path]]:
    results = []
    for file in files:
        out = convert_file(file, output_dir=output_dir, overwrite=overwrite)
        results.append((file.resolve(), out.resolve()))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert NetEase .ncm files to mp3")
    parser.add_argument("input", help="Path to .ncm file or directory")
    parser.add_argument("-o", "--output-dir", help="Directory for converted mp3 files")
    parser.add_argument("--dry-run", action="store_true", help="Only list matched .ncm files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing mp3 files")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_path = Path(args.input)
        files = collect_ncm_files(input_path)
        if not files:
            print("No .ncm files found.")
            return 1

        for file in files:
            print(f"FOUND {file}")

        if args.dry_run:
            return 0

        output_dir = Path(args.output_dir) if args.output_dir else None
        if output_dir is None:
            for file in files:
                out = convert_file(file, output_dir=None, overwrite=args.overwrite)
                print(f"OK {file} -> {out}")
        else:
            for src, out in convert_many(files, output_dir=output_dir, overwrite=args.overwrite):
                print(f"OK {src} -> {out}")
        return 0
    except (FileNotFoundError, ValueError, FileExistsError, AssertionError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
