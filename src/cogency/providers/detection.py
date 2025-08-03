"""Provider detection based on available API keys."""

from typing import Dict, Optional

from cogency.utils.keys import KeyManager


def _detect_llm():
    """Detect LLM provider based on available imports AND API keys."""
    from .lazy import _llms

    # Get actually available providers (post-import)
    available_providers = _llms()

    # Check for API keys in preference order, but only for available providers
    preference_order = ["openai", "anthropic", "gemini", "mistral"]

    for provider in preference_order:
        if provider in available_providers:
            try:
                keys = KeyManager.detect_keys(provider)
                if keys:
                    return provider
            except Exception:
                continue

    # Fallback to openai if available (should always be available as core dependency)
    if "openai" in available_providers:
        return "openai"

    # Last resort - return first available provider
    if available_providers:
        return next(iter(available_providers))

    raise ValueError("No LLM providers available")


def _detect_provider(providers: Dict[str, str], fallback: Optional[str] = None) -> str:
    """Generic provider detection based on available API keys.

    Args:
        providers: Dict mapping provider names to their env key prefixes
                  e.g. {"openai": "OPENAI", "anthropic": "ANTHROPIC"}
        fallback: Default provider if no keys detected

    Returns:
        Provider name with available keys, or fallback
    """
    # Check providers in order of preference (first wins)
    for provider, env_prefix in providers.items():
        try:
            # Try to detect keys for this provider
            keys = KeyManager.detect_keys(env_prefix.lower())
            if keys:
                return provider
        except Exception:
            continue

    if fallback:
        return fallback

    available = ", ".join(providers.keys())
    required_keys = [f"{prefix}_API_KEY" for prefix in providers.values()]
    raise ValueError(
        f"No API keys found. Available providers: {available}. "
        f"Set one of: {', '.join(required_keys)}. "
        f"See https://github.com/iteebz/cogency#installation for setup instructions."
    )
