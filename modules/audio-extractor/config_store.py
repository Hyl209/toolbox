import json
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path(__file__).with_name('mp4mp3_config.json')


def _normalize_dir(path: str | Path) -> Path:
    p = Path(path).expanduser()
    return p.resolve() if p.exists() else p


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"default_output_dir": ""}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {"default_output_dir": ""}


def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')


def get_default_output_dir() -> Optional[Path]:
    config = load_config()
    value = (config.get('default_output_dir') or '').strip()
    if not value:
        return None
    return _normalize_dir(value)


def set_default_output_dir(path: str | Path) -> Path:
    out_dir = _normalize_dir(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    config = load_config()
    config['default_output_dir'] = str(out_dir)
    save_config(config)
    return out_dir


def clear_default_output_dir() -> None:
    save_config({"default_output_dir": ""})
