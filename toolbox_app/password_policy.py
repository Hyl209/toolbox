from __future__ import annotations


DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'Hyl@Init1'  # 首次登录后应强制修改


def validate_password_policy(password: str, username: str = '') -> list[str]:
    errors: list[str] = []
    if len(password) < 6:
        errors.append('密码长度至少 6 位')
    elif len(password) > 64:
        errors.append('密码长度不能超过 64 位')
    if not any(ch.isalpha() for ch in password):
        errors.append('密码必须包含至少一个字母')
    if not any(ch.isdigit() for ch in password):
        errors.append('密码必须包含至少一个数字')
    if username:
        lower_pw = password.lower()
        lower_un = username.strip().lower()
        if len(lower_un) >= 3 and (lower_un in lower_pw or lower_un[::-1] in lower_pw):
            errors.append('密码不能包含用户名')
    return errors
