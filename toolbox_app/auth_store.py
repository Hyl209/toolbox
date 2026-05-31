from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from toolbox_app.password_policy import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    validate_password_policy,
)

# Cache for loaded users to avoid repeated file reads (keyed by mtime)
_users_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}


def load_users(store_path: str | Path) -> list[dict[str, str]]:
    path = Path(store_path)
    cache_key = str(path)

    # Check cache first
    if cache_key in _users_cache:
        mtime, cached_users = _users_cache[cache_key]
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime == mtime:
                return cached_users
        except OSError:
            pass

    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(data, list):
        return []
    users: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        username = str(item.get('username', '')).strip()
        password_hash = str(item.get('password_hash', '')).strip()
        if username and password_hash:
            users.append({'username': username, 'password_hash': password_hash})

    # Update cache
    try:
        _users_cache[cache_key] = (path.stat().st_mtime, users)
    except OSError:
        pass

    return users


def save_users(store_path: str | Path, users: list[dict[str, str]]) -> None:
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {'username': item['username'], 'password_hash': item['password_hash']}
        for item in users
        if item.get('username') and item.get('password_hash')
    ]
    import tempfile
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Invalidate cache
    _users_cache.pop(str(path), None)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 300_000)
    return f'pbkdf2${salt.hex()}${digest.hex()}'


def verify_password(password: str, stored_hash: str) -> bool:
    parts = stored_hash.split('$')
    if len(parts) == 3 and parts[0] == 'pbkdf2':
        salt = bytes.fromhex(parts[1])
        expected = bytes.fromhex(parts[2])
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 300_000)
        return hmac.compare_digest(actual, expected)
    # Legacy SHA-256 format (backward compat)
    try:
        salt_hex, expected_hex = stored_hash.split('$', 1)
    except ValueError:
        return False
    actual = hashlib.sha256(f'{salt_hex}:{password}'.encode('utf-8')).hexdigest()
    return hmac.compare_digest(actual, expected_hex)


def find_user(users: list[dict[str, str]], username: str):
    target = username.strip().casefold()
    for item in users:
        if str(item.get('username', '')).strip().casefold() == target:
            return item
    return None


def ensure_default_admin_user(store_path: str | Path) -> bool:
    users = load_users(store_path)
    if find_user(users, DEFAULT_ADMIN_USERNAME) is not None:
        return False
    users.append({'username': DEFAULT_ADMIN_USERNAME, 'password_hash': hash_password(DEFAULT_ADMIN_PASSWORD)})
    save_users(store_path, users)
    return True


def register_user(store_path: str | Path, username: str, password: str) -> dict[str, str]:
    clean_name = username.strip()
    users = load_users(store_path)
    if find_user(users, clean_name) is not None:
        raise ValueError('该用户名已存在')
    password_errors = validate_password_policy(password, clean_name)
    if password_errors:
        raise ValueError('\n'.join(password_errors))
    record = {'username': clean_name, 'password_hash': hash_password(password)}
    users.append(record)
    save_users(store_path, users)
    return {'username': clean_name}


def verify_user_credentials(store_path: str | Path, username: str, password: str) -> bool:
    user = find_user(load_users(store_path), username)
    if user is None:
        return False
    return verify_password(password, str(user.get('password_hash', '')))


def update_user_password(store_path: str | Path, username: str, current_password: str, new_password: str) -> None:
    users = load_users(store_path)
    user = find_user(users, username)
    if user is None:
        raise ValueError('账号不存在')
    if not verify_password(current_password, str(user.get('password_hash', ''))):
        raise ValueError('当前密码错误')
    password_errors = validate_password_policy(new_password, username)
    if password_errors:
        raise ValueError('\n'.join(password_errors))
    user['password_hash'] = hash_password(new_password)
    save_users(store_path, users)
