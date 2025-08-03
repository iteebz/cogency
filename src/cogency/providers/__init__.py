"""LLM and embedding provider management.

This module handles automatic discovery and setup of AI providers (LLM and embedding).
It provides:

- LLM: Base class for language model providers
- Embed: Base class for embedding providers
- LLMCache: Caching layer for LLM responses
- Automatic provider detection based on available API keys
- Lazy loading of optional provider dependencies

The module supports OpenAI (core), Anthropic, Gemini, Mistral (optional extras).
Providers are auto-detected based on available imports and API keys.

Note: Provider instances are typically created automatically by Agent initialization.
"""

# Public: Base classes for creating custom providers
from .lazy import _embed_base, _llm_base, _llm_cache


def __getattr__(name):
    """Lazy loading for module attributes."""
    if name == "LLM":
        return _llm_base()
    elif name == "Embed":
        return _embed_base()
    elif name == "LLMCache":
        return _llm_cache()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Public provider base classes for extensions
    "LLM",
    "Embed",
    "LLMCache",
]
