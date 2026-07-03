from __future__ import annotations

import base64
import importlib.util
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "modules" / "ai-image-gen" / "converter.py"

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAgMBgJ0XW8sAAAAASUVORK5CYII="
)
PNG_1X1_BYTES = base64.b64decode(PNG_1X1_BASE64)


def load_converter_module():
    spec = importlib.util.spec_from_file_location("aiimage_converter_test", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemorySecretStore:
    def __init__(self, fail_on_set: bool = False):
        self.fail_on_set = fail_on_set
        self.values: dict[str, str] = {}

    def get_secret(self, service_name: str, username: str) -> str | None:
        return self.values.get(f"{service_name}/{username}")

    def set_secret(self, service_name: str, username: str, password: str) -> None:
        if self.fail_on_set:
            raise RuntimeError("keyring unavailable")
        self.values[f"{service_name}/{username}"] = password

    def delete_secret(self, service_name: str, username: str) -> None:
        self.values.pop(f"{service_name}/{username}", None)


@dataclass
class FakeResponse:
    payload: dict
    content: bytes = b""
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, *, post_response: FakeResponse, get_response: FakeResponse | None = None):
        self.post_response = post_response
        self.get_response = get_response
        self.post_calls: list[dict] = []
        self.get_calls: list[dict] = []

    def post(self, url: str, **kwargs):
        self.post_calls.append({"url": url, **kwargs})
        return self.post_response

    def get(self, url: str, **kwargs):
        self.get_calls.append({"url": url, **kwargs})
        assert self.get_response is not None
        return self.get_response


def test_aiimage_load_config_uses_defaults_and_hides_secrets(tmp_path: Path) -> None:
    module = load_converter_module()

    config = module.load_config(settings_path=tmp_path / "hyl_toolbox.ini", secret_store=MemorySecretStore())

    assert config["selected_profile_id"] == ""
    assert config["default_size"] == "1024x1024"
    assert config["default_count"] == 1
    assert config["profiles"] == []
    assert "AI Images" in config["output_dir"]


def test_aiimage_save_config_persists_profiles_and_writes_secret_store(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"

    saved = module.save_config(
        {
            "selected_profile_id": "main",
            "output_dir": str(tmp_path / "images"),
            "default_size": "1536x1024",
            "default_count": 2,
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-1",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )

    assert saved["selected_profile_id"] == "main"
    assert saved["default_size"] == "1536x1024"
    assert saved["default_count"] == 2
    assert saved["profiles"][0]["secret_ref"] == "hyl-toolbox/aiimage/main"
    assert "api_key" not in saved["profiles"][0]
    assert store.values["hyl-toolbox/aiimage/main/main"] == "sk-test"

    loaded = module.load_config(settings_path=settings_path, secret_store=store)
    assert loaded == saved


def test_aiimage_save_config_keeps_ini_unchanged_when_secret_write_fails(tmp_path: Path) -> None:
    module = load_converter_module()
    settings_path = tmp_path / "hyl_toolbox.ini"
    settings_path.write_text("[aiimage]\nselected_profile_id=kept\n", encoding="utf-8")
    before = settings_path.read_text(encoding="utf-8")

    with pytest.raises(module.AiImageError, match="keyring unavailable"):
        module.save_config(
            {
                "selected_profile_id": "main",
                "profiles": [
                    {
                        "id": "main",
                        "name": "Main",
                        "base_url": "https://example.test/v1",
                        "model": "gpt-image-1",
                        "api_key": "sk-test",
                    }
                ],
            },
            settings_path=settings_path,
            secret_store=MemorySecretStore(fail_on_set=True),
        )

    assert settings_path.read_text(encoding="utf-8") == before


def test_aiimage_generate_images_saves_b64_results_and_includes_negative_prompt(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    output_dir = tmp_path / "output"
    module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-1",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(
        post_response=FakeResponse(
            {
                "created": 1,
                "data": [{"b64_json": PNG_1X1_BASE64}],
            }
        )
    )

    result = module.generate_images(
        {
            "profile_id": "main",
            "prompt": "cat astronaut",
            "negative_prompt": "blurry",
            "size": "1024x1024",
            "n": 1,
            "output_dir": str(output_dir),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    assert len(result["images"]) == 1
    assert Path(result["images"][0]["path"]).exists()
    assert result["images"][0]["mime"] == "image/png"
    assert result["images"][0]["width"] == 1
    assert result["images"][0]["height"] == 1
    assert session.post_calls[0]["url"] == "https://example.test/v1/images/generations"
    assert session.post_calls[0]["json"]["negative_prompt"] == "blurry"
    assert session.post_calls[0]["json"]["response_format"] == "b64_json"


def test_aiimage_generate_images_downloads_url_fallback(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    output_dir = tmp_path / "output"
    module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-1",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(
        post_response=FakeResponse({"data": [{"url": "https://cdn.example.test/a.png"}]}),
        get_response=FakeResponse({}, content=PNG_1X1_BYTES),
    )

    result = module.generate_images(
        {
            "profile_id": "main",
            "prompt": "cat astronaut",
            "size": "1024x1024",
            "n": 1,
            "output_dir": str(output_dir),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    assert len(result["images"]) == 1
    assert Path(result["images"][0]["path"]).exists()
    assert session.get_calls[0]["url"] == "https://cdn.example.test/a.png"


def test_aiimage_generate_images_requires_profile_secret_and_base_url(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    module.save_config(
        {
            "selected_profile_id": "broken",
            "profiles": [
                {
                    "id": "broken",
                    "name": "Broken",
                    "base_url": "",
                    "model": "gpt-image-1",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )

    with pytest.raises(module.AiImageError, match="base url"):
        module.generate_images(
            {
                "profile_id": "broken",
                "prompt": "cat astronaut",
                "size": "1024x1024",
                "n": 1,
                "output_dir": str(tmp_path / "output"),
            },
            settings_path=settings_path,
            secret_store=store,
            session=FakeSession(post_response=FakeResponse({"data": []})),
        )
