"""Provider setup and configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from cogency.utils.registry import Provider

from .detection import _detect_llm, _detect_provider
from .lazy import _embedders, _llms

if TYPE_CHECKING:
    from cogency.providers.embed.base import Embed
    from cogency.providers.llm.base import LLM


# Provider registries with zero ceremony defaults
_llm_provider = Provider(
    _llms,
    detect_fn=_detect_llm,
)

_embed_provider = Provider(
    _embedders,
    detect_fn=lambda: _detect_provider(
        {
            "openai": "OPENAI",
            "mistral": "MISTRAL",
            "nomic": "NOMIC",
        },
        fallback="sentence",
    ),
)


def _setup_llm(provider: str | LLM | None = None, notifier=None) -> LLM:
    """Setup LLM provider with lazy discovery."""
    from .lazy import _llm_base

    _llm_base = _llm_base()
    if isinstance(provider, _llm_base):
        provider.notifier = notifier
        return provider

    try:
        return _llm_provider.instance(provider, notifier=notifier)
    except ValueError as e:
        # Add installation hint for missing optional providers
        if provider in ["gemini", "anthropic", "mistral"]:
            raise ValueError(f"{e}\n\nTo use {provider}: pip install cogency[{provider}]") from e
        raise


def _setup_embed(provider: str | None = None) -> Type[Embed]:
    """Setup embedding provider with lazy discovery."""
    embed_class = _embed_provider.get(provider)

    def create_embed(**kwargs):
        return embed_class(**kwargs)

    create_embed.__name__ = embed_class.__name__
    create_embed.__qualname__ = embed_class.__qualname__
    return create_embed
