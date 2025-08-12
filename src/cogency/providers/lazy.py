"""Lazy loading utilities for providers."""


def _llm_base():
    """Lazy import Provider base - backwards compatibility."""
    from .base import Provider

    return Provider


def _embed_base():
    """Lazy import Provider base - backwards compatibility."""
    from .base import Provider

    return Provider


def _llm_cache():
    """Lazy import Cache."""
    from .cache import Cache

    return Cache


def _llms():
    """Lazy import LLM providers with helpful error messages."""
    providers = {}

    # OpenAI is always available (core dependency)
    from .openai import OpenAI

    providers["openai"] = OpenAI

    # Optional providers with graceful failure
    try:
        from .anthropic import Anthropic

        providers["anthropic"] = Anthropic
    except ImportError:
        pass

    try:
        from .gemini import Gemini

        providers["gemini"] = Gemini
    except ImportError:
        pass

    try:
        from .mistral import Mistral

        providers["mistral"] = Mistral
    except ImportError:
        pass

    try:
        from .ollama import Ollama

        providers["ollama"] = Ollama
    except ImportError:
        pass

    return providers


def _embedders():
    """Lazy import embed providers with graceful failure."""
    providers = {}

    try:
        from .openai import OpenAI

        providers["openai"] = OpenAI
    except ImportError:
        pass

    try:
        from .nomic import Nomic

        providers["nomic"] = Nomic
    except ImportError:
        pass

    try:
        from .mistral import Mistral

        providers["mistral"] = Mistral
    except ImportError:
        pass

    return providers
