from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "modules" / "theme-customizer" / "color_scheme.py"
spec = importlib.util.spec_from_file_location("theme_customizer_color_scheme_test", MODULE_PATH)
color_scheme = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(color_scheme)


class FakeSettings:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values

    def value(self, key: str, default: str = "") -> object:
        return self.values.get(key, default)


def test_load_custom_colors_ignores_non_string_settings_values() -> None:
    settings = FakeSettings({"theme/dark/accent": ["#123456", "#abcdef"]})

    colors = color_scheme.load_custom_colors(settings, "dark")

    assert colors["accent"] == color_scheme.get_default_colors("dark")["accent"]
