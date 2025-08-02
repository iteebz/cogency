"""Embed services - lazy loading."""

from .base import Embed


def __getattr__(name):
    """Lazy loading for embed providers."""
    if name == "MistralEmbed":
        from .mistral import MistralEmbed

        return MistralEmbed
    elif name == "Nomic":
        from .nomic import Nomic

        return Nomic
    elif name == "OpenAIEmbed":
        from .openai import OpenAIEmbed

        return OpenAIEmbed
    elif name == "Sentence":
        from .sentence import Sentence

        return Sentence
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["Embed", "MistralEmbed", "Nomic", "OpenAIEmbed", "Sentence"]
