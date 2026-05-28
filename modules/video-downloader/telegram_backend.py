"""Telegram login, authorization, and media download."""
from __future__ import annotations

import asyncio
import importlib.util
from datetime import date, datetime, time, timezone
from pathlib import Path

from .models import (
    CancelledError, DownloadError, DownloadOptions, DownloadTask,
    ProgressCallback, TelegramConfig, TelegramUrlParts,
)
from . import _shared as _s
from .progress import (
    _emit, _emit_scan_progress, _emit_task_done, _emit_task_start,
    _make_telegram_progress_callback, _make_result,
)
from .source_parser import _coerce_tasks


def _require_telegram_backend() -> None:
    if importlib.util.find_spec('telethon') is None:
        raise DownloadError('未安装 Telethon，无法使用 Telegram 下载')


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


def check_telegram_authorization(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_check_telegram_authorization_async(config))


def begin_telegram_login(config: TelegramConfig) -> dict[str, object]:
    return asyncio.run(_begin_telegram_login_async(config))


def complete_telegram_login(config: TelegramConfig, code: str, phone_code_hash: str) -> dict[str, object]:
    return asyncio.run(_complete_telegram_login_async(config, code, phone_code_hash))


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
            _emit_task_start(progress_cb, index, total_tasks, task)
            results[index] = _make_result(task, False, [], 'Telegram 配置缺失')
            _emit_task_done(progress_cb, len(results), total_tasks)
        return results
    try:
        client = await _create_telegram_client(config)
        await client.connect()
        if not await client.is_user_authorized():
            message = 'Telegram 尚未登录，请先在页面完成验证码登录'
            for index, task in entries:
                _emit_task_start(progress_cb, index, total_tasks, task)
                results[index] = _make_result(task, False, [], message)
                _emit_task_done(progress_cb, len(results), total_tasks)
            return results
        for index, task in entries:
            _emit_task_start(progress_cb, index, total_tasks, task)
            try:
                results[index] = await _download_single_telegram_task(client, task, output_root, options, progress_cb)
            except CancelledError:
                results[index] = _make_result(task, False, [], '下载已取消')
                raise
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
            client, message, output_folder,
            fallback_prefix=task.target_title or 'telegram_video',
            options=options, progress_cb=progress_cb,
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
            client, message, output_folder,
            fallback_prefix=f'{task.target_title or "telegram_video"}_{message.id}',
            options=options, progress_cb=progress_cb,
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
            try:
                return await client.get_entity(f'https://t.me/+{parts.invite_hash}')
            except Exception:
                pass
            async for dialog in client.iter_dialogs():
                if _dialog_matches_invite(dialog, parts.invite_hash):
                    return dialog.entity
            raise DownloadError('无法根据邀请链接解析聊天，请确认账号已加入该会话')
        except Exception as exc:
            raise DownloadError(f'无法访问 Telegram 邀请链接: {exc}') from exc
        if updates is not None:
            chats = getattr(updates, 'chats', None) or []
            if chats:
                return chats[0]
        raise DownloadError('邀请链接解析失败，未返回聊天信息')
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
    client, message, output_dir: Path, fallback_prefix: str,
    options: DownloadOptions, progress_cb: ProgressCallback | None = None,
) -> Path:
    file_info = getattr(message, 'file', None)
    original_name = ''
    suffix = ''
    if file_info is not None:
        original_name = getattr(file_info, 'name', '') or ''
        suffix = getattr(file_info, 'ext', '') or ''
    if _is_photo_message(message) and options.telegram_include_photos:
        suffix = Path(original_name).suffix or suffix or '.jpg'
        target_name = _s.sanitize_filename_component(Path(original_name).stem or fallback_prefix) + suffix
    elif original_name:
        target_name = _s.sanitize_filename_component(Path(original_name).stem) + (Path(original_name).suffix or suffix or '.mp4')
    else:
        target_name = _s.sanitize_filename_component(fallback_prefix) + (suffix or '.mp4')
    target_path = _s.ensure_unique_path(output_dir / target_name)
    downloaded = await client.download_media(
        message, file=str(target_path),
        progress_callback=_make_telegram_progress_callback(progress_cb, target_path.name),
    )
    if not downloaded:
        raise DownloadError('Telegram 视频下载失败')
    return Path(downloaded)


def _parse_telegram_url(url: str) -> TelegramUrlParts:
    from urllib.parse import urlparse
    parsed = urlparse(_s._normalize_url_text(url))
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


def _dialog_matches_invite(dialog, invite_hash: str) -> bool:
    invite_lower = str(invite_hash or '').lower()
    if not invite_lower:
        return False
    username = str(getattr(dialog.entity, 'username', '') or '').lower()
    return bool(username and invite_lower in username)


def _resolve_task_output_dir(output_root: Path, task: DownloadTask, default_name: str = '') -> Path:
    subdir = _s.sanitize_filename_component(task.output_subdir or default_name, fallback='').strip()
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
