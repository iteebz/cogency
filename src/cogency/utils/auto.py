"""Unified provider auto-detection utilities."""

import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


def next_key(provider: str) -> list:
    """Get API keys for a given provider from environment variables."""
    keys = []
    base_key = os.getenv(f"{provider.upper()}_API_KEY")
    if base_key:
        keys.append(base_key)

    i = 1
    while True:
        numbered_key = os.getenv(f"{provider.upper()}_API_KEY_{i}")
        if numbered_key:
            keys.append(numbered_key)
            i += 1
        else:
            break

    return keys


def detect_provider(provider_map: Dict[str, Any], provider_type: str = "provider") -> Any:
    """Auto-detect provider from environment variables.

    Args:
        provider_map: Dictionary of {provider_name: provider_class}
        provider_type: Type description for error messages (e.g., "LLM", "embedding")

    Returns:
        Configured provider instance

    Raises:
        RuntimeError: If no providers installed or no API keys found.
    """
    for provider_name, provider_class in provider_map.items():
        api_keys = next_key(provider_name)
        if api_keys:
            return provider_class(api_keys=api_keys)

    # Generate error messages
    available_providers = list(provider_map.keys())
    if not available_providers:
        package_names = [
            f"cogency[{name}]"
            for name in [
                "openai",
                "anthropic",
                "gemini",
                "mistral",
                "nomic",
                "sentence-transformers",
            ]
        ]
        raise RuntimeError(
            f"No {provider_type} providers installed. Install at least one:\n"
            + "\n".join(f"  - pip install {pkg}" for pkg in package_names)
        )

    # Format API key names for the error
    api_key_names = [f"  - {provider.upper()}_API_KEY" for provider in available_providers]

    raise RuntimeError(
        f"No {provider_type} provider configured. Available providers: {', '.join(available_providers)}\n"
        f"Set an API key for one of the supported providers:\n" + "\n".join(api_key_names)
    )


def _scan_providers(module: str, names: list[str], suffix: str) -> dict:
    """Scan for available providers."""
    providers = {}
    for name in names:
        try:
            mod = __import__(f"{module}.{name}", fromlist=[f"{name.title()}{suffix}"])
            cls = getattr(mod, f"{name.title()}{suffix}", None)
            if cls:
                providers[name] = cls
        except ImportError:
            pass
    return providers


def detect_llm():
    """Auto-detect LLM from environment."""
    providers = _scan_providers(
        "cogency.services.llm", ["openai", "anthropic", "gemini", "xai", "mistral"], "LLM"
    )
    return detect_provider(providers, "LLM")


def detect_embedder():
    """Auto-detect embedder from environment."""
    providers = _scan_providers("cogency.services.embed", ["openai", "nomic", "mistral"], "Embed")

    try:
        return detect_provider(providers, "embedding")
    except RuntimeError:
        # Fallback to local sentence transformers
        try:
            from cogency.services.embed.sentence import SentenceEmbed

            return SentenceEmbed()
        except ImportError:
            raise RuntimeError(
                "No embedding providers available. Install cogency[openai] or cogency[sentence-transformers]"
            ) from None
