from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Callable, Generator


class ArchiveExtractError(Exception):
    pass


_SEVEN_ZIP_SUCCESS_CODES = {0, 1}


def _iter_7z_candidates() -> Generator[str, None, None]:
    yielded: set[str] = set()
    candidates = [
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
        Path(r"C:\Program Files\AMD\CIM\Bin64\7z.exe"),
        Path(r"C:\Program Files\AMD\CNext\CNext\7z.exe"),
        Path(r"C:\Program Files\AMD\AMDInstallManager\7z.exe"),
    ]
    for name in ("7z", "7za", "7zr"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    for candidate in candidates:
        key = str(candidate).lower()
        if key not in yielded and candidate.is_file():
            yielded.add(key)
            yield str(candidate)


def _find_7z() -> str:
    return next(_iter_7z_candidates(), "")


def _detect_with_7z(path: Path) -> tuple[str, str]:
    for seven_zip in _iter_7z_candidates():
        try:
            result = subprocess.run(
                [seven_zip, "l", "-y", str(path)],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            continue
        output = f"{result.stdout}\n{result.stderr}"
        if "Cannot open encrypted archive" in output or "Wrong password" in output:
            return "7z-encrypted", seven_zip
        if result.returncode not in _SEVEN_ZIP_SUCCESS_CODES:
            continue
        for line in result.stdout.splitlines():
            if line.startswith("Type = "):
                archive_type = line.split("=", 1)[1].strip().lower()
                detected = f"7z-{archive_type}" if archive_type else "7z"
                return detected, seven_zip
    return "", ""


def _detect_7z_archive_type(path: Path) -> str:
    archive_type, _seven_zip = _detect_with_7z(path)
    return archive_type


def _find_7z_for_archive(path: Path) -> str:
    _archive_type, seven_zip = _detect_with_7z(path)
    if seven_zip:
        return seven_zip
    return _find_7z()


def detect_archive_type(path: str | Path) -> str:
    archive = Path(path)
    if not archive.is_file():
        return ""
    if zipfile.is_zipfile(archive):
        return "zip"
    if tarfile.is_tarfile(archive):
        return "tar"
    return _detect_7z_archive_type(archive)


def is_supported_archive(path: str | Path) -> bool:
    return bool(detect_archive_type(path))


def _ensure_inside(base_dir: Path, target: Path) -> None:
    base = base_dir.resolve()
    resolved = target.resolve()
    if resolved != base and base not in resolved.parents:
        raise ArchiveExtractError(f"压缩包包含不安全路径: {target.name}")


def _zip_passwords(password: str) -> Generator[bytes | None, None, None]:
    if not password:
        yield None
        return
    seen: set[bytes] = set()
    for encoding in ("utf-8", "gbk", "cp437"):
        try:
            pwd = password.encode(encoding)
        except UnicodeEncodeError:
            continue
        if pwd not in seen:
            seen.add(pwd)
            yield pwd


def _safe_zip_extract(archive_path: Path, output_dir: Path, password: str = "") -> int:
    with zipfile.ZipFile(archive_path) as zf:
        for member in zf.infolist():
            target = output_dir / member.filename
            _ensure_inside(output_dir, target)
        errors: list[Exception] = []
        for pwd in _zip_passwords(password):
            try:
                zf.extractall(output_dir, pwd=pwd)
                break
            except RuntimeError as exc:
                errors.append(exc)
        else:
            raise errors[-1]
        return len(zf.infolist())


def _safe_tar_extract(archive_path: Path, output_dir: Path) -> int:
    with tarfile.open(archive_path) as tf:
        members = tf.getmembers()
        for member in members:
            target = output_dir / member.name
            _ensure_inside(output_dir, target)
            if member.issym() or member.islnk():
                link_target = output_dir / member.linkname
                _ensure_inside(output_dir, link_target)
        try:
            tf.extractall(output_dir, members=members, filter="data")
        except TypeError:
            tf.extractall(output_dir, members=members)
        return len(members)


def _escape_bat_password(password: str) -> str:
    """Escape password for safe use in a batch file `set "VAR=..."` command."""
    # % must be doubled (variable expansion); ^ & | < > need caret escaping
    password = password.replace("%", "%%")
    for ch in "^&|<>":
        password = password.replace(ch, f"^{ch}")
    return password


def _build_7z_cmd(seven_zip: str, output_dir: Path, archive_path: Path, password: str) -> tuple[list[str], dict]:
    """Build 7z command and env. Uses batch wrapper on Windows to hide password from process list."""
    args = [seven_zip, "x", "-y", f"-o{output_dir}", str(archive_path)]
    env = os.environ.copy()
    if not password:
        return args, env
    # On Windows, write a temp batch file to avoid password in process list
    if os.name == "nt":
        escaped = _escape_bat_password(password)
        bat = tempfile.NamedTemporaryFile("w", suffix=".bat", delete=False, encoding="utf-8")
        bat.write(f'@echo off\nset "ARCHIVE_PASS={escaped}"\n')
        bat.write(f'"{seven_zip}" x -y "-o{output_dir}" "-p%ARCHIVE_PASS%" "{archive_path}"\n')
        bat.write("exit /b %errorlevel%\n")
        bat.close()
        return ["cmd", "/c", bat.name], {"_bat_path": bat.name, **env}
    # Fallback: direct password (7z has no stdin-password support)
    args.insert(4, f"-p{password}")
    return args, env


def _extract_with_7z(
    archive_path: Path,
    output_dir: Path,
    password: str = "",
    abort: threading.Event | None = None,
    log_callback: Callable[[str], None] | None = None,
) -> Generator[str, None, int]:
    """Yields real-time log lines; returns file count on completion."""
    seven_zip = _find_7z_for_archive(archive_path)
    if not seven_zip:
        raise ArchiveExtractError("未找到 7z，无法解压该格式")

    existing_files = {p.resolve() for p in output_dir.rglob("*") if p.is_file()}

    if abort is not None and abort.is_set():
        raise ArchiveExtractError("解压已取消")

    args, env = _build_7z_cmd(seven_zip, output_dir, archive_path, password)
    bat_path = env.pop("_bat_path", None)

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        assert proc.stdout is not None
        for line in proc.stdout:
            if abort is not None and abort.is_set():
                proc.kill()
                proc.wait()
                raise ArchiveExtractError("解压已取消")
            stripped = line.rstrip()
            if stripped:
                yield stripped

        proc.wait()
    finally:
        if bat_path:
            try:
                os.unlink(bat_path)
            except OSError:
                pass

    if proc.returncode not in _SEVEN_ZIP_SUCCESS_CODES:
        raise ArchiveExtractError(f"7z 解压失败 (返回码 {proc.returncode})")

    new_files = {p.resolve() for p in output_dir.rglob("*") if p.is_file()}
    return len(new_files - existing_files)


def iter_extract_archive(
    archive_path: str | Path,
    output_dir: str | Path,
    password: str = "",
    abort: threading.Event | None = None,
    log_callback: object = None,
) -> Generator[str, None, int]:
    """Extract archive, yielding real-time log lines. Returns file count.

    For zip/tar: yields nothing, returns count directly.
    For 7z: yields 7z output lines, returns count.
    """
    archive = Path(archive_path)
    target = Path(output_dir)
    if not archive.is_file():
        raise ArchiveExtractError("请选择有效的压缩包文件")
    archive_type = detect_archive_type(archive)
    if not archive_type:
        raise ArchiveExtractError("无法识别压缩包格式")
    target.mkdir(parents=True, exist_ok=True)
    if archive_type == "zip":
        return _safe_zip_extract(archive, target, password)
    if archive_type == "tar":
        return _safe_tar_extract(archive, target)
    if archive_type.startswith("7z"):
        return (yield from _extract_with_7z(archive, target, password, abort, log_callback))
    raise ArchiveExtractError("无法识别压缩包格式")



def extract_archive(
    archive_path: str | Path,
    output_dir: str | Path,
    password: str = "",
    abort: threading.Event | None = None,
    log_callback: Callable[[str], None] | None = None,
) -> int:
    """Extract archive synchronously and return the number of extracted entries."""
    gen = iter_extract_archive(archive_path, output_dir, password, abort, log_callback)
    while True:
        try:
            line = next(gen)
        except StopIteration as exc:
            return int(exc.value or 0)
        if log_callback is not None:
            log_callback(line)

def extract_archive_sync(
    archive_path: str | Path,
    output_dir: str | Path,
    password: str = "",
    abort: threading.Event | None = None,
    log_callback: object = None,
) -> int:
    """Backward-compatible synchronous wrapper."""
    return extract_archive(archive_path, output_dir, password, abort, log_callback)
