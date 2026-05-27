from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from .logger import get_logger

logger = get_logger(__name__)


class AIProvider(ABC):
    """AI 提供者基类"""

    def __init__(self, name: str, api_key: str = None):
        self.name = name
        self.api_key = api_key
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @abstractmethod
    def initialize(self) -> bool:
        """初始化提供者"""
        pass

    @abstractmethod
    def chat(self, message: str, context: list[dict] = None) -> str:
        """聊天"""
        pass

    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str = None) -> str:
        """分析图片"""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """生成文本"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI 提供者"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__("OpenAI", api_key)
        self.model = model
        self._client = None

    def initialize(self) -> bool:
        """初始化"""
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI 提供者初始化成功")
            return True
        except ImportError:
            logger.error("openai 包未安装")
            return False
        except Exception as e:
            logger.error(f"OpenAI 初始化失败: {e}")
            return False

    def chat(self, message: str, context: list[dict] = None) -> str:
        """聊天"""
        if not self._initialized:
            raise RuntimeError("OpenAI 未初始化")

        messages = context or []
        messages.append({"role": "user", "content": message})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI 聊天失败: {e}")
            raise

    def analyze_image(self, image_path: str, prompt: str = None) -> str:
        """分析图片"""
        if not self._initialized:
            raise RuntimeError("OpenAI 未初始化")

        try:
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or "描述这张图片"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ]

            response = self._client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI 图片分析失败: {e}")
            raise

    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """生成文本"""
        return self.chat(prompt)


class ClaudeProvider(AIProvider):
    """Claude 提供者"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__("Claude", api_key)
        self.model = model
        self._client = None

    def initialize(self) -> bool:
        """初始化"""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            self._initialized = True
            logger.info("Claude 提供者初始化成功")
            return True
        except ImportError:
            logger.error("anthropic 包未安装")
            return False
        except Exception as e:
            logger.error(f"Claude 初始化失败: {e}")
            return False

    def chat(self, message: str, context: list[dict] = None) -> str:
        """聊天"""
        if not self._initialized:
            raise RuntimeError("Claude 未初始化")

        messages = context or []
        messages.append({"role": "user", "content": message})

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude 聊天失败: {e}")
            raise

    def analyze_image(self, image_path: str, prompt: str = None) -> str:
        """分析图片"""
        if not self._initialized:
            raise RuntimeError("Claude 未初始化")

        try:
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": prompt or "描述这张图片"}
                    ]
                }
            ]

            response = self._client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude 图片分析失败: {e}")
            raise

    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """生成文本"""
        return self.chat(prompt)


class AIManager:
    """AI 管理器"""

    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._default_provider: Optional[str] = None

    def register_provider(self, provider: AIProvider) -> bool:
        """注册提供者"""
        try:
            if provider.initialize():
                self._providers[provider.name] = provider
                if self._default_provider is None:
                    self._default_provider = provider.name
                return True
            return False
        except Exception as e:
            logger.error(f"注册 AI 提供者失败: {e}")
            return False

    def get_provider(self, name: str = None) -> Optional[AIProvider]:
        """获取提供者"""
        if name is None:
            name = self._default_provider
        return self._providers.get(name)

    def chat(self, message: str, provider_name: str = None, **kwargs) -> str:
        """聊天"""
        provider = self.get_provider(provider_name)
        if provider is None:
            raise RuntimeError(f"AI 提供者不存在: {provider_name}")

        return provider.chat(message, **kwargs)

    def analyze_image(self, image_path: str, prompt: str = None,
                      provider_name: str = None) -> str:
        """分析图片"""
        provider = self.get_provider(provider_name)
        if provider is None:
            raise RuntimeError(f"AI 提供者不存在: {provider_name}")

        return provider.analyze_image(image_path, prompt)

    def generate_text(self, prompt: str, max_tokens: int = 1000,
                      provider_name: str = None) -> str:
        """生成文本"""
        provider = self.get_provider(provider_name)
        if provider is None:
            raise RuntimeError(f"AI 提供者不存在: {provider_name}")

        return provider.generate_text(prompt, max_tokens)

    def get_available_providers(self) -> list[str]:
        """获取可用提供者"""
        return list(self._providers.keys())

    def set_default_provider(self, name: str):
        """设置默认提供者"""
        if name in self._providers:
            self._default_provider = name


# 全局 AI 管理器实例
_ai_manager: Optional[AIManager] = None


def get_ai_manager() -> AIManager:
    """获取全局 AI 管理器实例"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIManager()
    return _ai_manager
