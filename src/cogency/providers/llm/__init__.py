"""Language model providers with lazy loading.

Provides access to various LLM providers through a unified interface:

- LLM: Base class for all language model providers (extension point)
- OpenAI: GPT models (always available)
- Anthropic: Claude models (optional extra)
- Gemini: Google's models (optional extra)
- Mistral: Mistral AI models (optional extra)
- Ollama: Local model serving (optional extra)
- LLMCache: Response caching layer

All providers are lazy-loaded to avoid import errors for missing dependencies.
"""

# Public: Base class for extension
from .base import LLM

# Public: Response caching
from .cache import LLMCache


def __getattr__(name):
    """Lazy loading for LLM providers."""
    if name == "Anthropic":
        from .anthropic import Anthropic

        return Anthropic
    elif name == "Gemini":
        from .gemini import Gemini

        return Gemini
    elif name == "Mistral":
        from .mistral import Mistral

        return Mistral
    elif name == "OpenAI":
        from .openai import OpenAI

        return OpenAI
    elif name == "Ollama":
        from .ollama import Ollama

        return Ollama
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Extension point
    "LLM",
    # Configuration classes
    "Anthropic",
    "Gemini",
    "Mistral",
    "OpenAI",
    "Ollama",
    # Utilities
    "LLMCache",
]
