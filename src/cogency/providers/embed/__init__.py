"""Embedding providers with lazy loading.

Provides access to various embedding providers through a unified interface:

- Embed: Base class for all embedding providers (extension point)
- OpenAIEmbed: OpenAI embedding models
- MistralEmbed: Mistral embedding models
- NomicEmbed: Nomic embedding models
- SentenceEmbed: Local sentence-transformers models

All providers are lazy-loaded to avoid import errors for missing dependencies.
"""

# Public: Base class for extension
from .base import Embed


def __getattr__(name):
    """Lazy loading for embed providers."""
    if name == "MistralEmbed":
        from .mistral import MistralEmbed

        return MistralEmbed
    elif name == "NomicEmbed":
        from .nomic import NomicEmbed

        return NomicEmbed
    elif name == "OpenAIEmbed":
        from .openai import OpenAIEmbed

        return OpenAIEmbed
    elif name == "SentenceEmbed":
        from .sentence import SentenceEmbed

        return SentenceEmbed
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Extension point
    "Embed",
    # Configuration classes
    "MistralEmbed",
    "NomicEmbed",
    "OpenAIEmbed",
    "SentenceEmbed",
]
