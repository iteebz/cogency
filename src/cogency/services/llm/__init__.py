"""LLM services - auto-discovery and detection."""

from .base import BaseLLM


def detect_llm():
    """Auto-detect LLM provider based on environment."""
    import os

    # Check for API keys in order of preference
    if os.getenv("ANTHROPIC_API_KEY"):
        from .anthropic import AnthropicLLM

        return AnthropicLLM
    elif os.getenv("OPENAI_API_KEY"):
        from .openai import OpenAILLM

        return OpenAILLM
    elif os.getenv("GEMINI_API_KEY"):
        from .gemini import GeminiLLM

        return GeminiLLM
    elif os.getenv("MISTRAL_API_KEY"):
        from .mistral import MistralLLM

        return MistralLLM
    elif os.getenv("XAI_API_KEY"):
        from .xai import XaiLLM

        return XaiLLM
    else:
        raise ValueError(
            "No LLM API key found. Please set one of ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, or XAI_API_KEY."
        )


__all__ = ["BaseLLM", "detect_llm"]
