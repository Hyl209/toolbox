from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


SUPPORTED_ALGORITHMS = ("md5", "sha1", "sha256")
_HASH_LENGTHS = {
    32: "md5",
    40: "sha1",
    64: "sha256",
}


class FileHashError(Exception):
    pass


def normalize_checksum(value: str) -> str:
    return "".join(str(value).strip().lower().split())


def detect_algorithm(expected_checksum: str) -> str:
    checksum = normalize_checksum(expected_checksum)
    algorithm = _HASH_LENGTHS.get(len(checksum))
    if not algorithm:
        raise FileHashError("无法根据校验值长度识别算法")
    return algorithm


def calculate_file_hash(path: str | Path, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    source = Path(path)
    if not source.is_file():
        raise FileHashError("请选择有效文件")
    algo = algorithm.lower()
    if algo not in SUPPORTED_ALGORITHMS:
        raise FileHashError(f"不支持的哈希算法: {algorithm}")
    digest = hashlib.new(algo)
    with source.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_hashes(
    path: str | Path,
    algorithms: Iterable[str] = SUPPORTED_ALGORITHMS,
    chunk_size: int = 1024 * 1024,
) -> dict[str, str]:
    source = Path(path)
    if not source.is_file():
        raise FileHashError("请选择有效文件")

    normalized = tuple(algorithm.lower() for algorithm in algorithms)
    for algorithm in normalized:
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise FileHashError(f"不支持的哈希算法: {algorithm}")

    digests = {algorithm: hashlib.new(algorithm) for algorithm in normalized}
    with source.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            for digest in digests.values():
                digest.update(chunk)
    return {algorithm: digest.hexdigest() for algorithm, digest in digests.items()}


def verify_file_hash(path: str | Path, expected_checksum: str, algorithm: str = "auto") -> dict[str, object]:
    expected = normalize_checksum(expected_checksum)
    if not expected:
        raise FileHashError("请输入要校验的哈希值")
    algo = detect_algorithm(expected) if algorithm == "auto" else algorithm.lower()
    actual = calculate_file_hash(path, algo)
    return {
        "algorithm": algo,
        "expected": expected,
        "actual": actual,
        "matched": actual == expected,
    }
