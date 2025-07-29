"""Services - automagical discovery for LLM and embed backends."""

from typing import Optional, Type

from cogency.utils.discovery import AutoRegistry

from .embed.base import Embed
from .llm.base import LLM

# Automagical registries
_llm_registry = AutoRegistry("cogency.services.llm", LLM)
_embed_registry = AutoRegistry("cogency.services.embed", Embed)


def llm(provider: Optional[str] = None) -> Type[LLM]:
    """Get LLM provider class with automagical discovery."""
    if provider is None:
        from cogency.utils import detect_llm

        return detect_llm()
    return _llm_registry.get(provider)


def embed(provider: Optional[str] = None) -> Type[Embed]:
    """Get embed provider class with automagical discovery."""
    if provider is None:
        provider = "openai"  # Default
    return _embed_registry.get(provider)


__all__ = ["llm", "embed", "LLM", "Embed"]
