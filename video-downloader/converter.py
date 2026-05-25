from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timezone
from html import unescape
import importlib.util
import re
import shutil
import subprocess
from dataclasses import dataclass
from collections.abc import Iterable
from pathlib import Path
from time import monotonic
from typing import Callable, Literal
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SourceKind = Literal['telegram_message', 'telegram_chat', 'web']
ProgressCallback = Callable[[str], None]

TELEGRAM_HOSTS = {'t.me', 'telegram.me', 'telegram.dog', 'www.t.me', 'www.telegram.me'}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WHITESPACE_RE = re.compile(r'\s+')
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
MEDIA_URL_RE = re.compile(r"""(?P<url>(?:https?:)?//[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
RELATIVE_MEDIA_RE = re.compile(r"""(?P<url>/[^"'\\\s<>]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:\?[^"'\\\s<>]*)?)""", re.IGNORECASE)
SESSION_FILE_NAME = 'telegram.session'
DEFAULT_FILENAME_TEMPLATE = '%(title)s [%(id)s].%(ext)s'


@dataclass(frozen=True)
class TelegramConfig:
    api_id: str
    api_hash: str
    phone: str
    session_file: str | Path


@dataclass(frozen=True)
class DownloadTask:
    source_url: str
    source_kind: SourceKind
    target_title: str = ''
    output_subdir: str = ''


@dataclass(frozen=True)
class DownloadOptions:
    web_use_browser_cookies: bool = False
    overwrite: bool = False
    filename_template: str = DEFAULT_FILENAME_TEMPLATE
    web_candidate_index: int | None = None
    web_download_all_candidates: bool = False
    telegram_recent_limit: int | None = 500
    telegram_download_all_messages: bool = False
    telegram_date_from: date | None = None
    telegram_date_to: date | None = None
    telegram_include_videos: bool = True
    telegram_include_photos: bool = False


@dataclass(frozen=True)
class TelegramUrlParts:
    entity_ref: str | int
    message_id: int | None
    invite_hash: str = ''


class DownloadError(RuntimeError):
    pass


def parse_task_lines(text: str) -> list[str]:
    unique: dict[str, None] = {}
    for raw in (text or '').splitlines():
        normalized = _normalize_url_text(raw)
        if normalized:
            unique.setdefault(normalized, None)
    return list(unique.keys())


def classify_source(url: str) -> SourceKind:
    normalized = _normalize_url_text(url)
    if not normalized:
        raise ValueError('链接不能为空')
    parsed = urlparse(normalized)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError(f'无效链接: {url}')
    host = parsed.netloc.lower()
    if host not in TELEGRAM_HOSTS:
        return 'web'
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return 'telegram_chat'
    if parts[0] == 'joinchat' or parts[0].startswith('+'):
        return 'telegram_chat'
    if parts[0] == 'c':
        if len(parts) >= 3 and parts[2].isdigit():
            return 'telegram_message'
        return 'telegram_chat'
    if len(parts) >= 2 and parts[1].isdigit():
        return 'telegram_message'
    return 'telegram_chat'


def build_download_tasks(urls: Iterable[str]) -> list[DownloadTask]:
    tasks: list[DownloadTask] = []
    for raw in urls:
        normalized = _normalize_url_text(raw)
        if not normalized:
            continue
        tasks.append(
            DownloadTask(
                source_url=normalized,
                source_kind=classify_source(normalized),
                target_title=guess_task_title(normalized),
            )
        )
    return tasks


def guess_task_title(url: str) -> str:
    parsed = urlparse(_normalize_url_text(url))
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return sanitize_filename_component(parsed.netloc or 'video')
    return sanitize_filename_component(parts[-1] or parts[0] or parsed.netloc or 'video')


def probe_download_backends() -> dict[str, dict[str, object]]:
    ffmpeg = shutil.which('ffmpeg')
    return {
        'telethon': _build_backend_status('telethon', 'Telegram 登录/下载'),
        'yt_dlp': _build_backend_status('yt_dlp', '网页视频解析'),
        'ffmpeg': {
            'available': bool(ffmpeg),
            'label': '媒体合并/转封装',
            'message': '已检测到 ffmpeg' if ffmpeg else '未检测到 ffmpeg，部分站点可能无法合并音视频',
            'path': ffmpeg or '',
        },
    }


def validate_download_request(
    task_lines: Iterable[str] | Iterable[DownloadTask] | str,
    output_dir: str,
    telegram_config: TelegramConfig | None = None,
    recent_limit: str | int | None = None,
    telegram_download_all_messages: bool = False,
    date_from: str | date | None = None,
    date_to: str | date | None = None,
    telegram_include_videos: bool = True,
    telegram_include_photos: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        tasks = _coerce_tasks(task_lines)
    except ValueError as exc:
        return [str(exc)]
    if not tasks:
        errors.append('请先输入下载链接')
    cleaned_output = (output_dir or '').strip()
    if not cleaned_output:
        errors.append('请选择输出目录')
    else:
        output_path = Path(cleaned_output)
        if output_path.exists() and not output_path.is_dir():
            errors.append('输出路径不是文件夹')
    try:
        normalize_recent_limit(recent_limit, default=500)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        normalize_date_range(date_from, date_to)
    except ValueError as exc:
        errors.append(str(exc))
    needs_telegram = any(task.source_kind.startswith('telegram') for task in tasks)
    if needs_telegram:
        if not telegram_include_videos and not telegram_include_photos:
            errors.append('Telegram 任务至少要勾选一种下载类型')
        if telegram_config is None:
            errors.append('Telegram 任务需要填写 API ID、API Hash 和手机号')
        else:
            if not str(telegram_config.api_id).strip():
                errors.append('请输入 Telegram API ID')
            if not str(telegram_config.api_hash).strip():
                errors.append('请输入 Telegram API Hash')
            if not str(telegram_config.phone).strip():
                errors.append('请输入 Telegram 手机号')
            if not str(telegram_config.session_file).strip():
                errors.append('Telegram 会话文件路径不能为空')
        if not telegram_download_all_messages:
            try:
                limit = normalize_recent_limit(recent_limit, default=500)
            except ValueError:
                limit = None
            if limit == 0:
                errors.append('未勾选“全部消息”时，最近消息条数不能为 0')
    return errors


def normalize_recent_limit(value: str | int | None, default: int | None = 500) -> int | None:
    if value is None:
        return default
    if isinstance(value, int):
        if value < 0:
            raise ValueError('最近消息条数不能小于 0')
        return value
    cleaned = str(value).strip()
    if not cleaned:
        return default
    try:
        limit = int(cleaned)
    except ValueError as exc:
        raise ValueError('最近消息条数必须是整数') from exc
    if limit < 0:
        raise ValueError('最近消息条数不能小于 0')
    return limit


def normalize_positive_index(value: str | int | None, field_label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f'{field_label}必须大于 0')
        return value
    cleaned = str(value).strip()
    if not cleaned:
        return None
    try:
        parsed = int(cleaned)
    except ValueError as exc:
        raise ValueError(f'{field_label}必须是正整数') from exc
    if parsed <= 0:
        raise ValueError(f'{field_label}必须大于 0')
    return parsed


def parse_iso_date(value: str | date | None, field_label: str) -> date | None:
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    cleaned = str(value).strip()
    if not cleaned:
        return None
    try:
        return datetime.strptime(cleaned, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError(f'{field_label}必须是 YYYY-MM-DD 格式') from exc


def normalize_date_range(date_from: str | date | None, date_to: str | date | None) -> tuple[date | None, date | None]:
    parsed_from = parse_iso_date(date_from, '开始日期')
    parsed_to = parse_iso_date(date_to, '结束日期')
    if parsed_from and parsed_to and parsed_from > parsed_to:
        raise ValueError('开始日期不能晚于结束日期')
    return parsed_from, parsed_to


def sanitize_filename_component(text: str, fallback: str = 'video') -> str:
    cleaned = INVALID_FILENAME_CHARS.sub('_', str(text or '').strip())
    cleaned = WHITESPACE_RE.sub(' ', cleaned).strip(' .')
    return cleaned or fallback


def ensure_unique_path(path: str | Path) -> Path:
    candidate = Path(path)
    parent = candidate.parent
    stem = candidate.stem
    suffix = ''.join(candidate.suffixes)
    index = 1
    while candidate.exists():
        candidate = parent / f'{stem} ({index}){suffix}'
        index += 1
    return candidate


def ensure_unique_stem(directory: str | Path, stem: str) -> str:
    folder = Path(directory)
    safe_stem = sanitize_filename_component(stem)
    candidate = safe_stem
    index = 1
    while any(folder.glob(f'{candidate}.*')):
        candidate = f'{safe_stem} ({index})'
        index += 1
    return candidate


def download_batch(
    tasks: Iterable[str] | Iterable[DownloadTask],
    output_dir: str | Path,
    telegram_config: TelegramConfig | None,
    options: DownloadOptions | None = None,
    progress_cb: ProgressCallback | None = None,
) -> list[dict[str, object]]:
    task_list = _coerce_tasks(tasks)
    config = telegram_config
    download_options = options or DownloadOptions()
    errors = validate_download_request(
        task_list,
        str(output_dir),
        config,
        recent_limit=download_options.telegram_recent_limit,
        telegram_download_all_messages=download_options.telegram_download_all_messages,
        date_from=download_options.telegram_date_from,
        date_to=download_options.telegram_date_to,
        telegram_include_videos=download_options.telegram_include_videos,
        telegram_include_photos=download_options.telegram_include_photos,
    )
    if errors:
        raise ValueError('\n'.join(errors))
    output_root = Path(output_dir).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)
    results: dict[int, dict[str, object]] = {}
    total_tasks = len(task_list)
    telegram_entries = [(index, task) for index, task in enumerate(task_list) if task.source_kind.startswith('telegram')]
    if telegram_entries:
        telegram_results = asyncio.run(
            _download_telegram_entries(
                telegram_entries,
                output_root,
                config,
                download_options,
                progress_cb,
                total_tasks=total_tasks,
            )
        )
        results.update(telegram_results)
    for index, task in enumerate(task_list):
        if task.source_kind.startswith('telegram'):
            continue
        _emit_task_start(progress_cb, index, total_tasks, task)
        try:
            results[index] = _download_web_task(task, output_root, download_options, progress_cb)
        except Exception as exc:
            results[index] = _make_result(task, False, [], str(exc))
        _emit_task_done(progress_cb, len(results), total_tasks)
    return [results[index] for index in range(len(task_list))]


def check_telegram_authorization(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_check_telegram_authorization_async(config))


def begin_telegram_login(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_begin_telegram_login_async(config))


def complete_telegram_login(config: TelegramConfig, code: str, phone_code_hash: str) -> dict[str, object]:
    return asyncio.run(_complete_telegram_login_async(config, code, phone_code_hash))


def _normalize_url_text(text: str) -> str:
    cleaned = str(text or '').strip()
    if not cleaned:
        return ''
    cleaned = cleaned.lstrip('-*').strip()
    if cleaned.startswith('www.'):
        cleaned = f'https://{cleaned}'
    elif '://' not in cleaned and cleaned.startswith(('t.me/', 'telegram.me/', 'telegram.dog/')):
        cleaned = f'https://{cleaned}'
    return cleaned


def _coerce_tasks(task_lines: Iterable[str] | Iterable[DownloadTask] | str) -> list[DownloadTask]:
    if isinstance(task_lines, str):
        return build_download_tasks(parse_task_lines(task_lines))
    items = list(task_lines)
    if not items:
        return []
    if all(isinstance(item, DownloadTask) for item in items):
        return [item for item in items if isinstance(item, DownloadTask)]
    return build_download_tasks(str(item) for item in items)


def _build_backend_status(module_name: str, label: str) -> dict[str, object]:
    available = importlib.util.find_spec(module_name) is not None
    return {
        'available': available,
        'label': label,
        'message': f'已检测到 {module_name}' if available else f'未安装 {module_name}',
        'path': module_name,
    }


async def _check_telegram_authorization_async(config: TelegramConfig) -> dict[str, object]:
    _require_telegram_backend()
    client = await _create_telegram_client(config)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        return {
            'authorized': authorized,
            'message': 'Telegram 会话已登录' if authorized else 'Telegram 尚未登录，请先发送验证码并完成登录',
        }
    finally:
        await client.disconnect()


async def _begin_telegram_login_async(config: TelegramConfig) -> dict[str, object]:
    _require_telegram_backend()
    client = await _create_telegram_client(config)
    try:
        await client.connect()
        if await client.is_user_authorized():
            return {
                'authorized': True,
                'sent': False,
                'phone_code_hash': '',
                'message': 'Telegram 会话已登录',
            }
        result = await client.send_code_request(config.phone)
        return {
            'authorized': False,
            'sent': True,
            'phone_code_hash': getattr(result, 'phone_code_hash', ''),
            'message': '验证码已发送，请输入验证码后点击登录',
        }
    finally:
        await client.disconnect()


async def _complete_telegram_login_async(config: TelegramConfig, code: str, phone_code_hash: str) -> dict[str, object]:
    _require_telegram_backend()
    cleaned_code = str(code or '').strip()
    cleaned_hash = str(phone_code_hash or '').strip()
    if not cleaned_code:
        raise ValueError('请输入 Telegram 验证码')
    if not cleaned_hash:
        raise ValueError('请先发送验证码')
    from telethon.errors import SessionPasswordNeededError

    client = await _create_telegram_client(config)
    try:
        await client.connect()
        if await client.is_user_authorized():
            return {'authorized': True, 'message': 'Telegram 会话已登录'}
        try:
            await client.sign_in(phone=config.phone, code=cleaned_code, phone_code_hash=cleaned_hash)
        except SessionPasswordNeededError as exc:
            raise DownloadError('当前账号开启了两步验证，v1 暂不支持密码验证') from exc
        return {'authorized': True, 'message': 'Telegram 登录成功'}
    finally:
        await client.disconnect()


async def _create_telegram_client(config: TelegramConfig):
    from telethon import TelegramClient

    api_id = str(config.api_id).strip()
    try:
        api_id_int = int(api_id)
    except ValueError as exc:
        raise ValueError('Telegram API ID 必须是整数') from exc
    session_path = Path(config.session_file).expanduser()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(str(session_path), api_id_int, str(config.api_hash).strip())


def _require_telegram_backend() -> None:
    if importlib.util.find_spec('telethon') is None:
        raise DownloadError('未安装 Telethon，无法使用 Telegram 下载')


def _require_web_backend() -> None:
    if importlib.util.find_spec('yt_dlp') is None:
        raise DownloadError('未安装 yt-dlp，无法解析网页视频')


async def _download_telegram_entries(
    entries: list[tuple[int, DownloadTask]],
    output_root: Path,
    config: TelegramConfig | None,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    total_tasks: int,
) -> dict[int, dict[str, object]]:
    results: dict[int, dict[str, object]] = {}
    if config is None:
        for index, task in entries:
            results[index] = _make_result(task, False, [], 'Telegram 配置缺失')
        return results
    try:
        client = await _create_telegram_client(config)
        await client.connect()
        if not await client.is_user_authorized():
            message = 'Telegram 尚未登录，请先在页面完成验证码登录'
            for index, task in entries:
                results[index] = _make_result(task, False, [], message)
                _emit_task_done(progress_cb, len(results), total_tasks)
            return results
        for index, task in entries:
            _emit_task_start(progress_cb, index, total_tasks, task)
            try:
                results[index] = await _download_single_telegram_task(client, task, output_root, options, progress_cb)
            except Exception as exc:
                results[index] = _make_result(task, False, [], str(exc))
            _emit_task_done(progress_cb, len(results), total_tasks)
        return results
    finally:
        if 'client' in locals():
            await client.disconnect()


async def _download_single_telegram_task(client, task: DownloadTask, output_root: Path, options: DownloadOptions, progress_cb: ProgressCallback | None) -> dict[str, object]:
    parts = _parse_telegram_url(task.source_url)
    entity = await _resolve_telegram_entity(client, parts)
    if task.source_kind == 'telegram_message':
        if parts.message_id is None:
            raise DownloadError('Telegram 消息链接缺少消息 ID')
        message = await client.get_messages(entity, ids=parts.message_id)
        if not message or not _message_matches_media_selection(message, options):
            raise DownloadError('该 Telegram 消息中没有符合筛选条件的媒体')
        output_folder = _resolve_task_output_dir(output_root, task)
        output_folder.mkdir(parents=True, exist_ok=True)
        file_path = await _download_telegram_message_media(
            client,
            message,
            output_folder,
            fallback_prefix=task.target_title or 'telegram_video',
            options=options,
            progress_cb=progress_cb,
        )
        _emit(progress_cb, f'Telegram OK -> {file_path.name}')
        return _make_result(task, True, [file_path], '')

    recent_limit = None if options.telegram_download_all_messages else options.telegram_recent_limit
    date_from = options.telegram_date_from
    date_to = options.telegram_date_to
    after_utc = _date_start_utc(date_from)
    before_utc = _date_end_utc(date_to)
    output_folder = _resolve_task_output_dir(output_root, task, default_name=_get_entity_title(entity))
    output_folder.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    scanned_count = 0
    matched_count = 0
    async for message in client.iter_messages(entity, limit=recent_limit or None):
        scanned_count += 1
        message_date = _normalize_message_datetime(getattr(message, 'date', None))
        if before_utc is not None and message_date is not None and message_date > before_utc:
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        if after_utc is not None and message_date is not None and message_date < after_utc:
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        if not _message_matches_media_selection(message, options):
            if scanned_count == 1 or scanned_count % 25 == 0:
                _emit_scan_progress(progress_cb, scanned_count, matched_count)
            continue
        matched_count += 1
        _emit_scan_progress(progress_cb, scanned_count, matched_count)
        file_path = await _download_telegram_message_media(
            client,
            message,
            output_folder,
            fallback_prefix=f'{task.target_title or "telegram_video"}_{message.id}',
            options=options,
            progress_cb=progress_cb,
        )
        files.append(file_path)
        _emit(progress_cb, f'Telegram OK -> {file_path.name}')
    if not files:
        raise DownloadError('该聊天范围内未找到符合筛选条件的媒体')
    return _make_result(task, True, files, '')


async def _resolve_telegram_entity(client, parts: TelegramUrlParts):
    from telethon import functions, utils
    from telethon.errors import UserAlreadyParticipantError

    if parts.invite_hash:
        try:
            updates = await client(functions.messages.ImportChatInviteRequest(parts.invite_hash))
        except UserAlreadyParticipantError:
            updates = None
        except Exception as exc:
            raise DownloadError(f'无法访问 Telegram 邀请链接: {exc}') from exc
        if updates is not None:
            chats = getattr(updates, 'chats', None) or []
            if chats:
                return chats[0]
        async for dialog in client.iter_dialogs():
            link_hash = sanitize_filename_component(parts.invite_hash, fallback='')
            title = sanitize_filename_component(_get_entity_title(dialog.entity), fallback='')
            if link_hash and link_hash in title:
                return dialog.entity
        raise DownloadError('无法根据邀请链接解析聊天，请确认账号已加入该会话')
    if isinstance(parts.entity_ref, int):
        expected_peer_id = int(f'-100{parts.entity_ref}')
        async for dialog in client.iter_dialogs():
            if utils.get_peer_id(dialog.entity) == expected_peer_id:
                return dialog.entity
        raise DownloadError('当前账号没有找到该私有聊天，请确认已加入并且聊天可见')
    try:
        return await client.get_entity(parts.entity_ref)
    except Exception as exc:
        raise DownloadError(f'无法解析 Telegram 聊天: {exc}') from exc


async def _download_telegram_message_media(
    client,
    message,
    output_dir: Path,
    fallback_prefix: str,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None = None,
) -> Path:
    file_info = getattr(message, 'file', None)
    original_name = ''
    suffix = ''
    if file_info is not None:
        original_name = getattr(file_info, 'name', '') or ''
        suffix = getattr(file_info, 'ext', '') or ''
    if _is_photo_message(message) and options.telegram_include_photos:
        suffix = Path(original_name).suffix or suffix or '.jpg'
        target_name = sanitize_filename_component(Path(original_name).stem or fallback_prefix) + suffix
    elif original_name:
        target_name = sanitize_filename_component(Path(original_name).stem) + (Path(original_name).suffix or suffix or '.mp4')
    else:
        target_name = sanitize_filename_component(fallback_prefix) + (suffix or '.mp4')
    target_path = ensure_unique_path(output_dir / target_name)
    downloaded = await client.download_media(
        message,
        file=str(target_path),
        progress_callback=_make_telegram_progress_callback(progress_cb, target_path.name),
    )
    if not downloaded:
        raise DownloadError('Telegram 视频下载失败')
    return Path(downloaded)


def _parse_telegram_url(url: str) -> TelegramUrlParts:
    parsed = urlparse(_normalize_url_text(url))
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        raise ValueError('无效 Telegram 链接')
    if parts[0] == 'joinchat':
        if len(parts) < 2:
            raise ValueError('无效 Telegram 邀请链接')
        return TelegramUrlParts(entity_ref='', message_id=None, invite_hash=parts[1])
    if parts[0].startswith('+'):
        return TelegramUrlParts(entity_ref='', message_id=None, invite_hash=parts[0][1:])
    if parts[0] == 'c':
        if len(parts) < 2 or not parts[1].isdigit():
            raise ValueError('无效 Telegram 私有聊天链接')
        message_id = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
        return TelegramUrlParts(entity_ref=int(parts[1]), message_id=message_id)
    message_id = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
    return TelegramUrlParts(entity_ref=parts[0], message_id=message_id)


def _is_video_message(message) -> bool:
    if message is None:
        return False
    if getattr(message, 'video', None) is not None:
        return True
    file_info = getattr(message, 'file', None)
    mime_type = getattr(file_info, 'mime_type', '') or ''
    if mime_type.startswith('video/'):
        return True
    document = getattr(message, 'document', None)
    doc_mime = getattr(document, 'mime_type', '') or ''
    return doc_mime.startswith('video/')


def _is_photo_message(message) -> bool:
    if message is None:
        return False
    if getattr(message, 'photo', None) is not None:
        return True
    file_info = getattr(message, 'file', None)
    mime_type = getattr(file_info, 'mime_type', '') or ''
    if mime_type.startswith('image/'):
        return True
    document = getattr(message, 'document', None)
    doc_mime = getattr(document, 'mime_type', '') or ''
    return doc_mime.startswith('image/')


def _message_matches_media_selection(message, options: DownloadOptions) -> bool:
    if options.telegram_include_videos and _is_video_message(message):
        return True
    if options.telegram_include_photos and _is_photo_message(message):
        return True
    return False


def _get_entity_title(entity) -> str:
    return getattr(entity, 'title', '') or getattr(entity, 'username', '') or getattr(entity, 'first_name', '') or 'telegram_chat'


def _resolve_task_output_dir(output_root: Path, task: DownloadTask, default_name: str = '') -> Path:
    subdir = sanitize_filename_component(task.output_subdir or default_name, fallback='').strip()
    if not subdir:
        return output_root
    return output_root / subdir


def _normalize_message_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _date_start_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _date_end_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


def _is_m3u8_url(url: str) -> bool:
    return str(url or '').lower().split('?', 1)[0].endswith('.m3u8')


def _download_web_candidate(
    candidate_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
) -> dict[str, object]:
    if _is_m3u8_url(candidate_url) and ffmpeg_path:
        return _download_m3u8_with_ffmpeg(
            candidate_url,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
        )
    return _download_url_with_ytdlp(
        candidate_url,
        output_root,
        options,
        progress_cb,
        title_hint=task.target_title,
    )


def _download_web_candidates(
    candidates: list[str],
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
) -> tuple[list[Path], Exception | None]:
    downloaded_files: list[Path] = []
    last_error: Exception | None = None
    total_candidates = len(candidates)
    for candidate_index, candidate in enumerate(candidates, start=1):
        try:
            _emit_file_select(progress_cb, candidate, candidate_index, total_candidates)
            downloaded = _download_web_candidate(
                candidate,
                task,
                output_root,
                options,
                progress_cb,
                ffmpeg_path=ffmpeg_path,
            )
            files = [Path(item) for item in downloaded['files']]
            if not options.web_download_all_candidates:
                return files, None
            downloaded_files.extend(files)
        except Exception as exc:
            last_error = exc
    return downloaded_files, last_error


def inspect_web_media_batch(urls: Iterable[str] | str, progress_cb: ProgressCallback | None = None) -> list[dict[str, object]]:
    items = parse_task_lines(urls) if isinstance(urls, str) else [_normalize_url_text(item) for item in urls]
    web_urls = [url for url in items if url and classify_source(url) == 'web']
    results: list[dict[str, object]] = []
    total = len(web_urls)
    for index, url in enumerate(web_urls, start=1):
        _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_start|index={index}|total={total}|url={url}')
        try:
            result = inspect_web_media_candidates(url)
            _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_done|count={result["candidate_count"]}|index={index}|total={total}|url={url}')
        except Exception as exc:
            result = {
                'source_url': url,
                'success': False,
                'candidate_count': 0,
                'candidates': [],
                'source': '',
                'error': str(exc),
            }
            _emit(progress_cb, f'__HYL_PROGRESS__|web_scan_done|count=0|index={index}|total={total}|url={url}')
        results.append(result)
    return results


def inspect_web_media_candidates(source_url: str) -> dict[str, object]:
    candidates, source = _collect_web_media_candidates(source_url)
    return {
        'source_url': source_url,
        'success': True,
        'candidate_count': len(candidates),
        'candidates': candidates,
        'source': source,
        'error': '',
    }


def _download_web_task(task: DownloadTask, output_root: Path, options: DownloadOptions, progress_cb: ProgressCallback | None) -> dict[str, object]:
    first_error = None
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(task.source_url)
    except Exception:
        ytdlp_candidates = []
    if len(ytdlp_candidates) > 1:
            try:
                ffmpeg_path = shutil.which('ffmpeg') or ''
                if options.web_download_all_candidates:
                    downloaded_files, last_error = _download_web_candidates(
                        ytdlp_candidates,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
                elif options.web_candidate_index is not None:
                    candidate_position = options.web_candidate_index - 1
                    if candidate_position < 0 or candidate_position >= len(ytdlp_candidates):
                        raise DownloadError(f'网页候选序号超出范围，共找到 {len(ytdlp_candidates)} 个候选')
                    selected = ytdlp_candidates[candidate_position]
                    _emit_file_select(progress_cb, selected, options.web_candidate_index, len(ytdlp_candidates))
                    downloaded = _download_web_candidate(
                        selected,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                    )
                    return _make_result(task, True, downloaded['files'], '')
                else:
                    downloaded_files, last_error = _download_web_candidates(
                        ytdlp_candidates,
                        task,
                        output_root,
                        options,
                        progress_cb,
                        ffmpeg_path=ffmpeg_path,
                    )
                    if downloaded_files:
                        return _make_result(task, True, downloaded_files, '')
            except Exception as exc:
                first_error = exc
    try:
        downloaded = _download_url_with_ytdlp(task.source_url, output_root, options, progress_cb, title_hint=task.target_title)
        return _make_result(task, True, downloaded['files'], '')
    except Exception as exc:
        first_error = exc
    try:
        candidates = _extract_media_candidates(_fetch_webpage_html(task.source_url), task.source_url)
    except Exception as exc:
        raise DownloadError(f'{first_error}; 网页兜底解析失败: {exc}') from exc
    if not candidates:
        raise DownloadError(f'{first_error}; 网页中未找到可下载媒体地址')
    ffmpeg_path = shutil.which('ffmpeg') or ''
    if options.web_download_all_candidates:
        downloaded_files, last_error = _download_web_candidates(
            candidates,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
        )
        if downloaded_files:
            return _make_result(task, True, downloaded_files, '')
        raise DownloadError(f'{first_error}; 全部候选下载失败: {last_error}')
    if options.web_candidate_index is not None:
        candidate_position = options.web_candidate_index - 1
        if candidate_position < 0 or candidate_position >= len(candidates):
            raise DownloadError(f'网页候选序号超出范围，共找到 {len(candidates)} 个候选')
        selected = candidates[candidate_position]
        _emit_file_select(progress_cb, selected, options.web_candidate_index, len(candidates))
        downloaded = _download_web_candidate(
            selected,
            task,
            output_root,
            options,
            progress_cb,
            ffmpeg_path=ffmpeg_path,
        )
        return _make_result(task, True, downloaded['files'], '')
    downloaded_files, last_error = _download_web_candidates(
        candidates,
        task,
        output_root,
        options,
        progress_cb,
        ffmpeg_path=ffmpeg_path,
    )
    if downloaded_files:
        return _make_result(task, True, downloaded_files, '')
    raise DownloadError(f'{first_error}; 兜底媒体地址下载失败: {last_error}')


def _collect_web_media_candidates(source_url: str) -> tuple[list[str], str]:
    ytdlp_candidates: list[str] = []
    try:
        ytdlp_candidates = _extract_ytdlp_entry_candidates(source_url)
    except Exception:
        ytdlp_candidates = []
    if ytdlp_candidates:
        return ytdlp_candidates, 'yt-dlp'
    try:
        html_candidates = _extract_media_candidates(_fetch_webpage_html(source_url), source_url)
    except Exception:
        html_candidates = []
    if html_candidates:
        return html_candidates, 'html'
    if _supports_ytdlp_direct_media(source_url):
        return [source_url], 'page'
    return [], ''


def _download_url_with_ytdlp(
    source_url: str,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    title_hint: str = '',
) -> dict[str, object]:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    before = {item.resolve() for item in output_root.glob('*') if item.is_file()}
    info = YoutubeDL({'quiet': True, 'skip_download': True, 'noplaylist': True}).extract_info(source_url, download=False)
    title = sanitize_filename_component(str(info.get('title') or title_hint or 'video'))
    media_id = sanitize_filename_component(str(info.get('id') or 'video'))
    base_stem = options.filename_template.replace('%(title)s', title).replace('%(id)s', media_id).replace('.%(ext)s', '')
    unique_stem = ensure_unique_stem(output_root, base_stem)
    ydl_opts = {
        'format': 'bv*+ba/b',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'windowsfilenames': True,
        'overwrites': bool(options.overwrite),
        'outtmpl': str(output_root / f'{unique_stem}.%(ext)s'),
        'progress_hooks': [_make_web_progress_hook(progress_cb)],
    }
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg
    if options.web_use_browser_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(source_url, download=True)
    after = {item.resolve() for item in output_root.glob('*') if item.is_file()}
    created = sorted(path for path in after - before if path.is_file())
    if not created:
        matched = sorted(output_root.glob(f'{unique_stem}.*'))
        created = [path.resolve() for path in matched if path.is_file()]
    if not created:
        raise DownloadError('网页视频下载完成，但未找到输出文件')
    _emit(progress_cb, f'网页 OK -> {created[0].name}')
    return {
        'success': True,
        'files': created,
    }


def _fetch_webpage_html(url: str) -> str:
    request = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': url,
        },
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return response.read().decode(charset, errors='ignore')


def _extract_media_candidates(html_text: str, page_url: str) -> list[str]:
    normalized = unescape(str(html_text or ''))
    normalized = normalized.replace('\\/', '/').replace('\\u002F', '/').replace('\\u002f', '/')
    unique: dict[str, None] = {}
    for pattern in (MEDIA_URL_RE, RELATIVE_MEDIA_RE):
        for match in pattern.finditer(normalized):
            raw_url = match.group('url')
            if not raw_url:
                continue
            if raw_url.startswith('//'):
                candidate = f'{urlparse(page_url).scheme}:{raw_url}'
            else:
                candidate = urljoin(page_url, raw_url)
            unique.setdefault(candidate, None)
    return list(unique.keys())


def _extract_ytdlp_entry_candidates(page_url: str) -> list[str]:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    info = YoutubeDL({'quiet': True, 'skip_download': True}).extract_info(page_url, download=False)
    entries = info.get('entries')
    if not isinstance(entries, Iterable):
        return []
    unique: dict[str, None] = {}
    _collect_ytdlp_entry_candidates(entries, page_url, unique)
    return list(unique.keys())


def _collect_ytdlp_entry_candidates(entries: object, page_url: str, unique: dict[str, None]) -> None:
    if not isinstance(entries, Iterable) or isinstance(entries, (str, bytes, dict)):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        nested_entries = entry.get('entries')
        if nested_entries is not None:
            _collect_ytdlp_entry_candidates(nested_entries, page_url, unique)
        for key in ('url', 'webpage_url', 'original_url'):
            candidate = _normalize_web_candidate_url(entry.get(key), page_url)
            if candidate:
                unique.setdefault(candidate, None)
                break


def _supports_ytdlp_direct_media(source_url: str) -> bool:
    _require_web_backend()
    from yt_dlp import YoutubeDL

    info = YoutubeDL({'quiet': True, 'skip_download': True, 'noplaylist': True}).extract_info(source_url, download=False)
    if not isinstance(info, dict):
        return False
    return bool(info.get('url') or info.get('formats') or info.get('id') or info.get('title'))


def _normalize_web_candidate_url(raw_url: object, page_url: str) -> str:
    text = str(raw_url or '').strip()
    if not text:
        return ''
    if text.startswith('//'):
        return f'{urlparse(page_url).scheme}:{text}'
    if text.startswith('/'):
        return urljoin(page_url, text)
    parsed = urlparse(text)
    if parsed.scheme in {'http', 'https'} and parsed.netloc:
        return text
    return ''


def _download_m3u8_with_ffmpeg(
    media_url: str,
    task: DownloadTask,
    output_root: Path,
    options: DownloadOptions,
    progress_cb: ProgressCallback | None,
    ffmpeg_path: str = '',
) -> dict[str, object]:
    ffmpeg = ffmpeg_path or shutil.which('ffmpeg')
    if not ffmpeg:
        raise DownloadError('未检测到 ffmpeg，无法直接下载 m3u8')
    base_stem = ensure_unique_stem(output_root, sanitize_filename_component(task.target_title or 'video'))
    output_path = ensure_unique_path(output_root / f'{base_stem}.mp4')
    command = [
        ffmpeg,
        '-y' if options.overwrite else '-n',
        '-i',
        media_url,
        '-c',
        'copy',
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or 'ffmpeg 下载失败').strip()
        raise DownloadError(message)
    _emit(progress_cb, f'网页 OK -> {output_path.name}')
    return {
        'success': True,
        'files': [output_path],
    }


def _make_web_progress_hook(progress_cb: ProgressCallback | None):
    def hook(status: dict[str, object]) -> None:
        state = str(status.get('status') or '')
        if state == 'downloading':
            filename = Path(str(status.get('filename') or '')).name
            percent = _resolve_web_percent_text(status)
            speed = _resolve_web_speed_text(status)
            eta = _normalize_progress_text(status.get('_eta_str', ''))
            text = _build_download_log_message(filename, speed, percent)
            normalized_percent = percent.replace('%', '').strip()
            try:
                _emit(progress_cb, f'__HYL_PROGRESS__|web_percent|percent={float(normalized_percent)}')
            except ValueError:
                pass
            _emit_web_transfer_progress(progress_cb, filename, normalized_percent, speed, eta)
            _emit(progress_cb, text)
        elif state == 'finished':
            filename = Path(str(status.get('filename') or '')).name
            _emit(progress_cb, f'网页处理完成 {filename}')
    return hook


def _make_telegram_progress_callback(progress_cb: ProgressCallback | None, file_name: str):
    clean_name = sanitize_filename_component(Path(str(file_name or 'telegram_media')).name, fallback='telegram_media')
    started_at = monotonic()
    last_emitted_at = started_at
    last_percent = -1.0

    def callback(received: int, total: int) -> None:
        nonlocal last_emitted_at, last_percent
        current = max(0, int(received or 0))
        total_bytes = max(0, int(total or 0))
        percent = (current * 100.0 / total_bytes) if total_bytes else 0.0
        now = monotonic()
        if current < total_bytes and now - last_emitted_at < 0.35 and percent - last_percent < 1.0:
            return
        elapsed = max(now - started_at, 1e-6)
        speed_value = current / elapsed if current > 0 else 0.0
        speed_text = _format_byte_rate(speed_value)
        eta_text = ''
        if speed_value > 0 and total_bytes > current:
            eta_text = _format_eta_seconds(int((total_bytes - current) / speed_value))
        parts = [f'name={clean_name}', f'percent={percent:.2f}']
        if speed_text:
            parts.append(f'speed={speed_text}')
        if eta_text:
            parts.append(f'eta={eta_text}')
        _emit(progress_cb, '__HYL_PROGRESS__|tg_media|' + '|'.join(parts))
        _emit(progress_cb, _build_download_log_message(clean_name, speed_text, _format_progress_percent(percent)))
        last_emitted_at = now
        last_percent = percent

    return callback


def _emit_web_transfer_progress(
    progress_cb: ProgressCallback | None,
    file_name: str,
    percent_text: str,
    speed_text: str,
    eta_text: str,
) -> None:
    parts = [f'name={sanitize_filename_component(Path(str(file_name or "video")).name, fallback="video")}']
    try:
        parts.append(f'percent={float(percent_text)}')
    except ValueError:
        pass
    if speed_text:
        parts.append(f'speed={speed_text}')
    if eta_text:
        parts.append(f'eta={eta_text}')
    _emit(progress_cb, '__HYL_PROGRESS__|web_status|' + '|'.join(parts))


def _normalize_progress_text(value: object) -> str:
    text = ANSI_ESCAPE_RE.sub('', str(value or ''))
    return WHITESPACE_RE.sub(' ', text).strip()


def _resolve_web_percent_text(status: dict[str, object]) -> str:
    percent = _normalize_progress_text(status.get('_percent_str', ''))
    if percent:
        return percent
    numeric_percent = _coerce_float(status.get('_percent'))
    if numeric_percent is not None:
        return _format_progress_percent(numeric_percent)
    downloaded = _coerce_float(status.get('downloaded_bytes'))
    total = _coerce_float(status.get('total_bytes'))
    estimate = _coerce_float(status.get('total_bytes_estimate'))
    denominator = total or estimate or 0.0
    if downloaded is not None and denominator > 0:
        return _format_progress_percent(downloaded * 100.0 / denominator)
    return ''


def _resolve_web_speed_text(status: dict[str, object]) -> str:
    speed = _normalize_progress_text(status.get('_speed_str', ''))
    if speed:
        return speed
    speed_value = _coerce_float(status.get('speed'))
    if speed_value is not None:
        return _format_byte_rate(speed_value)
    return ''


def _coerce_float(value: object) -> float | None:
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_download_log_message(file_name: str, speed_text: str, percent_text: str) -> str:
    clean_name = str(file_name or 'video').strip() or 'video'
    clean_speed = _normalize_progress_text(speed_text) or '--'
    clean_percent = _normalize_progress_text(percent_text) or '--'
    return f'正在下载 "{clean_name}" "{clean_speed}" "{clean_percent}"'


def _format_progress_percent(percent: float) -> str:
    value = max(0.0, min(100.0, float(percent or 0.0)))
    text = f'{value:.1f}'.rstrip('0').rstrip('.')
    return f'{text}%'


def _format_byte_rate(bytes_per_second: float) -> str:
    rate = max(0.0, float(bytes_per_second or 0.0))
    if rate <= 0:
        return ''
    units = ['B/s', 'KiB/s', 'MiB/s', 'GiB/s']
    unit_index = 0
    while rate >= 1024.0 and unit_index < len(units) - 1:
        rate /= 1024.0
        unit_index += 1
    precision = 0 if unit_index == 0 else 1
    return f'{rate:.{precision}f} {units[unit_index]}'


def _format_eta_seconds(seconds: int) -> str:
    remaining = max(0, int(seconds or 0))
    hours, remainder = divmod(remaining, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f'{hours:d}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def _make_result(task: DownloadTask, success: bool, files: Iterable[Path], error: str) -> dict[str, object]:
    file_list = [str(Path(path)) for path in files]
    return {
        'source_url': task.source_url,
        'source_kind': task.source_kind,
        'title': task.target_title,
        'success': success,
        'error': error,
        'downloaded_count': len(file_list),
        'files': file_list,
    }


def _emit(progress_cb: ProgressCallback | None, message: str) -> None:
    if progress_cb is not None and message:
        progress_cb(message)


def _emit_task_start(progress_cb: ProgressCallback | None, index: int, total: int, task: DownloadTask) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|task_start|index={index}|total={total}|url={task.source_url}')


def _emit_task_done(progress_cb: ProgressCallback | None, completed: int, total: int) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|task_done|completed={completed}|total={total}')


def _emit_scan_progress(progress_cb: ProgressCallback | None, scanned: int, matched: int) -> None:
    _emit(progress_cb, f'__HYL_PROGRESS__|tg_scan|matched={matched}|scanned={scanned}')


def _emit_file_select(progress_cb: ProgressCallback | None, file_label: str, index: int = 0, total: int = 0) -> None:
    parsed = urlparse(str(file_label or ''))
    label = Path(parsed.path).name if parsed.path else str(file_label or '')
    clean_label = sanitize_filename_component(label, fallback='media')
    _emit(progress_cb, f'__HYL_PROGRESS__|file|index={index}|name={clean_label}|total={total}')
