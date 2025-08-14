"""Provider detection based on available API keys."""

from typing import TYPE_CHECKING, Optional

from .credentials import Credentials

if TYPE_CHECKING:
    from ..base import Provider as ProviderBase


def _detect_llm_provider():
    """Auto-detect available LLM provider based on credentials."""
    # Check for Gemini keys first (preferred for rotation)
    gemini_creds = Credentials.detect("gemini")
    if gemini_creds:
        from ..gemini import Gemini

        return Gemini()

    # Fall back to OpenAI
    openai_creds = Credentials.detect("openai")
    if openai_creds:
        from ..openai import OpenAI

        return OpenAI()

    # No credentials found - raise helpful error
    raise ValueError(
        "No LLM API keys found. "
        "Set GEMINI_API_KEY or OPENAI_API_KEY environment variable. "
        "See https://github.com/iteebz/cogency#installation for setup instructions."
    )


def _detect_embed_provider():
    """Auto-detect available embedding provider."""
    # Try Nomic first (dedicated embedding provider)
    try:
        nomic_creds = Credentials.detect("nomic")
        if nomic_creds:
            from ..nomic import Nomic

            return Nomic()
    except ImportError:
        pass

    # Fall back to OpenAI embeddings
    openai_creds = Credentials.detect("openai")
    if openai_creds:
        from ..openai import OpenAI

        return OpenAI()

    # No credentials found - raise helpful error
    raise ValueError(
        "No embedding API keys found. "
        "Set NOMIC_API_KEY or OPENAI_API_KEY environment variable. "
        "See https://github.com/iteebz/cogency#installation for setup instructions."
    )


def detect_llm(provider=None):
    """Setup LLM provider with auto-detection and rotation."""
    if provider is None:
        provider = _detect_llm_provider()

    # Import at runtime to avoid circular import
    from ..base import Provider
    if not isinstance(provider, Provider):
        raise ValueError(
            f"Expected Provider instance, got {type(provider)}. Use OpenAI(), Gemini(), etc."
        )

    return provider


def detect_embed(provider=None):
    """Setup embedding provider with auto-detection."""
    if provider is None:
        provider = _detect_embed_provider()

    # Import at runtime to avoid circular import
    from ..base import Provider
    if not isinstance(provider, Provider):
        raise ValueError(
            f"Expected Provider instance, got {type(provider)}. Use OpenAI(), Nomic(), etc."
        )

    return provider


def _detect_provider(providers: dict[str, str], fallback: Optional[str] = None) -> str:
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
            detected = Credentials.detect(env_prefix.lower())
            if detected and detected.get("api_key"):
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
