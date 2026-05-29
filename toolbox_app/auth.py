from __future__ import annotations

from pathlib import Path

# Re-export from sub-modules so existing `from toolbox_app.auth import ...` still works.
from toolbox_app.password_policy import (  # noqa: F401
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    validate_password_policy,
)
from toolbox_app.auth_store import (  # noqa: F401
    find_user,
    hash_password,
    load_users,
    register_user,
    save_users,
    update_user_password,
    verify_password,
    verify_user_credentials,
    ensure_default_admin_user,
)
from toolbox_app.auth_preferences import (  # noqa: F401
    decode_saved_password,
    encode_saved_password,
    load_auth_preferences,
    normalize_auth_preferences,
    save_auth_preferences,
    should_auto_login,
)


# ---------------------------------------------------------------------------
# Auth form helpers (kept here — thin UI/form layer)
# ---------------------------------------------------------------------------


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
        'menu_height': 200,
        'menu_padding': 20,
        'menu_spacing': 14,
    }
