from __future__ import annotations

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path


class ArchiveExtractError(Exception):
    pass


_SEVEN_ZIP_SUCCESS_CODES = {0, 1}


def _iter_7z_candidates():
    yielded = set()
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
                [seven_zip, "l", "-y", "-p", str(path)],
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


def _zip_passwords(password: str):
    if not password:
        yield None
        return
    seen = set()
    for encoding in ("utf-8", "gbk"):
        try:
            pwd = password.encode(encoding)
        except UnicodeEncodeError:
            continue
        if pwd not in seen:
            seen.add(pwd)
            yield pwd


def _safe_zip_extract(archive_path: Path, output_dir: Path, password: str = "") -> int:
    count = 0
    with zipfile.ZipFile(archive_path) as zf:
        for member in zf.infolist():
            target = output_dir / member.filename
            _ensure_inside(output_dir, target)
        errors = []
        for pwd in _zip_passwords(password):
            try:
                zf.extractall(output_dir, pwd=pwd)
                break
            except RuntimeError as exc:
                errors.append(exc)
        else:
            raise errors[-1]
        count = len(zf.infolist())
    return count


def _safe_tar_extract(archive_path: Path, output_dir: Path) -> int:
    count = 0
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
        count = len(members)
    return count


def _extract_with_7z(archive_path: Path, output_dir: Path, password: str = "") -> int:
    seven_zip = _find_7z_for_archive(archive_path)
    if not seven_zip:
        raise ArchiveExtractError("未找到 7z，无法解压该格式")
    args = [seven_zip, "x", "-y", f"-o{output_dir}"]
    if password:
        args.append(f"-p{password}")
    args.append(str(archive_path))
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=None,
        check=False,
    )
    if result.returncode not in _SEVEN_ZIP_SUCCESS_CODES:
        message = (result.stderr or result.stdout or "7z 解压失败").strip()
        raise ArchiveExtractError(message)
    return sum(1 for item in output_dir.rglob("*") if item.is_file())


def extract_archive(archive_path: str | Path, output_dir: str | Path, password: str = "") -> int:
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
        return _extract_with_7z(archive, target, password)
    raise ArchiveExtractError("无法识别压缩包格式")
