"""Color scheme customization — zone definitions, QSS generation, persistence."""

from __future__ import annotations

COLOR_ZONES = [
    ('window_bg', '窗口背景', '主窗口和表面背景'),
    ('surface_bg', '面板背景', '侧栏、内容区面板'),
    ('card_bg', '卡片背景', '卡片和放置区背景'),
    ('accent', '强调色', '按钮、选中项、进度条、焦点边框'),
    ('text_primary', '主文字', '标题和正文文字'),
    ('text_secondary', '次文字', '副标题和辅助文字'),
    ('input_bg', '输入框背景', '输入框、下拉框背景'),
]

_DARK_ZONE_COLORS = {
    'window_bg': ['#1b1f25'],
    'surface_bg': ['#1f2329'],
    'card_bg': ['rgba(44, 50, 59, 0.88)', 'rgba(44,50,59,0.88)'],
    'accent': ['#6f95c7', '#7ea6d9', '#6d94c8', '#6488b7', '#7b9fd0',
               '#7ea4d3', 'rgba(118, 160, 214, 0.28)', 'rgba(118,160,214,0.28)',
               'rgba(111, 149, 199, 0.30)', 'rgba(111,149,199,0.30)',
               'rgba(111, 149, 199, 0.32)', 'rgba(111,149,199,0.32)',
               'rgba(111, 149, 199, 0.40)', 'rgba(111,149,199,0.40)'],
    'text_primary': ['#eef2f7', '#eef4fb', '#f3f6fb', '#f4f7fb', '#f5f7fa',
                     '#d5dce6'],
    'text_secondary': ['#9aa6b5', '#a4b0bf', '#9eabb9', '#aeb8c6', '#aab4c2'],
    'input_bg': ['#2a3038', '#303741'],
}

_LIGHT_ZONE_COLORS = {
    'window_bg': ['#e5e9ef'],
    'surface_bg': ['#eef1f5'],
    'card_bg': ['rgba(255, 255, 255, 0.76)', 'rgba(255,255,255,0.76)'],
    'accent': ['#e4efff', '#edf4ff', '#d7e7fb', '#cfd9e8', '#dfeafc',
               '#d4e4ff', '#8fb4e8', '#5b8dd9',
               'rgba(223, 234, 252, 0.85)', 'rgba(223,234,252,0.85)',
               'rgba(216, 226, 246, 0.65)', 'rgba(216,226,246,0.65)',
               'rgba(196, 212, 240, 0.70)', 'rgba(196,212,240,0.70)',
               'rgba(226, 234, 246, 0.72)', 'rgba(226,234,246,0.72)'],
    'text_primary': ['#1f252d', '#2b3541', '#2d3748', '#20262d', '#243447',
                     '#24415f'],
    'text_secondary': ['#697586', '#748091', '#7d8a9a', '#586474', '#637083',
                       '#7f8a99', '#7a8796', '#94a0af'],
    'input_bg': ['#eef1f5', '#f5f7fa', '#e8edf4'],
}

_DEFAULT_COLORS = {
    'dark': {
        'window_bg': '#1b1f25', 'surface_bg': '#1f2329',
        'card_bg': 'rgba(44, 50, 59, 0.88)',
        'accent': '#6f95c7', 'text_primary': '#eef2f7',
        'text_secondary': '#9aa6b5', 'input_bg': '#2a3038',
    },
    'light': {
        'window_bg': '#e5e9ef', 'surface_bg': '#eef1f5',
        'card_bg': 'rgba(255, 255, 255, 0.76)',
        'accent': '#e4efff', 'text_primary': '#1f252d',
        'text_secondary': '#697586', 'input_bg': '#eef1f5',
    },
}


def get_default_colors(theme: str) -> dict[str, str]:
    return dict(_DEFAULT_COLORS.get(theme, _DEFAULT_COLORS['dark']))


def _clean_color_value(value) -> str:
    return value.strip() if isinstance(value, str) else ''


def load_custom_colors(settings, theme: str) -> dict[str, str]:
    defaults = get_default_colors(theme)
    result = {}
    for zone_id, _, _ in COLOR_ZONES:
        raw = settings.value(f'theme/{theme}/{zone_id}', '') if hasattr(settings, 'value') else ''
        value = _clean_color_value(raw)
        result[zone_id] = value if value else defaults.get(zone_id, '')
    return result


def save_custom_colors(settings, theme: str, colors: dict[str, str]) -> None:
    defaults = get_default_colors(theme)
    for zone_id in colors:
        val = colors[zone_id]
        default_val = defaults.get(zone_id, '')
        key = f'theme/{theme}/{zone_id}'
        if val and val != default_val:
            settings.setValue(key, val)
        else:
            settings.setValue(key, '')
    if hasattr(settings, 'sync'):
        settings.sync()


def _parse_hex(color: str) -> tuple[int, int, int]:
    color = color.strip().lstrip('#')
    if len(color) == 3:
        color = ''.join(c * 2 for c in color)
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _to_hex(r: int, g: int, b: int) -> str:
    return f'#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}'


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def _lighten(hex_color: str, percent: float) -> str:
    r, g, b = _parse_hex(hex_color)
    return _to_hex(
        int(r + (255 - r) * percent),
        int(g + (255 - g) * percent),
        int(b + (255 - b) * percent),
    )


def _darken(hex_color: str, percent: float) -> str:
    r, g, b = _parse_hex(hex_color)
    return _to_hex(
        int(r * (1 - percent)),
        int(g * (1 - percent)),
        int(b * (1 - percent)),
    )


def _alpha_hex(hex_color: str, alpha: float) -> str:
    r, g, b = _parse_hex(hex_color)
    return f'rgba({r}, {g}, {b}, {alpha:.2f})'


def generate_qss(base_qss: str, overrides: dict[str, str], theme: str) -> str:
    if not overrides:
        return base_qss

    zone_colors_map = _DARK_ZONE_COLORS if theme == 'dark' else _LIGHT_ZONE_COLORS
    qss = base_qss

    for zone_id, originals in zone_colors_map.items():
        new_color = overrides.get(zone_id, '')
        if not new_color:
            continue

        if zone_id == 'accent':
            hover = _lighten(new_color, 0.08)
            pressed = _darken(new_color, 0.08)
            border = _lighten(new_color, 0.12)
            focus_border = _alpha_hex(new_color, 0.70) if not new_color.startswith('rgba') else new_color
            for orig in originals:
                if orig in ('#7b9fd0', '#edf4ff'):
                    qss = qss.replace(orig, hover)
                elif orig in ('#6488b7', '#d7e7fb'):
                    qss = qss.replace(orig, pressed)
                elif orig in ('#7ea4d3', '#cfd9e8'):
                    qss = qss.replace(orig, border)
                elif orig in ('#7ea6d9', '#8fb4e8'):
                    qss = qss.replace(orig, focus_border)
                else:
                    qss = qss.replace(orig, new_color)
        else:
            for orig in originals:
                qss = qss.replace(orig, new_color)

    return qss
