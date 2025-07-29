"""Services - automagical discovery for LLM and embed stores."""

from typing import Optional, Type, Union

from cogency.utils import Provider, detect_provider

from .embed import MistralEmbed, Nomic, OpenAIEmbed, Sentence
from .embed.base import Embed
from .llm import Anthropic, Gemini, Mistral, OpenAI, xAI
from .llm.base import LLM
from .llm.cache import LLMCache

# Provider registries with auto-detection
_llm_provider = Provider(
    {
        "anthropic": Anthropic,
        "gemini": Gemini,
        "mistral": Mistral,
        "openai": OpenAI,
        "xai": xAI,
    },
    detect_fn=lambda: detect_provider(
        {
            "openai": "OPENAI",
            "anthropic": "ANTHROPIC",
            "gemini": "GEMINI",
            "mistral": "MISTRAL",
            "xai": "XAI",
        },
        fallback="openai",
    ),
)

_embed_provider = Provider(
    {
        "mistral": MistralEmbed,
        "nomic": Nomic,
        "openai": OpenAIEmbed,
        "sentence": Sentence,
    },
    detect_fn=lambda: detect_provider(
        {
            "openai": "OPENAI",
            "mistral": "MISTRAL",
            "nomic": "NOMIC",
        },
        fallback="sentence",
    ),
)


def setup_llm(provider: Optional[Union[str, LLM]] = None) -> LLM:
    """Get LLM provider class or instance with automagical discovery."""
    if isinstance(provider, LLM):
        return provider
    return _llm_provider.instance(provider)


def setup_embed(provider: Optional[str] = None) -> Type[Embed]:
    """Get embed provider class with automagical discovery."""
    return _embed_provider.get(provider)


__all__ = ["setup_llm", "setup_embed", "LLM", "Embed", "LLMCache"]
