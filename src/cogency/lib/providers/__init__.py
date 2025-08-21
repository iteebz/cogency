"""Providers: External service integrations."""

from .anthropic import Anthropic
from .gemini import Gemini
from .openai import OpenAI

__all__ = ["OpenAI", "Anthropic", "Gemini", "create_llm", "create_embedder"]


def create_llm(provider: str):
    """Create LLM instance from string shortcut."""
    if isinstance(provider, str):
        if provider.lower() in ["openai", "gpt"]:
            return OpenAI()
        if provider.lower() in ["anthropic", "claude"]:
            return Anthropic()
        if provider.lower() in ["gemini", "google"]:
            return Gemini()
        raise ValueError(f"Unknown provider: {provider}")
    return provider


def create_embedder(provider: str):
    """Create Embedder instance from string shortcut."""
    if isinstance(provider, str):
        if provider.lower() in ["openai", "gpt"]:
            return OpenAI()
        if provider.lower() in ["gemini", "google"]:
            return Gemini()
        raise ValueError(f"Unknown embedder provider: {provider}")
    return provider
