from __future__ import annotations

import base64
import configparser
import json
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol

import requests
from PIL import Image


SECTION = "aiimage"
SECRET_SERVICE_PREFIX = "hyl-toolbox/aiimage"
DEFAULT_SIZE = "1024x1024"
DEFAULT_COUNT = 1
DEFAULT_MODEL = "gpt-image-1"


class AiImageError(RuntimeError):
    pass


class SecretStore(Protocol):
    def get_secret(self, service_name: str, username: str) -> str | None: ...

    def set_secret(self, service_name: str, username: str, password: str) -> None: ...

    def delete_secret(self, service_name: str, username: str) -> None: ...


class KeyringSecretStore:
    def _backend(self):
        try:
            import keyring
        except ImportError as exc:  # pragma: no cover
            raise AiImageError("keyring is not installed") from exc
        return keyring

    def get_secret(self, service_name: str, username: str) -> str | None:
        return self._backend().get_password(service_name, username)

    def set_secret(self, service_name: str, username: str, password: str) -> None:
        self._backend().set_password(service_name, username, password)

    def delete_secret(self, service_name: str, username: str) -> None:
        self._backend().delete_password(service_name, username)


def default_output_dir() -> str:
    return str(Path.home() / "Pictures" / "Hyl Toolbox" / "AI Images")


def secret_ref_for_profile(profile_id: str) -> str:
    return f"{SECRET_SERVICE_PREFIX}/{profile_id}"


def _read_settings(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    if path.exists():
        parser.read(path, encoding="utf-8")
    return parser


def _write_settings(parser: configparser.ConfigParser, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            parser.write(handle, space_around_delimiters=False)
        temp_path.replace(path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _ensure_section(parser: configparser.ConfigParser, section: str) -> None:
    if not parser.has_section(section):
        parser.add_section(section)


def _value(parser: configparser.ConfigParser, option: str, default: str = "") -> str:
    if parser.has_section(SECTION) and parser.has_option(SECTION, option):
        return parser.get(SECTION, option).strip()
    return default


def _now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now()).replace(microsecond=0).isoformat()


def _normalize_profile(raw: dict[str, Any], existing: dict[str, dict[str, Any]], now_iso: str) -> dict[str, Any]:
    profile_id = str(raw.get("id", "")).strip()
    if not profile_id:
        raise AiImageError("profile id is required")
    previous = existing.get(profile_id, {})
    base_url = str(raw.get("base_url", previous.get("base_url", ""))).strip().rstrip("/")
    model = str(raw.get("model", previous.get("model", DEFAULT_MODEL))).strip() or DEFAULT_MODEL
    name = str(raw.get("name", previous.get("name", profile_id))).strip() or profile_id
    return {
        "id": profile_id,
        "name": name,
        "base_url": base_url,
        "model": model,
        "secret_ref": str(raw.get("secret_ref", previous.get("secret_ref", secret_ref_for_profile(profile_id)))).strip()
        or secret_ref_for_profile(profile_id),
        "created_at": str(previous.get("created_at", raw.get("created_at", now_iso))).strip() or now_iso,
        "updated_at": now_iso,
    }


def _parse_profiles(parser: configparser.ConfigParser) -> list[dict[str, Any]]:
    raw = _value(parser, "profiles_json", "[]")
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AiImageError("profiles_json is invalid") from exc
    if not isinstance(loaded, list):
        raise AiImageError("profiles_json must be a list")
    existing = {str(item.get("id", "")).strip(): item for item in loaded if isinstance(item, dict)}
    now_iso = _now_iso()
    profiles: list[dict[str, Any]] = []
    for item in loaded:
        if isinstance(item, dict):
            profiles.append(_normalize_profile(item, existing, now_iso))
    return profiles


def _config_from_profiles(
    profiles: list[dict[str, Any]],
    parser: configparser.ConfigParser,
    *,
    selected_profile_id: str | None = None,
    output_dir: str | None = None,
    default_size: str | None = None,
    default_count: int | None = None,
) -> dict[str, Any]:
    count_text = str(default_count if default_count is not None else _value(parser, "default_count", str(DEFAULT_COUNT)))
    return {
        "selected_profile_id": (selected_profile_id if selected_profile_id is not None else _value(parser, "selected_profile_id", "")).strip(),
        "output_dir": (output_dir if output_dir is not None else _value(parser, "output_dir", default_output_dir())).strip() or default_output_dir(),
        "default_size": (default_size if default_size is not None else _value(parser, "default_size", DEFAULT_SIZE)).strip() or DEFAULT_SIZE,
        "default_count": int(count_text or DEFAULT_COUNT),
        "profiles": profiles,
    }


def load_config(*, settings_path: str | Path, secret_store: SecretStore | None = None) -> dict[str, Any]:
    del secret_store
    parser = _read_settings(Path(settings_path))
    profiles = _parse_profiles(parser)
    config = _config_from_profiles(profiles, parser)
    if config["selected_profile_id"] and not any(profile["id"] == config["selected_profile_id"] for profile in profiles):
        config["selected_profile_id"] = ""
    return config


def save_config(
    payload: dict[str, Any],
    *,
    settings_path: str | Path,
    secret_store: SecretStore | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    store = secret_store or KeyringSecretStore()
    path = Path(settings_path)
    parser = _read_settings(path)
    existing_profiles = _parse_profiles(parser)
    existing_by_id = {profile["id"]: profile for profile in existing_profiles}
    raw_profiles = payload.get("profiles", [])
    if not isinstance(raw_profiles, list):
        raise AiImageError("profiles must be a list")

    now_iso = _now_iso(now)
    profiles = [_normalize_profile(item, existing_by_id, now_iso) for item in raw_profiles if isinstance(item, dict)]

    selected_profile_id = str(payload.get("selected_profile_id", "")).strip()
    if selected_profile_id and not any(profile["id"] == selected_profile_id for profile in profiles):
        raise AiImageError("selected profile id is not in profiles")

    output_dir = str(payload.get("output_dir", default_output_dir())).strip() or default_output_dir()
    default_size = str(payload.get("default_size", DEFAULT_SIZE)).strip() or DEFAULT_SIZE
    try:
        default_count = int(payload.get("default_count", DEFAULT_COUNT))
    except (TypeError, ValueError) as exc:
        raise AiImageError("default count must be an integer") from exc
    if default_count < 1:
        raise AiImageError("default count must be at least 1")

    for item in raw_profiles:
        if not isinstance(item, dict):
            continue
        profile_id = str(item.get("id", "")).strip()
        api_key = item.get("api_key")
        if isinstance(api_key, str) and api_key.strip():
            try:
                store.set_secret(secret_ref_for_profile(profile_id), profile_id, api_key.strip())
            except Exception as exc:
                raise AiImageError(str(exc)) from exc

    _ensure_section(parser, SECTION)
    parser.set(SECTION, "selected_profile_id", selected_profile_id)
    parser.set(SECTION, "output_dir", output_dir)
    parser.set(SECTION, "default_size", default_size)
    parser.set(SECTION, "default_count", str(default_count))
    parser.set(SECTION, "profiles_json", json.dumps(profiles, ensure_ascii=False))
    _write_settings(parser, path)

    removed_ids = {profile["id"] for profile in existing_profiles} - {profile["id"] for profile in profiles}
    for profile_id in removed_ids:
        secret_ref = existing_by_id.get(profile_id, {}).get("secret_ref", secret_ref_for_profile(profile_id))
        try:
            store.delete_secret(str(secret_ref), profile_id)
        except Exception:
            continue

    return _config_from_profiles(
        profiles,
        parser,
        selected_profile_id=selected_profile_id,
        output_dir=output_dir,
        default_size=default_size,
        default_count=default_count,
    )


def _profile_for_generation(config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    requested_id = str(payload.get("profile_id", "")).strip() or str(config.get("selected_profile_id", "")).strip()
    if not requested_id:
        raise AiImageError("profile id is required")
    for profile in config["profiles"]:
        if profile["id"] == requested_id:
            return profile
    raise AiImageError("profile not found")


def _image_details(content: bytes) -> tuple[str, str, int, int]:
    try:
        with Image.open(BytesIO(content)) as image:
            fmt = (image.format or "PNG").upper()
            width, height = image.size
    except Exception as exc:
        raise AiImageError("invalid image data returned by provider") from exc
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    mime = "image/jpeg" if fmt == "JPEG" else f"image/{ext}"
    return ext, mime, width, height


def _build_run_dir(output_dir: str) -> Path:
    base = Path(output_dir).expanduser()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = base / timestamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = base / f"{timestamp}-{suffix}"
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def _save_image_bytes(run_dir: Path, index: int, content: bytes) -> dict[str, Any]:
    ext, mime, width, height = _image_details(content)
    filename = f"image_{index:02d}.{ext}"
    path = run_dir / filename
    path.write_bytes(content)
    return {
        "path": str(path.resolve()),
        "filename": filename,
        "mime": mime,
        "width": width,
        "height": height,
    }


def _decode_b64_image(item: dict[str, Any]) -> bytes | None:
    value = item.get("b64_json")
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return base64.b64decode(value)
    except Exception as exc:
        raise AiImageError("invalid b64_json returned by provider") from exc


def _download_image(item: dict[str, Any], session: Any) -> bytes | None:
    url = item.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    response = session.get(url, timeout=120)
    response.raise_for_status()
    return bytes(response.content)


def generate_images(
    payload: dict[str, Any],
    *,
    settings_path: str | Path,
    secret_store: SecretStore | None = None,
    session: Any | None = None,
) -> dict[str, Any]:
    store = secret_store or KeyringSecretStore()
    config = load_config(settings_path=settings_path, secret_store=store)
    profile = _profile_for_generation(config, payload)
    base_url = str(profile.get("base_url", "")).strip().rstrip("/")
    if not base_url:
        raise AiImageError("profile base url is required")
    secret_ref = str(profile.get("secret_ref", "")).strip() or secret_ref_for_profile(profile["id"])
    api_key = store.get_secret(secret_ref, profile["id"])
    if not api_key:
        raise AiImageError("profile api key is missing")

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise AiImageError("prompt is required")
    size = str(payload.get("size", config.get("default_size", DEFAULT_SIZE))).strip() or DEFAULT_SIZE
    try:
        count = int(payload.get("n", config.get("default_count", DEFAULT_COUNT)))
    except (TypeError, ValueError) as exc:
        raise AiImageError("image count must be an integer") from exc
    if count < 1:
        raise AiImageError("image count must be at least 1")
    output_dir = str(payload.get("output_dir", config.get("output_dir", default_output_dir()))).strip() or default_output_dir()

    request_payload: dict[str, Any] = {
        "model": str(profile.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
        "prompt": prompt,
        "size": size,
        "n": count,
        "response_format": "b64_json",
    }
    negative_prompt = str(payload.get("negative_prompt", "")).strip()
    if negative_prompt:
        request_payload["negative_prompt"] = negative_prompt

    client = session or requests.Session()
    response = client.post(
        f"{base_url}/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=request_payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise AiImageError("provider returned no images")

    run_dir = _build_run_dir(output_dir)
    images: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise AiImageError("provider returned an invalid image item")
        content = _decode_b64_image(item) or _download_image(item, client)
        if content is None:
            raise AiImageError("provider returned neither b64_json nor url")
        images.append(_save_image_bytes(run_dir, index, content))

    return {
        "output_dir": str(run_dir.resolve()),
        "images": images,
        "count": len(images),
        "profile_id": profile["id"],
        "model": request_payload["model"],
    }
