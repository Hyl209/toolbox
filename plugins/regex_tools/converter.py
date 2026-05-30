from __future__ import annotations

import re
import signal
import threading
from contextlib import contextmanager


class RegexToolError(Exception):
    pass


_REGEX_TIMEOUT_SECONDS = 5


@contextmanager
def _regex_timeout(seconds: int = _REGEX_TIMEOUT_SECONDS):
    """Best-effort timeout for regex operations to mitigate ReDoS."""
    if hasattr(signal, 'SIGALRM') and threading.current_thread() is threading.main_thread():
        def _handler(signum, frame):
            raise RegexToolError(f"正则匹配超时（>{seconds}s），可能存在灾难性回溯")
        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        # Windows fallback: run regex in a worker thread with timeout
        import concurrent.futures
        _timeout_holder = [seconds]
        class _TimeoutProxy:
            """Allow the context body to set the timeout value."""
            def set_timeout(self, s):
                _timeout_holder[0] = s
        proxy = _TimeoutProxy()
        yield proxy
        # The actual timeout enforcement happens at the call site via _run_with_timeout
        return


def _run_with_timeout(func, seconds: int = _REGEX_TIMEOUT_SECONDS):
    """Run *func()* in a thread, raise RegexToolError on timeout (Windows-safe)."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(func)
        try:
            return future.result(timeout=seconds)
        except concurrent.futures.TimeoutError:
            raise RegexToolError(f"正则匹配超时（>{seconds}s），可能存在灾难性回溯")


def _require_text(value: str, label: str) -> str:
    text = str(value)
    if not text:
        raise RegexToolError(f"请输入{label}")
    return text


def compile_pattern(pattern: str, ignore_case: bool = False, multiline: bool = True) -> re.Pattern:
    """Compile regex. multiline=True (default): ^/$ match line boundaries."""
    pattern = _require_text(pattern, "正则表达式")
    flags = 0
    if ignore_case:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.MULTILINE
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        raise RegexToolError(f"正则表达式无效: {exc}") from exc


def extract_matches(
    text: str,
    pattern: str,
    group: int | str = 0,
    ignore_case: bool = False,
    multiline: bool = True,
) -> list[str]:
    source = _require_text(text, "待处理文本")
    regex = compile_pattern(pattern, ignore_case=ignore_case, multiline=multiline)
    results: list[str] = []

    def _do_match():
        for match in regex.finditer(source):
            try:
                value = match.group(group)
            except (IndexError, KeyError) as exc:
                raise RegexToolError(f"分组不存在: {group}") from exc
            results.append(value)

    if hasattr(signal, 'SIGALRM'):
        with _regex_timeout():
            _do_match()
    else:
        _run_with_timeout(_do_match)
    return results


def extract_matches_text(text: str, pattern: str, **kwargs) -> str:
    return "\n".join(extract_matches(text, pattern, **kwargs))


def replace_matches(
    text: str,
    pattern: str,
    replacement: str = "",
    ignore_case: bool = False,
    multiline: bool = True,
) -> str:
    source = _require_text(text, "待处理文本")
    regex = compile_pattern(pattern, ignore_case=ignore_case, multiline=multiline)

    def _do_sub():
        try:
            return regex.sub(str(replacement), source)
        except re.error as exc:
            raise RegexToolError(f"替换表达式无效: {exc}") from exc

    if hasattr(signal, 'SIGALRM'):
        with _regex_timeout():
            return _do_sub()
    else:
        return _run_with_timeout(_do_sub)


def regex_summary(text: str, pattern: str, ignore_case: bool = False, multiline: bool = True) -> dict[str, int]:
    matches = extract_matches(text, pattern, ignore_case=ignore_case, multiline=multiline)
    return {
        "matches": len(matches),
        "unique": len(set(matches)),
    }
