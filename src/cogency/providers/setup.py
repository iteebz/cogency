"""Provider setup and configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Provider


def _setup_llm(provider: Provider | None = None) -> Provider:
    """Setup LLM provider - explicit instances only."""
    from cogency.events import emit

    from .base import Provider as ProviderBase

    if provider is None:
        # Default to OpenAI
        from .openai import OpenAI

        provider = OpenAI()

    if not isinstance(provider, ProviderBase):
        raise ValueError(
            f"Expected Provider instance, got {type(provider)}. Use OpenAI(), Gemini(), etc."
        )

    emit(
        "provider",
        type="llm",
        operation="setup",
        provider=provider.__class__.__name__,
        status="complete",
    )
    return provider


def _setup_embed(provider: Provider | None = None) -> Provider:
    """Setup embedding provider - explicit instances only."""
    from cogency.events import emit

    from .base import Provider as ProviderBase

    if provider is None:
        # Default to OpenAI for embeddings too
        from .openai import OpenAI

        provider = OpenAI()

    if not isinstance(provider, ProviderBase):
        raise ValueError(
            f"Expected Provider instance, got {type(provider)}. Use OpenAI(), Nomic(), etc."
        )

    emit(
        "provider",
        type="embed",
        operation="setup",
        provider=provider.__class__.__name__,
        status="complete",
    )
    return provider
