from __future__ import annotations

import base64
import builtins
import importlib.util
import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def block_imports(monkeypatch: pytest.MonkeyPatch, blocked_roots: set[str]) -> None:
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split(".", 1)[0]
        if root in blocked_roots:
            raise ModuleNotFoundError(f"No module named '{root}'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


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
    assert module.DEFAULT_MODEL == "gpt-image-2"
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


def test_aiimage_save_config_does_not_require_generation_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    block_imports(monkeypatch, {"requests", "PIL"})
    module = load_converter_module()

    saved = module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-2",
                }
            ],
        },
        settings_path=tmp_path / "hyl_toolbox.ini",
        secret_store=MemorySecretStore(),
    )

    assert saved["selected_profile_id"] == "main"
    assert saved["profiles"][0]["name"] == "Main"


def test_aiimage_save_config_uses_file_secret_store_when_keyring_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    block_imports(monkeypatch, {"keyring"})
    module = load_converter_module()
    settings_path = tmp_path / "hyl_toolbox.ini"

    saved = module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-2",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
    )

    assert saved["selected_profile_id"] == "main"
    assert "api_key" not in saved["profiles"][0]
    assert module.FileSecretStore(settings_path).get_secret("hyl-toolbox/aiimage/main", "main") == "sk-test"


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
            "quality": "high",
            "output_format": "webp",
            "background": "transparent",
            "moderation": "low",
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
    assert session.post_calls[0]["json"]["quality"] == "high"
    assert session.post_calls[0]["json"]["output_format"] == "webp"
    assert session.post_calls[0]["json"]["background"] == "transparent"
    assert session.post_calls[0]["json"]["moderation"] == "low"


def test_aiimage_generate_images_appends_persistent_history(tmp_path: Path) -> None:
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
                    "model": "gpt-image-2",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    result = module.generate_images(
        {
            "profile_id": "main",
            "prompt": "persistent cat",
            "size": "1024x1024",
            "n": 1,
            "output_dir": str(output_dir),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    history = module.load_history(settings_path=settings_path)
    assert result["history_id"] == history[0]["id"]
    assert history[0]["prompt"] == "persistent cat"
    assert history[0]["status"] == "success"
    assert history[0]["images"] == result["images"]
    assert history[0]["outputDir"] == result["output_dir"]


def test_aiimage_generate_images_uses_stdlib_http_when_requests_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    output_dir = tmp_path / "output"
    requests_seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            requests_seen.append(
                {
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                    "body": json.loads(body.decode("utf-8")),
                }
            )
            payload = json.dumps({"data": [{"b64_json": PNG_1X1_BASE64}]}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        module.save_config(
            {
                "selected_profile_id": "main",
                "profiles": [
                    {
                        "id": "main",
                        "name": "Main",
                        "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                        "model": "gpt-image-2",
                        "api_key": "sk-test",
                    }
                ],
            },
            settings_path=settings_path,
            secret_store=store,
        )
        block_imports(monkeypatch, {"requests"})

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
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert result["count"] == 1
    assert Path(result["images"][0]["path"]).exists()
    assert requests_seen[0]["path"] == "/v1/images/generations"
    assert requests_seen[0]["authorization"] == "Bearer sk-test"
    assert requests_seen[0]["body"]["prompt"] == "cat astronaut"


def test_aiimage_generate_images_forwards_output_compression_for_lossy_formats(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
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
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    module.generate_images(
        {
            "profile_id": "main",
            "prompt": "cat astronaut",
            "size": "1024x1024",
            "n": 1,
            "output_format": "webp",
            "output_compression": 72,
            "output_dir": str(tmp_path / "output"),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    assert session.post_calls[0]["json"]["output_compression"] == 72


def test_aiimage_generate_images_rejects_invalid_output_compression_before_request(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
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
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    with pytest.raises(module.AiImageError, match="output compression"):
        module.generate_images(
            {
                "profile_id": "main",
                "prompt": "cat astronaut",
                "size": "1024x1024",
                "n": 1,
                "output_format": "jpeg",
                "output_compression": 101,
                "output_dir": str(tmp_path / "output"),
            },
            settings_path=settings_path,
            secret_store=store,
            session=session,
        )

    assert session.post_calls == []


def test_aiimage_generate_images_rejects_unsupported_size_before_request(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
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
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    with pytest.raises(module.AiImageError, match="size is invalid"):
        module.generate_images(
            {
                "profile_id": "main",
                "prompt": "cat astronaut",
                "size": "4096x4096",
                "n": 1,
                "output_dir": str(tmp_path / "output"),
            },
            settings_path=settings_path,
            secret_store=store,
            session=session,
        )

    assert session.post_calls == []


def test_aiimage_generate_images_accepts_all_1k_ratio_preset_sizes() -> None:
    module = load_converter_module()
    expected_sizes = {
        "1024x1024",
        "1536x1024",
        "1024x1536",
        "1280x720",
        "720x1280",
        "1024x768",
        "768x1024",
        "1920x816",
    }

    assert expected_sizes <= module.SUPPORTED_SIZES


def test_aiimage_generate_images_accepts_gpt_image_2_high_resolution_sizes() -> None:
    module = load_converter_module()

    expected_sizes = {
        "2048x2048",
        "2560x1440",
        "1440x2560",
        "3840x2160",
        "2160x3840",
    }

    assert expected_sizes <= module.SUPPORTED_SIZES


def test_aiimage_generate_images_sends_4k_size_for_gpt_image_2(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-2",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    module.generate_images(
        {
            "profile_id": "main",
            "prompt": "cat astronaut",
            "size": "3840x2160",
            "n": 1,
            "output_dir": str(tmp_path / "output"),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    assert session.post_calls[0]["json"]["model"] == "gpt-image-2"
    assert session.post_calls[0]["json"]["size"] == "3840x2160"


def test_aiimage_generate_images_accepts_dynamic_gpt_image_2_dimensions(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-2",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    module.generate_images(
        {
            "profile_id": "main",
            "prompt": "cat astronaut",
            "size": "2880x2880",
            "n": 1,
            "output_dir": str(tmp_path / "output"),
        },
        settings_path=settings_path,
        secret_store=store,
        session=session,
    )

    assert session.post_calls[0]["json"]["size"] == "2880x2880"


def test_aiimage_generate_images_rejects_gpt_image_2_dimensions_over_pixel_limit(tmp_path: Path) -> None:
    module = load_converter_module()
    store = MemorySecretStore()
    settings_path = tmp_path / "hyl_toolbox.ini"
    module.save_config(
        {
            "selected_profile_id": "main",
            "profiles": [
                {
                    "id": "main",
                    "name": "Main",
                    "base_url": "https://example.test/v1",
                    "model": "gpt-image-2",
                    "api_key": "sk-test",
                }
            ],
        },
        settings_path=settings_path,
        secret_store=store,
    )
    session = FakeSession(post_response=FakeResponse({"data": [{"b64_json": PNG_1X1_BASE64}]}))

    with pytest.raises(module.AiImageError, match="size is invalid"):
        module.generate_images(
            {
                "profile_id": "main",
                "prompt": "cat astronaut",
                "size": "3840x2560",
                "n": 1,
                "output_dir": str(tmp_path / "output"),
            },
            settings_path=settings_path,
            secret_store=store,
            session=session,
        )

    assert session.post_calls == []


def test_aiimage_generate_images_accepts_reference_source_size_table() -> None:
    module = load_converter_module()
    expected_sizes = {
        "1024x1024", "1536x1024", "1024x1536", "1280x720", "720x1280", "1024x768", "768x1024", "1920x816",
        "2048x2048", "2160x1440", "1440x2160", "2560x1440", "1440x2560", "2048x1536", "1536x2048", "3120x1344",
        "2880x2880", "3456x2304", "2304x3456", "3840x2160", "2160x3840", "3200x2400", "2400x3200", "3840x1648",
    }

    assert expected_sizes <= module.SUPPORTED_SIZES


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
