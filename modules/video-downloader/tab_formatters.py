from __future__ import annotations

from ._shared import classify_source, TELEGRAM_HOSTS
from .tab_constants import SUMMARY_EMPTY_TEXT, TELEGRAM_ONLY_ERROR, WEB_ONLY_ERROR


def normalize_source_mode(source_mode: str) -> str:
    cleaned = str(source_mode or '').strip().lower()
    return cleaned if cleaned in {'mixed', 'telegram', 'web'} else 'mixed'


def _guess_source_kind(url: str) -> str:
    """Classify a URL as telegram_message, telegram_chat, or web.

    Delegates to _shared.classify_source for consistent logic.
    Falls back to 'web' for invalid/empty input (UI display context).
    """
    try:
        return classify_source(url)
    except (ValueError, Exception):
        return 'web'


def format_video_task_summary(urls: list[str]) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    telegram_message = 0
    telegram_chat = 0
    web = 0
    for url in urls:
        kind = _guess_source_kind(url)
        if kind == 'telegram_message':
            telegram_message += 1
        elif kind == 'telegram_chat':
            telegram_chat += 1
        else:
            web += 1
    lines = [
        f'任务总数: {len(urls)}',
        f'Telegram 消息: {telegram_message}',
        f'Telegram 群/频道: {telegram_chat}',
        f'网页视频任务: {web}',
    ]
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)


def format_web_task_summary(urls: list[str], web_scan_results: dict[str, dict[str, object]] | None = None) -> str:
    if not urls:
        return SUMMARY_EMPTY_TEXT
    lines = [f'网页链接: {len(urls)}']
    if web_scan_results:
        lines.append('扫描结果:')
        for url in urls[:3]:
            result = web_scan_results.get(url)
            if not result:
                continue
            if result.get('success'):
                count = int(result.get('candidate_count', 0) or 0)
                lines.append(f'{count} 个候选: {url}')
            else:
                lines.append(f'扫描失败: {url}')
    else:
        lines.append('点击"扫描候选"可查看每个页面的候选视频')
    preview = urls[:3]
    if preview:
        lines.append('预览:')
        lines.extend(preview)
    return '\n'.join(lines)

def format_backend_status(status: dict[str, dict[str, object]]) -> str:
    lines: list[str] = []
    for key in ('telethon', 'yt_dlp', 'aria2c', 'ffmpeg'):
        item = status.get(key, {})
        available = bool(item.get('available'))
        label = str(item.get('label') or key)
        message = str(item.get('message') or '')
        prefix = '可用' if available else '缺失'
        lines.append(f'{prefix} {label}: {message}')
    return '\n'.join(lines)


def build_source_mode_summary(urls: list[str], source_mode: str, web_scan_results: dict[str, dict[str, object]] | None = None) -> str:
    mode = normalize_source_mode(source_mode)
    if not urls or mode == 'mixed':
        return format_video_task_summary(urls)
    if mode == 'telegram':
        summary = format_video_task_summary(urls)
        mismatched = [url for url in urls if _guess_source_kind(url) == 'web']
        if mismatched:
            return summary + f'当前页不匹配链接'
        return summary
    web_urls = [url for url in urls if _guess_source_kind(url) == 'web']
    mismatched = [url for url in urls if _guess_source_kind(url) != 'web']
    if mismatched:
        return format_web_task_summary(web_urls) + f'当前页不匹配链接'
    return format_web_task_summary(web_urls)


def validate_source_mode_urls(urls: list[str], source_mode: str) -> list[str]:
    mode = normalize_source_mode(source_mode)
    if mode == 'mixed' or not urls:
        return []
    if mode == 'telegram':
        return [TELEGRAM_ONLY_ERROR] if any(_guess_source_kind(url) == 'web' for url in urls) else []
    return [WEB_ONLY_ERROR] if any(_guess_source_kind(url) != 'web' for url in urls) else []


def filter_tasks_for_source_mode(tasks: list[object], source_mode: str) -> list[object]:
    mode = normalize_source_mode(source_mode)
    if mode == 'mixed':
        return tasks
    filtered: list[object] = []
    for task in tasks:
        kind = str(getattr(task, 'source_kind', ''))
        if mode == 'telegram' and kind.startswith('telegram'):
            filtered.append(task)
        elif mode == 'web' and kind == 'web':
            filtered.append(task)
    return filtered


def build_progress_marker(kind: str, **values: object) -> str:
    parts = [f'{key}={values[key]}' for key in sorted(values.keys())]
    return '__HYL_PROGRESS__|' + kind + ('|' + '|'.join(parts) if parts else '')


def parse_progress_marker(message: str) -> tuple[str, dict[str, str]] | None:
    text = str(message or '')
    if not text.startswith('__HYL_PROGRESS__|'):
        return None
    parts = text.split('|')
    if len(parts) < 2:
        return None
    kind = parts[1]
    payload: dict[str, str] = {}
    for item in parts[2:]:
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        payload[key] = value
    return kind, payload


def summarize_download_results(results: list[dict[str, object]]) -> list[str]:
    success_count = sum(1 for item in results if item.get('success'))
    failed_count = sum(1 for item in results if not item.get('success'))
    downloaded_count = sum(int(item.get('downloaded_count', 0) or 0) for item in results)
    return [
        f'任务总数: {len(results)}',
        f'成功任务: {success_count}',
        f'失败任务: {failed_count}',
        f'下载文件: {downloaded_count}',
    ]
