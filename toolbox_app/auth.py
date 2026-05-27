from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from toolbox_app.utils import load_setting, save_setting


ALLOWED_PASSWORD_SYMBOLS = '!@#$%^&*()_+-='
FORBIDDEN_PASSWORD_FRAGMENTS = ('2024', '2025', '2026', 'admin', 'root', 'password')
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = '123'


def load_users(store_path: str | Path) -> list[dict[str, str]]:
    path = Path(store_path)
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
    return users


def save_users(store_path: str | Path, users: list[dict[str, str]]) -> None:
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {'username': item['username'], 'password_hash': item['password_hash']}
        for item in users
        if item.get('username') and item.get('password_hash')
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.sha256(f'{salt}:{password}'.encode('utf-8')).hexdigest()
    return f'{salt}${digest}'


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split('$', 1)
    except ValueError:
        return False
    actual = hashlib.sha256(f'{salt}:{password}'.encode('utf-8')).hexdigest()
    return hmac.compare_digest(actual, expected)


def find_user(users: list[dict[str, str]], username: str):
    target = username.strip().casefold()
    for item in users:
        if str(item.get('username', '')).strip().casefold() == target:
            return item
    return None


def validate_password_policy(password: str, username: str = '') -> list[str]:
    clean_name = username.strip().casefold()
    if clean_name == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
        return []
    errors: list[str] = []
    if len(password) != 12:
        errors.append('密码长度必须严格等于 12 位')
    if password and not password[0].isupper():
        errors.append('首字符必须是大写字母')
    if password and not password[-1].isdigit():
        errors.append('尾字符必须是数字')
    upper_count = sum(1 for ch in password if ch.isupper())
    lower_count = sum(1 for ch in password if ch.islower())
    digit_count = sum(1 for ch in password if ch.isdigit())
    symbol_count = sum(1 for ch in password if ch in ALLOWED_PASSWORD_SYMBOLS)
    invalid_symbols = [ch for ch in password if not (ch.isupper() or ch.islower() or ch.isdigit() or ch in ALLOWED_PASSWORD_SYMBOLS)]
    if upper_count < 2 or lower_count < 2 or digit_count < 2 or symbol_count < 2:
        errors.append('密码必须包含大写字母、小写字母、数字、特殊符号各至少 2 个')
    if invalid_symbols:
        errors.append(f'特殊符号只能从 {ALLOWED_PASSWORD_SYMBOLS} 里选')
    for index in range(len(password) - 2):
        chunk = password[index:index + 3]
        if len(set(chunk)) == 1:
            errors.append('密码不能包含连续 3 位相同字符')
            break
    for index in range(len(password) - 2):
        a, b, c = password[index:index + 3]
        if ord(b) == ord(a) + 1 and ord(c) == ord(b) + 1:
            errors.append('密码不能包含连续 3 位顺序字符')
            break
    lowered = password.casefold()
    if any(fragment in lowered for fragment in FORBIDDEN_PASSWORD_FRAGMENTS):
        errors.append('密码不能包含 2024、2025、2026、admin、root、password 任何片段')
    return errors


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


def validate_auth_form(username: str, password: str, confirm_password: str = '', is_register: bool = False) -> list[str]:
    errors: list[str] = []
    clean_name = username.strip()
    if not clean_name:
        errors.append('请输入用户名')
    elif len(clean_name) < 3:
        errors.append('用户名至少需要 3 个字符')
    if not password:
        errors.append('请输入密码')
    elif is_register:
        errors.extend(validate_password_policy(password, clean_name))
    elif clean_name.casefold() == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
        pass
    elif len(password) < 4:
        errors.append('密码长度至少需要 4 个字符')
    if is_register and password != confirm_password:
        errors.append('两次输入的密码不一致')
    return errors


def build_auth_state(store_path: str | Path) -> dict[str, object]:
    users = load_users(store_path)
    has_users = bool(users)
    return {
        'has_users': has_users,
        'mode': 'login' if has_users else 'register',
        'user_count': len(users),
    }


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


def clear_auth_fields(fields: dict[str, str]) -> dict[str, str]:
    return {key: '' for key in fields}


def prepare_auth_mode_fields(previous_mode: str, next_mode: str, current_fields: dict[str, str], login_snapshot: dict[str, str] | None) -> dict[str, dict[str, str] | None]:
    snapshot = dict(login_snapshot or {})
    visible_fields = dict(current_fields)
    if next_mode in {'register', 'change_password'} and previous_mode == 'login':
        snapshot = dict(current_fields)
        visible_fields = clear_auth_fields(current_fields)
    elif next_mode == 'login' and previous_mode in {'register', 'change_password'} and snapshot:
        visible_fields = dict(snapshot)
    return {
        'visible_fields': visible_fields,
        'login_snapshot': snapshot or None,
    }


def build_user_menu_state(username: str) -> dict[str, str]:
    clean_name = username.strip()
    return {
        'username': clean_name or '未登录',
        'avatar_text': (clean_name[:1] or 'U').upper(),
        'logout_text': '退出账号',
        'avatar_button_size': 38,
        'avatar_border_radius': 19,
        'avatar_uses_theme_toggle_style': True,
        'menu_width': 236,
        'menu_height': 148,
        'menu_padding': 20,
        'menu_spacing': 14,
    }


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
