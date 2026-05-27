from __future__ import annotations


ALLOWED_PASSWORD_SYMBOLS = '!@#$%^&*()_+-='
FORBIDDEN_PASSWORD_FRAGMENTS = ('2024', '2025', '2026', 'admin', 'root', 'password')
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = '123'  # WARNING: 首次登录后应强制修改


def validate_password_policy(password: str, username: str = '') -> list[str]:
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
