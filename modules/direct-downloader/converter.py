from __future__ import annotations

import re
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_CONNECTIONS = 16
URL_RE = re.compile(r'https?://[^\s\'"<>]+', re.IGNORECASE)
ARIA2_PROGRESS_RE = re.compile(r'^\[[#0-9a-fA-F]+(?:\s|$)')


@dataclass(frozen=True)
class DirectDownloadOptions:
    output_dir: str
    output_name: str = ''
    proxy_url: str = ''
    connections: int = DEFAULT_CONNECTIONS
    extra_headers: tuple[str, ...] = ()
    referer: str = ''
    overwrite: bool = False
    output_subdir_by_filename: bool = False


@dataclass(frozen=True)
class DirectDownloadRequest:
    url: str
    output_name: str = ''
    extra_headers: tuple[str, ...] = ()
    referer: str = ''


def parse_url_lines(text: str) -> list[str]:
    unique: dict[str, None] = {}
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line:
            continue
        match = URL_RE.search(line)
        if match:
            unique.setdefault(match.group(0).rstrip('，,;；。、'), None)
    return list(unique)


def _strip_wrapping_quotes(value: str) -> str:
    cleaned = str(value or '').strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def _split_command_line(line: str) -> list[str]:
    try:
        return [_strip_wrapping_quotes(item) for item in shlex.split(line, posix=True)]
    except ValueError:
        return []


def parse_aria2_command_line(line: str) -> DirectDownloadRequest | None:
    tokens = _split_command_line(line)
    if not tokens:
        return None
    first = Path(tokens[0]).name.lower()
    if first not in {'aria2c', 'aria2c.exe'}:
        return None

    url = ''
    output_name = ''
    headers: list[str] = []
    referer = ''
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token.startswith('http://') or token.startswith('https://'):
            url = token
            index += 1
            continue
        if token in {'-o', '--out'} and index + 1 < len(tokens):
            output_name = tokens[index + 1]
            index += 2
            continue
        if token.startswith('--out='):
            output_name = token.split('=', 1)[1]
            index += 1
            continue
        if token == '--header' and index + 1 < len(tokens):
            headers.append(tokens[index + 1])
            index += 2
            continue
        if token.startswith('--header='):
            headers.append(token.split('=', 1)[1])
            index += 1
            continue
        if token == '--referer' and index + 1 < len(tokens):
            referer = tokens[index + 1]
            index += 2
            continue
        if token.startswith('--referer='):
            referer = token.split('=', 1)[1]
            index += 1
            continue
        index += 1

    if not url:
        return None
    for header in headers:
        if header.lower().startswith('referer:') and not referer:
            referer = header.split(':', 1)[1].strip()
    return DirectDownloadRequest(url=url, output_name=output_name, extra_headers=tuple(headers), referer=referer)


def parse_download_requests(text: str) -> list[DirectDownloadRequest]:
    unique: dict[tuple[str, str], DirectDownloadRequest] = {}
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line:
            continue
        command_request = parse_aria2_command_line(line)
        if command_request:
            unique.setdefault((command_request.url, command_request.output_name), command_request)
            continue
        match = URL_RE.search(line)
        if match:
            url = match.group(0).rstrip('，,;；。、')
            unique.setdefault((url, ''), DirectDownloadRequest(url=url))
    return list(unique.values())


def build_proxy_url(host: str | None, port: str | int | None) -> str:
    clean_host = str(host or '').strip()
    clean_port = str(port or '').strip()
    if not clean_host:
        return ''
    if '://' in clean_host and not clean_port:
        return clean_host
    if not clean_port:
        return f'http://{clean_host}'
    if '://' not in clean_host:
        clean_host = f'http://{clean_host}'
    return f'{clean_host}:{clean_port}'


def split_proxy_url(value: str | None) -> tuple[str, str]:
    cleaned = str(value or '').strip()
    if not cleaned:
        return '', ''
    parsed = urlparse(cleaned if '://' in cleaned else f'http://{cleaned}')
    host = parsed.hostname or cleaned
    port = str(parsed.port or '')
    scheme = parsed.scheme or 'http'
    if parsed.username:
        user = parsed.username
        password = f':{parsed.password}' if parsed.password else ''
        host = f'{scheme}://{user}{password}@{host}'
    return host, port


def guess_filename(url: str) -> str:
    path_name = Path(unquote(urlparse(url).path)).name
    return path_name or 'download'


def sanitize_folder_name(value: str, fallback: str = 'download') -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', str(value or '').strip()).strip(' .')
    return cleaned or fallback


def resolve_output_dir_for_request(base_output_dir: str, filename: str, enabled: bool) -> str:
    if not enabled:
        return base_output_dir
    stem = Path(filename or 'download').stem or filename or 'download'
    return str(Path(base_output_dir) / sanitize_folder_name(stem))


def is_aria2_progress_text(text: str) -> bool:
    cleaned = str(text or '').strip()
    if not cleaned:
        return False
    return (
        cleaned.startswith('*** Download Progress Summary')
        or ARIA2_PROGRESS_RE.search(cleaned) is not None
        or '\n[#' in cleaned
    )


def validate_download_form(url_text: str, output_dir: str, connections: str | int, output_name: str = '') -> list[str]:
    errors: list[str] = []
    requests = parse_download_requests(url_text)
    if not requests:
        errors.append('请粘贴至少一个 http/https 直链')
    cleaned_output = output_dir.strip()
    if not cleaned_output:
        errors.append('请选择输出目录')
    elif not Path(cleaned_output).exists():
        errors.append('输出目录不存在')
    try:
        value = int(str(connections).strip() or DEFAULT_CONNECTIONS)
        if value < 1 or value > 64:
            errors.append('连接数必须在 1 到 64 之间')
    except ValueError:
        errors.append('连接数必须是数字')
    if output_name.strip() and len(requests) > 1:
        errors.append('多个链接下载时不要填写统一文件名')
    return errors


def resolve_aria2c_path(root: str | Path | None = None) -> str:
    base = Path(root).resolve() if root else Path(__file__).resolve().parents[2]
    bundled = base / 'modules' / 'video-downloader' / 'bin' / 'aria2c.exe'
    if bundled.is_file():
        return str(bundled)
    return shutil.which('aria2c') or ''


def build_aria2_command(url: str, options: DirectDownloadOptions, aria2c_path: str) -> list[str]:
    connections = max(1, min(64, int(options.connections or DEFAULT_CONNECTIONS)))
    output_name = options.output_name.strip()
    output_dir = resolve_output_dir_for_request(
        options.output_dir,
        output_name or guess_filename(url),
        options.output_subdir_by_filename,
    )
    command = [
        aria2c_path,
        '--continue=true',
        '--max-tries=10',
        '--retry-wait=3',
        '--timeout=60',
        '--connect-timeout=30',
        '--summary-interval=1',
        '--console-log-level=notice',
        '--auto-file-renaming=false',
        f'--allow-overwrite={str(bool(options.overwrite)).lower()}',
        '-x', str(connections),
        '-s', str(connections),
        '-k', '2M',
        '-d', output_dir,
    ]
    if output_name:
        command.extend(['-o', output_name])
    if options.proxy_url:
        command.append(f'--all-proxy={options.proxy_url}')
    if options.referer:
        command.append(f'--referer={options.referer}')
    for header in options.extra_headers:
        if header.strip():
            command.append(f'--header={header.strip()}')
    command.append(url)
    return command


def build_aria2_command_for_request(request: DirectDownloadRequest, options: DirectDownloadOptions, aria2c_path: str) -> list[str]:
    merged_headers = tuple(dict.fromkeys((*request.extra_headers, *options.extra_headers)))
    merged_options = DirectDownloadOptions(
        output_dir=options.output_dir,
        output_name=request.output_name or options.output_name,
        proxy_url=options.proxy_url,
        connections=options.connections,
        extra_headers=merged_headers,
        referer=request.referer or options.referer,
        overwrite=options.overwrite,
        output_subdir_by_filename=options.output_subdir_by_filename,
    )
    return build_aria2_command(request.url, merged_options, aria2c_path)


def _run_command(command: list[str], progress_cb=None, process_cb=None, should_stop=None) -> tuple[int, str]:
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if process_cb:
        process_cb(proc)
    output_lines: list[str] = []
    try:
        while proc.poll() is None:
            if should_stop and should_stop():
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return 130, '\n'.join(output_lines + ['下载已停止'])
            line = proc.stdout.readline() if proc.stdout else ''
            if line:
                text = line.rstrip()
                output_lines.append(text)
                if progress_cb:
                    progress_cb(text)
            else:
                time.sleep(0.1)
        tail = proc.stdout.read() if proc.stdout else ''
        if tail:
            for line in tail.splitlines():
                output_lines.append(line)
                if progress_cb:
                    progress_cb(line)
        return int(proc.returncode or 0), '\n'.join(output_lines)
    finally:
        if process_cb:
            process_cb(None)


def iter_download_urls(
    urls: list[str],
    options: DirectDownloadOptions,
    progress_cb=None,
    root: str | Path | None = None,
    process_cb=None,
    should_stop=None,
) -> list[dict[str, object]]:
    aria2c = resolve_aria2c_path(root)
    if not aria2c:
        raise RuntimeError('未检测到 aria2c')
    Path(options.output_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for index, url in enumerate(urls, start=1):
        if progress_cb:
            progress_cb(f'开始下载 {index}/{len(urls)}: {guess_filename(url)}')
        command = build_aria2_command(url, options, aria2c)
        returncode, output = _run_command(command, progress_cb, process_cb, should_stop)
        results.append({'url': url, 'success': returncode == 0, 'returncode': returncode, 'output': output})
        if returncode == 130:
            break
    return results


def iter_download_requests(
    requests: list[DirectDownloadRequest],
    options: DirectDownloadOptions,
    progress_cb=None,
    root: str | Path | None = None,
    process_cb=None,
    should_stop=None,
) -> list[dict[str, object]]:
    aria2c = resolve_aria2c_path(root)
    if not aria2c:
        raise RuntimeError('未检测到 aria2c')
    Path(options.output_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for index, request in enumerate(requests, start=1):
        if progress_cb:
            progress_cb(f'开始下载 {index}/{len(requests)}: {request.output_name or guess_filename(request.url)}')
        command = build_aria2_command_for_request(request, options, aria2c)
        returncode, output = _run_command(command, progress_cb, process_cb, should_stop)
        results.append({'url': request.url, 'success': returncode == 0, 'returncode': returncode, 'output': output})
        if returncode == 130:
            break
    return results
