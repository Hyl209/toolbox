import base64
import pathlib
import tempfile

from converter import (
    build_data_url,
    decode_base64_to_file,
    encode_image_to_base64,
    infer_extension_from_base64,
    normalize_base64_text,
    save_base64_text,
)


def test_encode_image_to_base64_roundtrip_png_header():
    data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK9sAAAAASUVORK5CYII=')
    with tempfile.TemporaryDirectory() as tmp:
        image = pathlib.Path(tmp) / 'demo.png'
        image.write_bytes(data)
        encoded = encode_image_to_base64(image)
    assert encoded.startswith('iVBORw0KGgo')


def test_build_data_url_uses_extension_mime():
    result = build_data_url('abcd', '.png')
    assert result == 'data:image/png;base64,abcd'


def test_normalize_base64_text_accepts_data_url_and_plain_text():
    plain = 'YWJjZA=='
    data_url = 'data:image/png;base64,YWJjZA=='
    assert normalize_base64_text(plain) == plain
    assert normalize_base64_text(data_url) == plain


def test_infer_extension_from_base64_prefers_data_url_mime():
    text = 'data:image/webp;base64,UklGRg=='
    assert infer_extension_from_base64(text) == '.webp'


def test_decode_base64_to_file_restores_bytes():
    payload = base64.b64encode(b'hello world').decode('ascii')
    with tempfile.TemporaryDirectory() as tmp:
        out = decode_base64_to_file(payload, pathlib.Path(tmp), 'demo.bin', default_extension='.bin')
        assert out.read_bytes() == b'hello world'
        assert out.name == 'demo.bin'


def test_decode_base64_to_file_falls_back_to_png_extension():
    payload = base64.b64encode(b'abc').decode('ascii')
    with tempfile.TemporaryDirectory() as tmp:
        out = decode_base64_to_file(payload, pathlib.Path(tmp), 'image')
        assert out.suffix == '.png'


def test_save_base64_text_writes_txt_file():
    with tempfile.TemporaryDirectory() as tmp:
        out = save_base64_text('abc', pathlib.Path(tmp), 'result.txt')
        assert out.read_text(encoding='utf-8') == 'abc'


def test_normalize_base64_text_rejects_invalid_payload():
    try:
        normalize_base64_text('not-valid-@@@')
    except ValueError as exc:
        assert 'Base64' in str(exc)
    else:
        raise AssertionError('expected ValueError')
