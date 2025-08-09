"""Unified provider management - LLM and embedding capabilities.

This module handles automatic discovery and setup of AI providers.
It provides:

- Provider: Unified base class supporting LLM and/or embedding capabilities
- Cache: Caching layer for both LLM responses and embeddings
- Automatic provider detection based on available API keys
- Lazy loading of optional provider dependencies

The module supports OpenAI, Anthropic, Gemini, Mistral, Ollama (core), and Nomic (optional extras).
Providers are auto-detected based on available imports and API keys.

Note: Provider instances are typically created automatically by Agent initialization.
"""

# Public: Unified base class and cache for creating custom providers
# Concrete provider implementations
from .anthropic import Anthropic
from .base import Provider
from .cache import Cache
from .gemini import Gemini
from .groq import Groq
from .mistral import Mistral
from .nomic import Nomic
from .ollama import Ollama
from .openai import OpenAI
from .openrouter import OpenRouter

__all__ = [
    # Public provider base class for extensions
    "Provider",
    "Cache",
    # Concrete providers
    "Anthropic",
    "Gemini",
    "Groq",
    "Mistral",
    "Nomic",
    "Ollama",
    "OpenAI",
    "OpenRouter",
]
