"""Lazy loading utilities for providers."""


def _llm_base():
    """Lazy import LLM base."""
    from .llm.base import LLM

    return LLM


def _embed_base():
    """Lazy import embed base."""
    from .embed.base import Embed

    return Embed


def _llm_cache():
    """Lazy import LLM cache."""
    from .llm.cache import LLMCache

    return LLMCache


def _llms():
    """Lazy import LLM providers with helpful error messages."""
    providers = {}

    # OpenAI is always available (core dependency)
    from .llm import OpenAI

    providers["openai"] = OpenAI

    # Optional providers with graceful failure
    try:
        from .llm import Anthropic

        providers["anthropic"] = Anthropic
    except ImportError:
        pass

    try:
        from .llm import Gemini

        providers["gemini"] = Gemini
    except ImportError:
        pass

    try:
        from .llm import Mistral

        providers["mistral"] = Mistral
    except ImportError:
        pass

    return providers


def _embedders():
    """Lazy import embed providers."""
    from .embed import MistralEmbed, NomicEmbed, OpenAIEmbed, SentenceEmbed

    return {
        "mistral": MistralEmbed,
        "nomic": NomicEmbed,
        "openai": OpenAIEmbed,
        "sentence": SentenceEmbed,
    }
