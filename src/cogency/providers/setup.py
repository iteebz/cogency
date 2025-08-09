"""Provider setup and configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from cogency.utils.registry import Provider as Registry

from .detection import _detect_llm, _detect_provider
from .lazy import _embedders, _llms

if TYPE_CHECKING:
    from .base import Provider


# Provider registries with zero ceremony defaults
_llm_provider = Registry(
    _llms,
    detect_fn=_detect_llm,
)

_embed_provider = Registry(
    _embedders,
    detect_fn=lambda: _detect_provider(
        {
            "openai": "OPENAI",
            "mistral": "MISTRAL",
            "nomic": "NOMIC",
        },
        fallback="openai",
    ),
)


def _setup_llm(provider: str | Provider | None = None) -> Provider:
    """Setup LLM provider with lazy discovery."""
    from cogency.events import emit

    from .base import Provider as ProviderBase

    emit("provider", type="llm", operation="setup", provider=str(provider), status="start")

    try:
        if isinstance(provider, ProviderBase):
            emit(
                "provider",
                type="llm",
                operation="setup",
                provider="existing_instance",
                status="complete",
            )
            return provider

        # Discovery and instantiation
        result = _llm_provider.instance(provider)
        emit(
            "provider",
            type="llm",
            operation="setup",
            provider=getattr(getattr(result, "__class__", None), "__name__", str(provider)),
            status="complete",
        )
        return result

    except ValueError as e:
        # Add installation hint for missing optional providers
        if provider in ["gemini", "anthropic", "mistral"]:
            error_msg = f"{e}\n\nTo use {provider}: pip install cogency[{provider}]"
            emit(
                "provider",
                type="llm",
                operation="setup",
                provider=str(provider),
                status="error",
                error=error_msg,
            )
            raise ValueError(error_msg) from e

        emit(
            "provider",
            type="llm",
            operation="setup",
            provider=str(provider),
            status="error",
            error=str(e),
        )
        raise


def _setup_embed(provider: str | None = None) -> Type[Provider]:
    """Setup embedding provider with lazy discovery."""
    from cogency.events import emit

    emit("provider", type="embed", operation="setup", provider=str(provider), status="start")

    try:
        embed_class = _embed_provider.get(provider)

        def create_provider(**kwargs):
            return embed_class(**kwargs)

        create_provider.__name__ = embed_class.__name__
        create_provider.__qualname__ = embed_class.__qualname__

        emit(
            "provider",
            type="embed",
            operation="setup",
            provider=embed_class.__name__,
            status="complete",
        )
        return create_provider

    except Exception as e:
        emit(
            "provider",
            type="embed",
            operation="setup",
            provider=str(provider),
            status="error",
            error=str(e),
        )
        raise
