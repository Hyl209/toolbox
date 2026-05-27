from __future__ import annotations

import hashlib

from toolbox_app.auth_store import find_user, verify_password
from toolbox_app.utils import load_setting, save_setting


def normalize_auth_preferences(remember_password: bool, auto_login: bool) -> dict[str, bool]:
    normalized_remember = bool(remember_password or auto_login)
    normalized_auto = bool(auto_login and normalized_remember)
    return {
        'remember_password': normalized_remember,
        'auto_login': normalized_auto,
    }


def encode_saved_password(username: str, password: str) -> str:
    if not username or not password:
        return ''
    key = hashlib.sha256(f'hyl-auth:{username.strip().casefold()}'.encode('utf-8')).digest()
    payload = password.encode('utf-8')
    encoded = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
    return encoded.hex()


def decode_saved_password(username: str, encoded_secret: str) -> str:
    if not username or not encoded_secret:
        return ''
    try:
        payload = bytes.fromhex(encoded_secret)
    except ValueError:
        return ''
    key = hashlib.sha256(f'hyl-auth:{username.strip().casefold()}'.encode('utf-8')).digest()
    decoded = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
    try:
        return decoded.decode('utf-8')
    except UnicodeDecodeError:
        return ''


def save_auth_preferences(settings, username: str, remember_password: bool, auto_login: bool, saved_secret: str = '') -> None:
    normalized = normalize_auth_preferences(remember_password, auto_login)
    save_setting(settings, 'auth/last_user', username.strip())
    save_setting(settings, 'auth/remember_password', '1' if normalized['remember_password'] else '0')
    save_setting(settings, 'auth/auto_login', '1' if normalized['auto_login'] else '0')
    save_setting(settings, 'auth/saved_secret', saved_secret if normalized['remember_password'] else '')


def load_auth_preferences(settings) -> dict[str, object]:
    normalized = normalize_auth_preferences(
        load_setting(settings, 'auth/remember_password', '0') == '1',
        load_setting(settings, 'auth/auto_login', '0') == '1',
    )
    last_username = load_setting(settings, 'auth/last_user', '').strip()
    if not last_username:
        last_username = load_setting(settings, 'auth/last_username', '').strip()
    return {
        'last_username': last_username,
        'remember_password': normalized['remember_password'],
        'auto_login': normalized['auto_login'],
        'saved_secret': load_setting(settings, 'auth/saved_secret', '') if normalized['remember_password'] else '',
    }


def should_auto_login(users: list[dict], prefs: dict[str, object]) -> dict[str, str] | None:
    username = str(prefs.get('last_username', '')).strip()
    if not prefs.get('remember_password') or not prefs.get('auto_login') or not username:
        return None
    password = decode_saved_password(username, str(prefs.get('saved_secret', '')))
    if not password:
        return None
    user = find_user(users, username)
    if user is None:
        return None
    if not verify_password(password, str(user.get('password_hash', ''))):
        return None
    return {
        'username': username,
        'password': password,
    }
