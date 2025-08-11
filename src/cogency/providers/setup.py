"""Provider setup and configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Provider


def _detect_llm_provider():
    """Auto-detect available LLM provider based on credentials."""
    from cogency.utils.credentials import Credentials

    # Check for Gemini keys first (preferred for rotation)
    gemini_creds = Credentials.detect("gemini")
    if gemini_creds:
        from .gemini import Gemini

        return Gemini()

    # Fall back to OpenAI
    openai_creds = Credentials.detect("openai")
    if openai_creds:
        from .openai import OpenAI

        return OpenAI()

    # Default to OpenAI (will fail with helpful error)
    from .openai import OpenAI

    return OpenAI()


def _detect_embed_provider():
    """Auto-detect available embedding provider based on credentials."""
    from cogency.utils.credentials import Credentials

    # Check for Nomic first (preferred for embeddings)
    nomic_creds = Credentials.detect("nomic")
    if nomic_creds:
        from .nomic import Nomic

        return Nomic()

    # Fall back to OpenAI
    openai_creds = Credentials.detect("openai")
    if openai_creds:
        from .openai import OpenAI

        return OpenAI()

    # Default to OpenAI (will fail with helpful error)
    from .openai import OpenAI

    return OpenAI()


def _setup_llm(provider: Provider | None = None) -> Provider:
    """Setup LLM provider - explicit instances only."""
    from cogency.events import emit

    from .base import Provider as ProviderBase

    if provider is None:
        # Auto-detect available providers
        provider = _detect_llm_provider()

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
        # Auto-detect available providers
        provider = _detect_embed_provider()

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
