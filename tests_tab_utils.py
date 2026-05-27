"""Tests for toolbox_app.tab_utils module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from toolbox_app.tab_utils import collect_inputs_by_suffix, format_drop_summary, merge_new_files


# ---------------------------------------------------------------------------
# collect_inputs_by_suffix
# ---------------------------------------------------------------------------
class TestCollectInputsBySuffix:
    """collect_inputs_by_suffix 边界测试"""

    def test_empty_path_list(self):
        result = collect_inputs_by_suffix([], {'.mp4'})
        assert result == []

    def test_no_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'a.txt').write_text('hello', encoding='utf-8')
            result = collect_inputs_by_suffix([tmp], {'.mp4'})
            assert result == []

    def test_single_file_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'video.mp4'
            f.write_bytes(b'data')
            result = collect_inputs_by_suffix([str(f)], {'.mp4'})
            assert len(result) == 1
            assert result[0].suffix == '.mp4'

    def test_single_file_not_matching_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'readme.txt'
            f.write_text('hi', encoding='utf-8')
            result = collect_inputs_by_suffix([str(f)], {'.mp4'})
            assert result == []

    def test_directory_recursive_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = Path(tmp) / 'sub'
            sub.mkdir()
            (sub / 'a.mp4').write_bytes(b'1')
            (Path(tmp) / 'b.mp4').write_bytes(b'2')
            result = collect_inputs_by_suffix([tmp], {'.mp4'})
            assert len(result) == 2

    def test_directory_non_recursive(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = Path(tmp) / 'sub'
            sub.mkdir()
            (sub / 'a.mp4').write_bytes(b'1')
            (Path(tmp) / 'b.mp4').write_bytes(b'2')
            result = collect_inputs_by_suffix([tmp], {'.mp4'}, recursive=False)
            assert len(result) == 1

    def test_mixed_files_and_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            f1 = Path(tmp) / 'single.mp4'
            f1.write_bytes(b'1')
            subdir = Path(tmp) / 'folder'
            subdir.mkdir()
            (subdir / 'inside.mp4').write_bytes(b'2')
            result = collect_inputs_by_suffix([str(f1), str(subdir)], {'.mp4'})
            assert len(result) == 2

    def test_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'dup.mp4'
            f.write_bytes(b'x')
            result = collect_inputs_by_suffix([str(f), str(f)], {'.mp4'})
            assert len(result) == 1

    def test_multiple_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'a.mp4').write_bytes(b'1')
            (Path(tmp) / 'b.avi').write_bytes(b'2')
            (Path(tmp) / 'c.txt').write_text('x', encoding='utf-8')
            result = collect_inputs_by_suffix([tmp], {'.mp4', '.avi'})
            assert len(result) == 2

    def test_suffix_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'a.MP4').write_bytes(b'1')
            result = collect_inputs_by_suffix([tmp], {'.mp4'})
            assert len(result) == 1


# ---------------------------------------------------------------------------
# format_drop_summary
# ---------------------------------------------------------------------------
class TestFormatDropSummary:
    """format_drop_summary 边界测试"""

    def test_empty_file_list(self):
        result = format_drop_summary([], label='视频')
        assert result == '拖入 视频'

    def test_single_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'my_video.mp4'
            f.write_bytes(b'data')
            result = format_drop_summary([f], label='视频')
            assert '已添加 1 个视频' in result
            assert 'my_video' in result

    def test_exactly_max_preview(self):
        files = []
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(6):
                f = Path(tmp) / f'file{i}.mp4'
                f.write_bytes(b'data')
                files.append(f)
            result = format_drop_summary(files, label='视频', max_preview=6)
            assert '已添加 6 个视频' in result
            assert '另有' not in result

    def test_more_than_max_preview(self):
        files = []
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(10):
                f = Path(tmp) / f'file{i}.mp4'
                f.write_bytes(b'data')
                files.append(f)
            result = format_drop_summary(files, label='视频', max_preview=6)
            assert '已添加 10 个视频' in result
            assert '另有 4 个视频' in result

    def test_custom_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'pic.png'
            f.write_bytes(b'data')
            result = format_drop_summary([f], label='图片')
            assert '已添加 1 个图片' in result
            assert '拖入' not in result


# ---------------------------------------------------------------------------
# merge_new_files
# ---------------------------------------------------------------------------
class TestMergeNewFiles:
    """merge_new_files 边界测试"""

    def test_empty_new_files(self):
        existing = []
        added = merge_new_files(existing, [])
        assert added == []
        assert existing == []

    def test_empty_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'a.mp4'
            f.write_bytes(b'data')
            existing: list[Path] = []
            added = merge_new_files(existing, [f])
            assert len(added) == 1
            assert len(existing) == 1

    def test_full_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'a.mp4'
            f.write_bytes(b'data')
            existing = [f.resolve()]
            added = merge_new_files(existing, [f])
            assert added == []
            assert len(existing) == 1

    def test_partial_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            f1 = Path(tmp) / 'a.mp4'
            f2 = Path(tmp) / 'b.mp4'
            f1.write_bytes(b'1')
            f2.write_bytes(b'2')
            existing = [f1.resolve()]
            added = merge_new_files(existing, [f1, f2])
            assert len(added) == 1
            assert len(existing) == 2

    def test_merge_preserves_existing_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for i in range(5):
                f = Path(tmp) / f'f{i}.mp4'
                f.write_bytes(str(i).encode())
                files.append(f)
            existing: list[Path] = []
            merge_new_files(existing, files[:3])
            merge_new_files(existing, files[2:])
            assert len(existing) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
