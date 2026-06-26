from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'modules' / 'direct-downloader' / 'converter.py'


def load_module():
    spec = importlib.util.spec_from_file_location('direct_downloader_converter_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_url_lines_extracts_unique_http_urls():
    module = load_module()
    urls = module.parse_url_lines('文件：https://example.com/a.zip\nhttps://example.com/a.zip\nhttp://x.test/b.rar，')
    assert urls == ['https://example.com/a.zip', 'http://x.test/b.rar']


def test_build_proxy_url_splits_host_and_port():
    module = load_module()
    proxy = module.build_proxy_url('127.0.0.1', '7890')
    assert proxy == 'http://127.0.0.1:7890'
    assert module.split_proxy_url(proxy) == ('127.0.0.1', '7890')


def test_parse_aria2_command_preserves_output_headers_and_referer():
    module = load_module()
    request = module.parse_aria2_command_line(
        'aria2c "https://cdn.example.com/a.rar?x=1&y=2" '
        '--out "755.part1.rar" '
        '--header "User-Agent:Mozilla/5.0" '
        '--header "Referer:https://drive.uc.cn/" '
        '--header "Cookie:a=b; c=d"'
    )
    assert request is not None
    assert request.url == 'https://cdn.example.com/a.rar?x=1&y=2'
    assert request.output_name == '755.part1.rar'
    assert 'User-Agent:Mozilla/5.0' in request.extra_headers
    assert 'Cookie:a=b; c=d' in request.extra_headers
    assert request.referer == 'https://drive.uc.cn/'


def test_parse_download_requests_accepts_mixed_plain_urls_and_aria2_commands():
    module = load_module()
    requests = module.parse_download_requests(
        'aria2c "https://cdn.example.com/a.rar" --out "a.rar" --header "Cookie:a=b"\n'
        'https://cdn.example.com/b.rar'
    )
    assert [(item.url, item.output_name) for item in requests] == [
        ('https://cdn.example.com/a.rar', 'a.rar'),
        ('https://cdn.example.com/b.rar', ''),
    ]


def test_validate_rejects_shared_filename_for_multiple_urls(tmp_path):
    module = load_module()
    errors = module.validate_download_form('https://a.test/a.zip\nhttps://b.test/b.zip', str(tmp_path), '16', 'pack.zip')
    assert '多个链接下载时不要填写统一文件名' in errors


def test_build_aria2_command_contains_direct_download_options(tmp_path):
    module = load_module()
    options = module.DirectDownloadOptions(
        output_dir=str(tmp_path),
        output_name='archive.zip',
        proxy_url='http://127.0.0.1:7890',
        connections=8,
        referer='https://pan.example.com/',
        overwrite=True,
    )
    command = module.build_aria2_command('https://cdn.example.com/archive.zip', options, 'aria2c.exe')
    assert command[:1] == ['aria2c.exe']
    assert command[-1] == 'https://cdn.example.com/archive.zip'
    assert ['-x', '8'] == command[command.index('-x'):command.index('-x') + 2]
    assert ['-o', 'archive.zip'] == command[command.index('-o'):command.index('-o') + 2]
    assert f'-d' in command
    assert f'--all-proxy=http://127.0.0.1:7890' in command
    assert '--referer=https://pan.example.com/' in command


def test_build_aria2_command_can_create_subdir_from_plain_url_filename(tmp_path):
    module = load_module()
    options = module.DirectDownloadOptions(
        output_dir=str(tmp_path),
        connections=4,
        output_subdir_by_filename=True,
    )
    command = module.build_aria2_command('https://cdn.example.com/archive.part1.rar?token=1', options, 'aria2c.exe')
    assert ['-d', str(tmp_path / 'archive.part1')] == command[command.index('-d'):command.index('-d') + 2]


def test_build_aria2_command_for_request_merges_command_headers(tmp_path):
    module = load_module()
    request = module.DirectDownloadRequest(
        url='https://cdn.example.com/archive.zip',
        output_name='from-command.zip',
        extra_headers=('Cookie:a=b', 'Referer:https://drive.uc.cn/'),
        referer='https://drive.uc.cn/',
    )
    options = module.DirectDownloadOptions(output_dir=str(tmp_path), output_name='manual.zip', connections=4)
    command = module.build_aria2_command_for_request(request, options, 'aria2c.exe')
    assert ['-o', 'from-command.zip'] == command[command.index('-o'):command.index('-o') + 2]
    assert '--header=Cookie:a=b' in command
    assert '--header=Referer:https://drive.uc.cn/' in command
    assert '--referer=https://drive.uc.cn/' in command


def test_build_aria2_command_for_request_can_create_subdir_from_out_name(tmp_path):
    module = load_module()
    request = module.DirectDownloadRequest(
        url='https://cdn.example.com/opaque',
        output_name='755.part1.rar',
    )
    options = module.DirectDownloadOptions(output_dir=str(tmp_path), output_subdir_by_filename=True)
    command = module.build_aria2_command_for_request(request, options, 'aria2c.exe')
    assert ['-d', str(tmp_path / '755.part1')] == command[command.index('-d'):command.index('-d') + 2]
    assert ['-o', '755.part1.rar'] == command[command.index('-o'):command.index('-o') + 2]


def test_is_aria2_progress_text_detects_summary_without_flagging_normal_logs():
    module = load_module()
    assert module.is_aria2_progress_text('*** Download Progress Summary as of Tue Jun 23 18:27:24 2026 ***')
    assert module.is_aria2_progress_text('[#1b550 162MiB/4.3GiB(3%) CN:16 DL:1.5MiB ETA:46m34s]')
    assert module.is_aria2_progress_text('FILE: G:/BaiduNetdiskDownload/a.mp4\n[#1b550 3%]')
    assert not module.is_aria2_progress_text('开始下载 1/1: a.mp4')
    assert not module.is_aria2_progress_text('ERROR failed')


def test_run_command_streams_output():
    module = load_module()
    lines = []
    returncode, output = module._run_command(
        ['cmd', '/c', 'echo hello'],
        lines.append,
    )
    assert returncode == 0
    assert 'hello' in output
    assert 'hello' in lines


def test_run_command_can_be_stopped():
    module = load_module()
    returncode, output = module._run_command(
        [sys.executable, '-c', 'import time; time.sleep(30)'],
        should_stop=lambda: True,
    )
    assert returncode == 130
    assert '下载已停止' in output
