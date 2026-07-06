from __future__ import annotations

import base64
import configparser
import hashlib
import json
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol
from urllib import request as urllib_request

from sidecar.history_store import append_history, clear_history as clear_tool_history, delete_history as delete_tool_history, load_history as load_tool_history


SECTION = "aiimage"
SECRET_SECTION = "aiimage_secrets"
SECRET_SERVICE_PREFIX = "hyl-toolbox/aiimage"
DEFAULT_SIZE = "1024x1024"
DEFAULT_COUNT = 1
DEFAULT_MODEL = "gpt-image-2"
SUPPORTED_SIZES = {"auto", "1024x1024", "1536x1024", "1024x1536", "1280x720", "720x1280", "1024x768", "768x1024", "1920x816", "2048x2048", "2160x1440", "1440x2160", "2560x1440", "1440x2560", "2048x1536", "1536x2048", "3120x1344", "2880x2880", "3456x2304", "2304x3456", "3840x2160", "2160x3840", "3200x2400", "2400x3200", "3840x1648"}
MAX_IMAGE_SIDE = 3840
MAX_IMAGE_PIXELS = 3840 * 2160
MAX_IMAGE_ASPECT_RATIO = 3
QUALITY_OPTIONS = {"auto", "low", "medium", "high"}
OUTPUT_FORMAT_OPTIONS = {"png", "jpeg", "webp"}
OUTPUT_COMPRESSION_MIN = 0
OUTPUT_COMPRESSION_MAX = 100
BACKGROUND_OPTIONS = {"auto", "transparent", "white", "black"}
MODERATION_OPTIONS = {"auto", "low"}
HISTORY_TOOL_ID = "aiimage"


class AiImageError(RuntimeError):
    pass


class _UrllibResponse:
    def __init__(self, content: bytes, status_code: int):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AiImageError(f"http {self.status_code}")

    def json(self) -> dict[str, Any]:
        data = json.loads(self.content.decode("utf-8"))
        if not isinstance(data, dict):
            raise AiImageError("provider returned invalid JSON")
        return data


class _UrllibSession:
    def __init__(self):
        self._opener = urllib_request.build_opener(urllib_request.ProxyHandler({}))

    def post(self, url: str, **kwargs):
        body = json.dumps(kwargs.get("json", {}), ensure_ascii=False).encode("utf-8")
        headers = dict(kwargs.get("headers", {}))
        request = urllib_request.Request(url, data=body, headers=headers, method="POST")
        with self._opener.open(request, timeout=kwargs.get("timeout", 120)) as response:
            return _UrllibResponse(response.read(), int(response.status))

    def get(self, url: str, **kwargs):
        request = urllib_request.Request(url, method="GET")
        with self._opener.open(request, timeout=kwargs.get("timeout", 120)) as response:
            return _UrllibResponse(response.read(), int(response.status))


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


class FileSecretStore:
    def __init__(self, settings_path: str | Path):
        self.settings_path = Path(settings_path)

    def _option(self, service_name: str, username: str) -> str:
        raw = f"{service_name}\n{username}".encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    def _key(self, service_name: str, username: str) -> bytes:
        return hashlib.sha256(f"{SECRET_SERVICE_PREFIX}:file:{service_name}:{username}".encode("utf-8")).digest()

    def _encode(self, service_name: str, username: str, password: str) -> str:
        key = self._key(service_name, username)
        payload = password.encode("utf-8")
        data = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
        return base64.urlsafe_b64encode(data).decode("ascii")

    def _decode(self, service_name: str, username: str, value: str) -> str | None:
        try:
            payload = base64.urlsafe_b64decode(value.encode("ascii"))
        except Exception:
            return None
        key = self._key(service_name, username)
        data = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def get_secret(self, service_name: str, username: str) -> str | None:
        parser = _read_settings(self.settings_path)
        value = _value(parser, self._option(service_name, username), "", SECRET_SECTION)
        return self._decode(service_name, username, value) if value else None

    def set_secret(self, service_name: str, username: str, password: str) -> None:
        parser = _read_settings(self.settings_path)
        _ensure_section(parser, SECRET_SECTION)
        parser.set(SECRET_SECTION, self._option(service_name, username), self._encode(service_name, username, password))
        _write_settings(parser, self.settings_path)

    def delete_secret(self, service_name: str, username: str) -> None:
        parser = _read_settings(self.settings_path)
        option = self._option(service_name, username)
        if parser.has_section(SECRET_SECTION) and parser.has_option(SECRET_SECTION, option):
            parser.remove_option(SECRET_SECTION, option)
            _write_settings(parser, self.settings_path)


class FallbackSecretStore:
    def __init__(self, primary: SecretStore, fallback: SecretStore):
        self.primary = primary
        self.fallback = fallback

    def get_secret(self, service_name: str, username: str) -> str | None:
        try:
            value = self.primary.get_secret(service_name, username)
        except Exception:
            value = None
        return value or self.fallback.get_secret(service_name, username)

    def set_secret(self, service_name: str, username: str, password: str) -> None:
        try:
            self.primary.set_secret(service_name, username, password)
        except Exception:
            self.fallback.set_secret(service_name, username, password)

    def delete_secret(self, service_name: str, username: str) -> None:
        try:
            self.primary.delete_secret(service_name, username)
        except Exception:
            pass
        self.fallback.delete_secret(service_name, username)


def default_secret_store(settings_path: str | Path) -> SecretStore:
    return FallbackSecretStore(KeyringSecretStore(), FileSecretStore(settings_path))


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


def _value(parser: configparser.ConfigParser, option: str, default: str = "", section: str = SECTION) -> str:
    if parser.has_section(section) and parser.has_option(section, option):
        return parser.get(section, option).strip()
    return default


def _now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now()).replace(microsecond=0).isoformat()


def _normalize_profile(
    raw: dict[str, Any],
    existing: dict[str, dict[str, Any]],
    now_iso: str,
    *,
    touch_updated_at: bool = True,
) -> dict[str, Any]:
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
        "updated_at": now_iso if touch_updated_at else str(previous.get("updated_at", raw.get("updated_at", now_iso))).strip() or now_iso,
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
            profiles.append(_normalize_profile(item, existing, now_iso, touch_updated_at=False))
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


def load_history(*, settings_path: str | Path) -> list[dict[str, Any]]:
    return load_tool_history(HISTORY_TOOL_ID, settings_path=settings_path)


def delete_history(item_id: str, *, settings_path: str | Path) -> list[dict[str, Any]]:
    delete_tool_history(HISTORY_TOOL_ID, item_id, settings_path=settings_path)
    return load_history(settings_path=settings_path)


def clear_history(*, settings_path: str | Path) -> list[dict[str, Any]]:
    clear_tool_history(HISTORY_TOOL_ID, settings_path=settings_path)
    return []


def save_config(
    payload: dict[str, Any],
    *,
    settings_path: str | Path,
    secret_store: SecretStore | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    path = Path(settings_path)
    store = secret_store or default_secret_store(path)
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

    parser = _read_settings(path)
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
        from PIL import Image

        with Image.open(BytesIO(content)) as image:
            fmt = (image.format or "PNG").upper()
            width, height = image.size
    except ImportError as exc:
        raise AiImageError("Pillow is not installed") from exc
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


def _is_valid_size(size: str) -> bool:
    normalized = size.lower()
    if normalized in SUPPORTED_SIZES:
        return True
    match = normalized.split("x")
    if len(match) != 2:
        return False
    try:
        width = int(match[0])
        height = int(match[1])
    except ValueError:
        return False
    if width < 16 or height < 16:
        return False
    if width % 16 or height % 16:
        return False
    if max(width, height) > MAX_IMAGE_SIDE:
        return False
    if width * height > MAX_IMAGE_PIXELS:
        return False
    if max(width / height, height / width) > MAX_IMAGE_ASPECT_RATIO:
        return False
    return True


def generate_images(
    payload: dict[str, Any],
    *,
    settings_path: str | Path,
    secret_store: SecretStore | None = None,
    session: Any | None = None,
) -> dict[str, Any]:
    store = secret_store or default_secret_store(settings_path)
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
    if not _is_valid_size(size):
        raise AiImageError("size is invalid")
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
        "n": count,
        "response_format": "b64_json",
    }
    if size.lower() != "auto":
        request_payload["size"] = size
    negative_prompt = str(payload.get("negative_prompt", "")).strip()
    if negative_prompt:
        request_payload["negative_prompt"] = negative_prompt
    quality = str(payload.get("quality", "")).strip().lower()
    if quality:
        if quality not in QUALITY_OPTIONS:
            raise AiImageError("quality is invalid")
        request_payload["quality"] = quality
    output_format = str(payload.get("output_format", "")).strip().lower()
    if output_format:
        if output_format not in OUTPUT_FORMAT_OPTIONS:
            raise AiImageError("output format is invalid")
        request_payload["output_format"] = output_format
    if output_format in {"jpeg", "webp"} and "output_compression" in payload:
        try:
            output_compression = int(payload.get("output_compression"))
        except (TypeError, ValueError) as exc:
            raise AiImageError("output compression must be an integer from 0 to 100") from exc
        if not OUTPUT_COMPRESSION_MIN <= output_compression <= OUTPUT_COMPRESSION_MAX:
            raise AiImageError("output compression must be from 0 to 100")
        request_payload["output_compression"] = output_compression
    background = str(payload.get("background", "")).strip().lower()
    if background:
        if background not in BACKGROUND_OPTIONS:
            raise AiImageError("background is invalid")
        request_payload["background"] = background
    moderation = str(payload.get("moderation", "")).strip().lower()
    if moderation:
        if moderation not in MODERATION_OPTIONS:
            raise AiImageError("moderation is invalid")
        request_payload["moderation"] = moderation

    if session is None:
        try:
            import requests
        except ImportError:
            client = _UrllibSession()
        else:
            client = requests.Session()
    else:
        client = session
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

    result = {
        "output_dir": str(run_dir.resolve()),
        "images": images,
        "count": len(images),
        "profile_id": profile["id"],
        "model": request_payload["model"],
    }
    history_items = append_history(
        HISTORY_TOOL_ID,
        {
            "title": prompt[:24] + ("..." if len(prompt) > 24 else ""),
            "prompt": prompt,
            "negativePrompt": negative_prompt,
            "size": size,
            "quality": request_payload.get("quality", "auto"),
            "outputFormat": request_payload.get("output_format", "png"),
            "outputCompression": request_payload.get("output_compression", 80),
            "background": request_payload.get("background", "auto"),
            "moderation": request_payload.get("moderation", "auto"),
            "count": count,
            "status": "success",
            "outputDir": result["output_dir"],
            "images": images,
            "profile_id": profile["id"],
            "model": request_payload["model"],
        },
        settings_path=settings_path,
    )
    if history_items:
        result["history_id"] = history_items[0]["id"]
    return result
