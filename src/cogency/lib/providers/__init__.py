"""Providers: External service integrations."""

from typing import Union

from ..credentials import detect_api_key
from .anthropic import Anthropic
from .gemini import Gemini
from .openai import OpenAI, generate

__all__ = ["OpenAI", "Anthropic", "Gemini", "create_llm", "create_embedder", "generate"]


def create_llm(provider: Union[str, object]) -> object:
    """Create LLM instance from string shortcut or return object.

    Args:
        provider: String shortcut ("openai", "claude", "gemini") or provider instance

    Returns:
        LLM provider instance

    Raises:
        ValueError: If string provider unknown or API key not found
    """
    if isinstance(provider, str):
        if provider.lower() in ["openai", "gpt"]:
            api_key = detect_api_key("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY.")
            return OpenAI(api_key=api_key)
        if provider.lower() in ["anthropic", "claude"]:
            api_key = detect_api_key("anthropic")
            if not api_key:
                raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY.")
            return Anthropic(api_key=api_key)
        if provider.lower() in ["gemini", "google"]:
            api_key = detect_api_key("gemini")
            if not api_key:
                raise ValueError("Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY.")
            return Gemini(api_key=api_key)
        raise ValueError(f"Unknown provider: {provider}")
    return provider


def create_embedder(provider: Union[str, object]) -> object:
    """Create Embedder instance from string shortcut or return object.

    Args:
        provider: String shortcut ("openai", "gemini") or embedder instance

    Returns:
        Embedder provider instance

    Raises:
        ValueError: If string provider unknown or API key not found
    """
    if isinstance(provider, str):
        if provider.lower() in ["openai", "gpt"]:
            api_key = detect_api_key("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY.")
            return OpenAI(api_key=api_key)
        if provider.lower() in ["gemini", "google"]:
            api_key = detect_api_key("gemini")
            if not api_key:
                raise ValueError("Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY.")
            return Gemini(api_key=api_key)
        raise ValueError(f"Unknown embedder provider: {provider}")
    return provider
