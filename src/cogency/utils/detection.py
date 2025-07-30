"""Provider detection based on available API keys."""

from typing import Dict, Optional

from .keys import KeyManager


def detect_provider(providers: Dict[str, str], fallback: Optional[str] = None) -> str:
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
            keys = KeyManager._detect_keys_from_env(env_prefix.lower())
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
