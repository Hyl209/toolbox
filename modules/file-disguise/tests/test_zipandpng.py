import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / 'zipandpng.py'
PYTHON = sys.executable

PNG_BASE64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+yF9sAAAAASUVORK5CYII='
)
JPEG_BASE64 = (
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBAQEA8QDw8PDw8QDw8PDw8QDxAQFREWFhURFRUYHSggGBolGxUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDQ0NDg0NDisZFRkrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrK//AABEIAAEAAQMBIgACEQEDEQH/xAAXAAEBAQEAAAAAAAAAAAAAAAAAAQID/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEAMQAAAB6A//xAAVEAEBAAAAAAAAAAAAAAAAAAAQIf/aAAgBAQABBQJf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAwEBPwEf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwEf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQAGPwJf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQABPyFf/9k='
)
GIF_BASE64 = 'R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs='
WEBP_BASE64 = 'UklGRjwAAABXRUJQVlA4IDAAAADQAQCdASoBAAEAAUAmJaACdLoB+AADsAD+8ut//NgVzXPv9//S4P0uD9Lg/9KQAAA='


def run_cli(*args):
    return subprocess.run(
        [PYTHON, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def write_base64(path, encoded):
    import base64

    path.write_bytes(base64.b64decode(encoded))


def test_disguise_command_requires_existing_cover_image(tmp_path):
    image_path = tmp_path / 'missing.png'
    payload_path = tmp_path / 'payload.exe'
    out_path = tmp_path / 'out.png'

    result = run_cli('disguise', str(image_path), str(payload_path), str(out_path))

    assert result.returncode == 1
    assert '输入图片不存在' in result.stderr


def test_info_command_reports_no_payload_for_plain_png(tmp_path):
    png_path = tmp_path / 'plain.png'
    write_base64(png_path, PNG_BASE64)

    result = run_cli('info', str(png_path))

    assert result.returncode == 0
    assert '未发现附加文件' in result.stdout


def test_disguise_recover_and_info_roundtrip_for_single_file(tmp_path):
    png_path = tmp_path / 'cover.png'
    write_base64(png_path, PNG_BASE64)

    payload_path = tmp_path / 'payload.exe'
    payload_bytes = bytes(range(32)) + b'hello daddy exe'
    payload_path.write_bytes(payload_bytes)

    disguised_path = tmp_path / 'disguised.png'
    recovered_path = tmp_path / 'recovered.exe'

    disguise_result = run_cli('disguise', str(png_path), str(payload_path), str(disguised_path))
    assert disguise_result.returncode == 0, disguise_result.stderr
    assert disguised_path.exists()

    info_result = run_cli('info', str(disguised_path))
    assert info_result.returncode == 0, info_result.stderr
    assert '发现附加文件' in info_result.stdout
    assert 'payload.exe' in info_result.stdout
    assert str(len(payload_bytes)) in info_result.stdout

    recover_result = run_cli('recover', str(disguised_path), str(recovered_path))
    assert recover_result.returncode == 0, recover_result.stderr
    assert recovered_path.read_bytes() == payload_bytes


def test_legacy_merge_and_extract_aliases_still_work(tmp_path):
    png_path = tmp_path / 'cover.png'
    write_base64(png_path, PNG_BASE64)

    payload_path = tmp_path / 'payload.bin'
    payload_path.write_bytes(b'legacy-alias-data')

    disguised_path = tmp_path / 'legacy.png'
    recovered_path = tmp_path / 'legacy.bin'

    merge_result = run_cli('merge', str(png_path), str(payload_path), str(disguised_path))
    assert merge_result.returncode == 0, merge_result.stderr

    extract_result = run_cli('extract', str(disguised_path), str(recovered_path))
    assert extract_result.returncode == 0, extract_result.stderr
    assert recovered_path.read_bytes() == payload_path.read_bytes()


def test_get_embedded_file_info_returns_structured_data(tmp_path):
    import zipandpng

    png_path = tmp_path / 'cover.png'
    write_base64(png_path, PNG_BASE64)
    payload_path = tmp_path / 'payload.bin'
    payload_path.write_bytes(b'abc123')
    disguised_path = tmp_path / 'embedded.png'

    zipandpng.disguise_file(png_path, payload_path, disguised_path)
    info = zipandpng.get_embedded_file_info(disguised_path)

    assert info['found'] is True
    assert info['filename'] == 'payload.bin'
    assert info['file_size'] == 6


def test_disguise_recover_roundtrip_with_jpg_cover(tmp_path):
    jpg_path = tmp_path / 'cover.jpg'
    write_base64(jpg_path, JPEG_BASE64)
    payload_path = tmp_path / 'payload.exe'
    payload_bytes = b'jpg-payload-data'
    payload_path.write_bytes(payload_bytes)
    disguised_path = tmp_path / 'masked.jpg'
    recovered_path = tmp_path / 'restored.exe'

    disguise_result = run_cli('disguise', str(jpg_path), str(payload_path), str(disguised_path))
    assert disguise_result.returncode == 0, disguise_result.stderr

    info_result = run_cli('info', str(disguised_path))
    assert info_result.returncode == 0, info_result.stderr
    assert 'payload.exe' in info_result.stdout

    recover_result = run_cli('recover', str(disguised_path), str(recovered_path))
    assert recover_result.returncode == 0, recover_result.stderr
    assert recovered_path.read_bytes() == payload_bytes


def test_disguise_recover_roundtrip_with_gif_cover(tmp_path):
    gif_path = tmp_path / 'cover.gif'
    write_base64(gif_path, GIF_BASE64)
    payload_path = tmp_path / 'payload.bin'
    payload_bytes = b'gif-payload-data'
    payload_path.write_bytes(payload_bytes)
    disguised_path = tmp_path / 'masked.gif'
    recovered_path = tmp_path / 'restored.bin'

    disguise_result = run_cli('disguise', str(gif_path), str(payload_path), str(disguised_path))
    assert disguise_result.returncode == 0, disguise_result.stderr

    recover_result = run_cli('recover', str(disguised_path), str(recovered_path))
    assert recover_result.returncode == 0, recover_result.stderr
    assert recovered_path.read_bytes() == payload_bytes


def test_disguise_recover_roundtrip_with_webp_cover(tmp_path):
    webp_path = tmp_path / 'cover.webp'
    write_base64(webp_path, WEBP_BASE64)
    payload_path = tmp_path / 'payload.bin'
    payload_bytes = b'webp-payload-data'
    payload_path.write_bytes(payload_bytes)
    disguised_path = tmp_path / 'masked.webp'
    recovered_path = tmp_path / 'restored.bin'

    disguise_result = run_cli('disguise', str(webp_path), str(payload_path), str(disguised_path))
    assert disguise_result.returncode == 0, disguise_result.stderr

    recover_result = run_cli('recover', str(disguised_path), str(recovered_path))
    assert recover_result.returncode == 0, recover_result.stderr
    assert recovered_path.read_bytes() == payload_bytes


def test_disguise_uses_auto_output_name_when_output_is_omitted(tmp_path):
    jpg_path = tmp_path / 'cover.jpg'
    write_base64(jpg_path, JPEG_BASE64)
    payload_path = tmp_path / 'payload.exe'
    payload_path.write_bytes(b'auto-output')

    result = run_cli('disguise', str(jpg_path), str(payload_path))

    assert result.returncode == 0, result.stderr
    auto_output = tmp_path / 'cover_disguised.jpg'
    assert auto_output.exists()
    assert str(auto_output) in result.stdout


def test_build_default_disguised_output_path_keeps_cover_suffix(tmp_path):
    import zipandpng

    assert zipandpng.build_default_disguised_output_path(tmp_path / 'cover.png').name == 'cover_disguised.png'
    assert zipandpng.build_default_disguised_output_path(tmp_path / 'cover.jpg').name == 'cover_disguised.jpg'
    assert zipandpng.build_default_disguised_output_path(tmp_path / 'cover.gif').name == 'cover_disguised.gif'
    assert zipandpng.build_default_disguised_output_path(tmp_path / 'cover.webp').name == 'cover_disguised.webp'


def test_detect_cover_image_format_supports_png_jpg_gif_webp(tmp_path):
    import zipandpng

    png_path = tmp_path / 'cover.png'
    jpg_path = tmp_path / 'cover.jpg'
    gif_path = tmp_path / 'cover.gif'
    webp_path = tmp_path / 'cover.webp'
    bad_path = tmp_path / 'bad.bin'

    write_base64(png_path, PNG_BASE64)
    write_base64(jpg_path, JPEG_BASE64)
    write_base64(gif_path, GIF_BASE64)
    write_base64(webp_path, WEBP_BASE64)
    bad_path.write_bytes(b'not-image-data')

    assert zipandpng.detect_cover_image_format(png_path.read_bytes()) == 'png'
    assert zipandpng.detect_cover_image_format(jpg_path.read_bytes()) == 'jpeg'
    assert zipandpng.detect_cover_image_format(gif_path.read_bytes()) == 'gif'
    assert zipandpng.detect_cover_image_format(webp_path.read_bytes()) == 'webp'

    try:
        zipandpng.ensure_supported_cover_image(bad_path, bad_path.read_bytes())
    except zipandpng.ZipAndPngError as exc:
        assert '不支持的封面图片格式' in str(exc)
    else:
        raise AssertionError('expected ZipAndPngError for invalid image format')
