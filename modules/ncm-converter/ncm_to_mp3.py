#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from pathlib import Path

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import APIC
except ModuleNotFoundError:
    MutagenFile = None
    APIC = None

try:
    from ncmdump import dump
except ModuleNotFoundError:
    dump = None


SUPPORTED_IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
DEFAULT_COVER_MIME = 'image/jpeg'


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


def _read_ncm_metadata_block(src: Path) -> dict:
    data = src.read_bytes()
    marker = b'music:'
    start = data.find(marker)
    if start == -1:
        return {}
    brace_start = data.find(b'{', start)
    if brace_start == -1:
        return {}
    depth = 0
    in_string = False
    escape = False
    for index in range(brace_start, len(data)):
        byte = data[index]
        if in_string:
            if escape:
                escape = False
            elif byte == 0x5C:
                escape = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte == 0x7B:
            depth += 1
        elif byte == 0x7D:
            depth -= 1
            if depth == 0:
                payload = data[brace_start:index + 1]
                try:
                    return json.loads(payload.decode('utf-8', errors='ignore'))
                except json.JSONDecodeError:
                    return {}
    return {}


def _guess_mime_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == '.png':
        return 'image/png'
    if suffix == '.webp':
        return 'image/webp'
    if suffix == '.gif':
        return 'image/gif'
    if suffix == '.bmp':
        return 'image/bmp'
    return DEFAULT_COVER_MIME


def _extract_cover_info(src: Path, metadata: dict) -> dict[str, str]:
    album_pic = metadata.get('albumPic')
    if isinstance(album_pic, str) and album_pic.strip().startswith('data:image'):
        return {'cover_data_url': album_pic.strip()}
    candidates: list[Path] = []
    candidates.append(src.with_suffix('.jpg'))
    candidates.extend(src.with_suffix(ext) for ext in SUPPORTED_IMAGE_SUFFIXES if ext != '.jpg')
    candidates.extend(src.parent.glob('AlbumArt*'))
    candidates.extend(src.parent.glob('Folder*'))
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
            encoded = base64.b64encode(candidate.read_bytes()).decode('ascii')
            mime = _guess_mime_from_path(candidate)
            return {'cover_data_url': f'data:{mime};base64,{encoded}'}
    return {'cover_data_url': ''}


def _read_mp3_tag_info(mp3_path: Path) -> dict[str, str]:
    if MutagenFile is None:
        return {}
    try:
        audio = MutagenFile(mp3_path)
    except Exception:
        return {}
    if audio is None:
        return {}
    result: dict[str, str] = {}
    try:
        title = audio.get('TIT2')
        if title:
            result['title'] = str(title)
    except Exception:
        pass
    try:
        artist = audio.get('TPE1')
        if artist:
            result['artist'] = str(artist)
    except Exception:
        pass
    try:
        apic = audio.get('APIC:') or audio.get('APIC')
        if apic and getattr(apic, 'data', None):
            mime = getattr(apic, 'mime', DEFAULT_COVER_MIME) or DEFAULT_COVER_MIME
            encoded = base64.b64encode(apic.data).decode('ascii')
            result['cover_data_url'] = f'data:{mime};base64,{encoded}'
    except Exception:
        pass
    return result


def enrich_song_info_from_mp3(item: dict[str, str], mp3_path: Path) -> dict[str, str]:
    enriched = dict(item)
    tag_info = _read_mp3_tag_info(mp3_path.resolve())
    if not tag_info:
        return enriched
    title = str(tag_info.get('title') or enriched.get('title') or Path(str(enriched.get('file_path', ''))).stem).strip()
    artist = str(tag_info.get('artist') or enriched.get('artist') or '').strip()
    enriched['title'] = title
    enriched['artist'] = artist
    enriched['display_name'] = f'{title} - {artist}' if artist else title
    if tag_info.get('cover_data_url'):
        enriched['cover_data_url'] = str(tag_info['cover_data_url'])
    return enriched


def extract_song_info(src: Path) -> dict[str, str]:
    src = src.resolve()
    metadata = _read_ncm_metadata_block(src)
    title = str(metadata.get('musicName') or src.stem).strip() or src.stem
    artists = metadata.get('artist') or []
    artist_names: list[str] = []
    if isinstance(artists, list):
        for item in artists:
            if isinstance(item, list) and item:
                artist_names.append(str(item[0]).strip())
            elif isinstance(item, str):
                artist_names.append(item.strip())
    artist_text = ' / '.join(name for name in artist_names if name)
    info = {
        'file_path': str(src),
        'title': title,
        'artist': artist_text,
        'display_name': f'{title} - {artist_text}' if artist_text else title,
    }
    info.update(_extract_cover_info(src, metadata))
    return info


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
