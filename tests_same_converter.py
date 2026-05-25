import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / 'same' / 'converter.py'


def load_module():
    sys.modules.pop('tests_same_converter_module', None)
    spec = importlib.util.spec_from_file_location('tests_same_converter_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_move_duplicates_reports_outside_source_without_aborting_batch():
    module = load_module()
    with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as outside_tmp:
        root = pathlib.Path(root_tmp)
        outside_root = pathlib.Path(outside_tmp)
        (root / 'a.txt').write_bytes(b'duplicate')
        inside_duplicate = root / 'b.txt'
        inside_duplicate.write_bytes(b'duplicate')
        outside_duplicate = outside_root / 'b.txt'
        outside_duplicate.write_bytes(b'duplicate')

        moved = module.move_duplicates(root, [{'duplicates': [outside_duplicate, inside_duplicate]}])

        assert len(moved) == 2
        assert moved[0]['success'] is False
        assert 'subpath' in moved[0]['error'] or 'relative_to' in moved[0]['error']
        assert moved[1]['success'] is True
        assert not inside_duplicate.exists()
        assert outside_duplicate.exists()
        assert (root / module.DEFAULT_TARGET_DIR_NAME / 'b.txt').exists()


def test_same_module_detects_exact_duplicate_bytes_across_different_suffixes():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / 'a.bin').write_bytes(b'exact-bytes')
        (root / 'b.dat').write_bytes(b'exact-bytes')
        (root / 'c.bin').write_bytes(b'other-bytes')

        result = module.find_duplicate_groups(root, recursive=False)

        assert result['duplicate_group_count'] == 1
        assert result['duplicate_file_count'] == 1
        group = result['groups'][0]
        assert group['match_mode'] == 'exact'
        assert pathlib.Path(group['keeper']).name == 'a.bin'
        assert [pathlib.Path(item).name for item in group['duplicates']] == ['b.dat']


def test_same_module_detects_same_video_content_with_similarity_threshold():
    module = load_module()
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        return

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        mp4_path = root / 'a.mp4'
        mkv_path = root / 'b.mkv'
        other_path = root / 'c.mp4'

        common_source = 'testsrc=size=160x120:rate=6:duration=4'
        other_source = 'smptebars=size=160x120:rate=6:duration=4'
        commands = [
            [
                ffmpeg_path,
                '-y',
                '-f',
                'lavfi',
                '-i',
                common_source,
                '-pix_fmt',
                'yuv420p',
                str(mp4_path),
            ],
            [
                ffmpeg_path,
                '-y',
                '-f',
                'lavfi',
                '-i',
                common_source,
                '-pix_fmt',
                'yuv420p',
                str(mkv_path),
            ],
            [
                ffmpeg_path,
                '-y',
                '-f',
                'lavfi',
                '-i',
                other_source,
                '-pix_fmt',
                'yuv420p',
                str(other_path),
            ],
        ]
        for command in commands:
            subprocess.run(command, check=True, capture_output=True)

        result = module.find_duplicate_groups(root, recursive=False)

        assert result['duplicate_group_count'] == 1
        assert result['duplicate_file_count'] == 1
        group = result['groups'][0]
        assert group['match_mode'] == 'video_similarity'
        assert float(group['similarity']) >= 0.95
        assert pathlib.Path(group['keeper']).name == 'a.mp4'
        assert [pathlib.Path(item).name for item in group['duplicates']] == ['b.mkv']


def test_same_module_does_not_detect_different_videos_as_duplicates():
    module = load_module()
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        return

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        a_path = root / 'a.mp4'
        b_path = root / 'b.mp4'
        subprocess.run(
            [ffmpeg_path, '-y', '-f', 'lavfi', '-i', 'testsrc=size=160x120:rate=6:duration=4', '-pix_fmt', 'yuv420p', str(a_path)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [ffmpeg_path, '-y', '-f', 'lavfi', '-i', 'testsrc2=size=160x120:rate=6:duration=4', '-pix_fmt', 'yuv420p', str(b_path)],
            check=True,
            capture_output=True,
        )

        result = module.find_duplicate_groups(root, recursive=False)

        assert result['duplicate_group_count'] == 0
        assert result['duplicate_file_count'] == 0


def test_same_module_only_builds_video_signatures_for_metadata_candidates():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        paths = [root / 'a.mp4', root / 'b.mp4', root / 'c.mp4']
        for path in paths:
            path.write_bytes(b'x')

        frame = bytes([128]) * (module.VIDEO_FRAME_WIDTH * module.VIDEO_FRAME_HEIGHT * 3)
        metadata_by_name = {
            'a.mp4': {'duration': 10.0, 'aspect_ratio': 1.33},
            'b.mp4': {'duration': 10.6, 'aspect_ratio': 1.34},
            'c.mp4': {'duration': 40.0, 'aspect_ratio': 1.78},
        }
        built_names: list[str] = []
        original_probe = module._probe_video
        original_build = module._build_video_signature

        def fake_probe(path):
            item = metadata_by_name[path.name]
            return {
                'duration': item['duration'],
                'width': 160,
                'height': 120,
                'aspect_ratio': item['aspect_ratio'],
            }

        def fake_build(path):
            built_names.append(path.name)
            if path.name == 'c.mp4':
                raise AssertionError('c.mp4 should have been filtered before signature building')
            item = metadata_by_name[path.name]
            return {
                'path': path,
                'duration': item['duration'],
                'width': 160,
                'height': 120,
                'aspect_ratio': item['aspect_ratio'],
                'frames': (frame, frame, frame),
            }

        module._probe_video = fake_probe
        module._build_video_signature = fake_build
        try:
            result = module.find_duplicate_groups(root, recursive=False)
        finally:
            module._probe_video = original_probe
            module._build_video_signature = original_build

        assert result['duplicate_group_count'] == 1
        assert set(built_names) == {'a.mp4', 'b.mp4'}
