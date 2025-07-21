"""Unified provider auto-detection utilities."""
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

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
        package_names = [f"cogency[{name}]" for name in ["openai", "anthropic", "gemini", "mistral", "nomic", "sentence-transformers"]]
        raise RuntimeError(
            f"No {provider_type} providers installed. Install at least one:\n" + 
            "\n".join(f"  - pip install {pkg}" for pkg in package_names)
        )
    
    # Format API key names for the error
    api_key_names = [f"  - {provider.upper()}_API_KEY" for provider in available_providers]
    
    raise RuntimeError(
        f"No {provider_type} provider configured. Available providers: {', '.join(available_providers)}\n"
        f"Set an API key for one of the supported providers:\n" +
        "\n".join(api_key_names)
    )