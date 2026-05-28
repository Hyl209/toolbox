from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / 'modules' / 'image-converter' / 'converter.py'


def load_module():
    sys.modules.pop('image_convert_test_module', None)
    spec = importlib.util.spec_from_file_location('image_convert_test_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collect_image_inputs_filters_supported_extensions_recursively():
    mod = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.jpg').write_text('x', encoding='utf-8')
        (root / 'b.txt').write_text('x', encoding='utf-8')
        nested = root / 'nested'
        nested.mkdir()
        (nested / 'c.HEIC').write_text('x', encoding='utf-8')
        (nested / 'd.webp').write_text('x', encoding='utf-8')
        paths = mod.collect_image_inputs([str(root)])
    assert [p.name for p in paths] == ['a.jpg', 'c.HEIC', 'd.webp']


def test_choose_image_output_suffix_normalizes_requested_format():
    mod = load_module()
    assert mod.choose_image_output_suffix('jpg') == '.jpg'
    assert mod.choose_image_output_suffix('jpeg') == '.jpg'
    assert mod.choose_image_output_suffix('png') == '.png'
    assert mod.choose_image_output_suffix('webp') == '.webp'
    assert mod.choose_image_output_suffix('heic') == '.heic'


def test_choose_image_output_suffix_rejects_unknown_format():
    mod = load_module()
    try:
        mod.choose_image_output_suffix('gif')
    except ValueError as exc:
        assert '不支持' in str(exc)
    else:
        raise AssertionError('expected ValueError for unsupported format')


def test_map_jpg_background_option_maps_supported_values():
    mod = load_module()
    assert mod.map_jpg_background_option('white') == 'white'
    assert mod.map_jpg_background_option('black') == 'black'
    assert mod.map_jpg_background_option('transparent') == 'white'


def test_validate_target_size_kb_accepts_positive_number():
    mod = load_module()
    assert mod.validate_target_size_kb('') is None
    assert mod.validate_target_size_kb('256') == 256
    assert mod.validate_target_size_kb('12.5') == 12.5


def test_validate_target_size_kb_rejects_zero_or_invalid():
    mod = load_module()
    for raw in ['0', '-1', 'abc']:
        try:
            mod.validate_target_size_kb(raw)
        except ValueError as exc:
            assert '目标大小' in str(exc)
        else:
            raise AssertionError(f'expected ValueError for {raw!r}')


def test_probe_imagemagick_reports_missing_dependency_cleanly():
    mod = load_module()
    original = mod.shutil.which
    try:
        mod.shutil.which = lambda _name: None
        available, message = mod.probe_imagemagick()
    finally:
        mod.shutil.which = original
    assert available is False
    assert 'ImageMagick' in message


def test_build_output_path_uses_source_stem_and_target_format():
    mod = load_module()
    output = mod.build_output_path(pathlib.Path('/tmp/demo/photo.png'), pathlib.Path('/tmp/out'), 'webp')
    assert output == pathlib.Path('/tmp/out/photo.webp')


def test_build_magick_command_for_jpg_flattens_alpha_with_background():
    mod = load_module()
    command = mod.build_magick_command(
        input_path=pathlib.Path('/tmp/in.png'),
        output_path=pathlib.Path('/tmp/out.jpg'),
        target_format='jpg',
        quality=82,
        preserve_alpha=False,
        jpg_background='black',
        resize_percent=None,
    )
    joined = ' '.join(command)
    assert '-background' in command
    assert 'black' in command
    assert '-alpha' in command
    assert 'remove' in joined
    assert str(pathlib.Path('/tmp/out.jpg')) == command[-1]


def test_build_magick_command_for_png_preserves_alpha_without_flattening():
    mod = load_module()
    command = mod.build_magick_command(
        input_path=pathlib.Path('/tmp/in.png'),
        output_path=pathlib.Path('/tmp/out.png'),
        target_format='png',
        quality=90,
        preserve_alpha=True,
        jpg_background='white',
        resize_percent=None,
    )
    joined = ' '.join(command)
    assert '-background' not in command
    assert 'remove' not in joined


def test_generate_quality_candidates_descends_to_minimum():
    mod = load_module()
    assert mod.generate_quality_candidates(85) == [85, 75, 65, 55, 45, 35, 25]


def test_generate_resize_candidates_descends_until_floor():
    mod = load_module()
    assert mod.generate_resize_candidates() == [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50]


def test_plan_target_attempts_prefers_quality_before_resize():
    mod = load_module()
    attempts = mod.plan_target_attempts(start_quality=85)
    assert attempts[0] == (85, 100)
    assert attempts[1] == (75, 100)
    assert attempts[6] == (25, 100)
    assert attempts[7] == (85, 95)


def test_compress_to_target_size_returns_first_output_within_limit():
    mod = load_module()
    attempts = []

    def fake_run(command):
        quality = int(command[command.index('-quality') + 1])
        resize_value = 100
        if '-resize' in command:
            resize_value = int(command[command.index('-resize') + 1].rstrip('%'))
        output_path = pathlib.Path(command[-1])
        size_map = {
            (85, 100): 300 * 1024,
            (75, 100): 220 * 1024,
            (65, 100): 180 * 1024,
        }
        attempts.append((quality, resize_value))
        output_path.write_bytes(b'x' * size_map[(quality, resize_value)])

    mod.run_magick_command = fake_run
    with tempfile.TemporaryDirectory() as tmp:
        input_path = pathlib.Path(tmp) / 'in.png'
        output_path = pathlib.Path(tmp) / 'out.webp'
        input_path.write_bytes(b'in')
        result = mod.compress_to_target_size(
            input_path=input_path,
            output_path=output_path,
            target_format='webp',
            start_quality=85,
            preserve_alpha=True,
            jpg_background='white',
            target_size_kb=200,
        )
        assert result == output_path
        assert output_path.stat().st_size == 180 * 1024
    assert attempts == [(85, 100), (75, 100), (65, 100)]


def test_compress_to_target_size_raises_when_all_attempts_exceed_target():
    mod = load_module()

    def fake_run(command):
        output_path = pathlib.Path(command[-1])
        output_path.write_bytes(b'x' * (500 * 1024))

    mod.run_magick_command = fake_run
    with tempfile.TemporaryDirectory() as tmp:
        input_path = pathlib.Path(tmp) / 'in.png'
        output_path = pathlib.Path(tmp) / 'out.webp'
        input_path.write_bytes(b'in')
        try:
            mod.compress_to_target_size(
                input_path=input_path,
                output_path=output_path,
                target_format='webp',
                start_quality=85,
                preserve_alpha=True,
                jpg_background='white',
                target_size_kb=100,
            )
        except mod.ImageConvertError as exc:
            assert '未能压缩到目标大小' in str(exc)
        else:
            raise AssertionError('expected ImageConvertError when all attempts exceed target')
