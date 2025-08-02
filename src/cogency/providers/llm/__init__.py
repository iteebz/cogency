"""LLM services - lazy loading."""

from .base import LLM
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
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "LLM",
    "Anthropic",
    "Gemini",
    "Mistral",
    "OpenAI",
    "LLMCache",
]
