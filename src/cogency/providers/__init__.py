"""Services - lazy discovery for LLM and embed stores."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from cogency.utils import Provider, detect_provider

if TYPE_CHECKING:
    from cogency.providers.embed.base import Embed
    from cogency.providers.llm.base import LLM


def _get_llm_base():
    """Lazy import LLM base."""
    from .llm.base import LLM

    return LLM


def _get_embed_base():
    """Lazy import embed base."""
    from .embed.base import Embed

    return Embed


def _get_llm_cache():
    """Lazy import LLM cache."""
    from .llm.cache import LLMCache

    return LLMCache


def _get_llm_providers():
    """Lazy import LLM providers."""
    from .llm import Anthropic, Gemini, Mistral, OpenAI

    return {
        "anthropic": Anthropic,
        "gemini": Gemini,
        "mistral": Mistral,
        "openai": OpenAI,
    }


def _get_embed_providers():
    """Lazy import embed providers."""
    from .embed import MistralEmbed, Nomic, OpenAIEmbed, Sentence

    return {
        "mistral": MistralEmbed,
        "nomic": Nomic,
        "openai": OpenAIEmbed,
        "sentence": Sentence,
    }


# Provider registries with lazy detection
_llm_provider = Provider(
    _get_llm_providers,
    detect_fn=lambda: detect_provider(
        {
            "openai": "OPENAI",
            "anthropic": "ANTHROPIC",
            "gemini": "GEMINI",
            "mistral": "MISTRAL",
        },
        fallback="openai",
    ),
)

_embed_provider = Provider(
    _get_embed_providers,
    detect_fn=lambda: detect_provider(
        {
            "openai": "OPENAI",
            "mistral": "MISTRAL",
            "nomic": "NOMIC",
        },
        fallback="sentence",
    ),
)


def setup_llm(provider: str | LLM | None = None, notifier=None) -> LLM:
    """Get LLM provider class or instance with lazy discovery."""
    llm_base = _get_llm_base()
    if isinstance(provider, llm_base):
        provider.notifier = notifier
        return provider
    return _llm_provider.instance(provider, notifier=notifier)


def setup_embed(provider: str | None = None) -> Type[Embed]:
    """Get embed provider class with lazy discovery."""
    embed_class = _embed_provider.get(provider)

    def create_embed(**kwargs):
        return embed_class(**kwargs)

    create_embed.__name__ = embed_class.__name__
    create_embed.__qualname__ = embed_class.__qualname__
    return create_embed


def __getattr__(name):
    """Lazy loading for module attributes."""
    if name == "LLM":
        return _get_llm_base()
    elif name == "Embed":
        return _get_embed_base()
    elif name == "LLMCache":
        return _get_llm_cache()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["setup_llm", "setup_embed", "LLM", "Embed", "LLMCache"]
