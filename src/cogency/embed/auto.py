"""Auto-detection of embedding providers from environment variables."""
from cogency.config import get_api_keys
from .base import BaseEmbed

def auto_detect_embedder() -> BaseEmbed:
    """Auto-detect embedding provider from environment variables.
    
    Fallback chain:
    1. OpenAI
    2. Nomic
    3. Sentence Transformers (local)
    
    Returns:
        BaseEmbed: Configured embedder instance
        
    Raises:
        RuntimeError: If no API keys found and sentence-transformers is not installed.
    """
    # Build provider map dynamically based on available imports
    provider_map = {}
    
    # Try OpenAI
    try:
        from .openai import OpenAIEmbed
        provider_map["openai"] = OpenAIEmbed
    except ImportError:
        pass
    
    # Try Nomic
    try:
        from .nomic import NomicEmbed
        provider_map["nomic"] = NomicEmbed
    except ImportError:
        pass

    for provider_name, embedder_class in provider_map.items():
        api_keys = get_api_keys(provider_name)
        if api_keys:
            return embedder_class(api_keys=api_keys)

    # Fall back to local sentence transformers (no API key needed)
    try:
        from .sentence import SentenceEmbed
        return SentenceEmbed()
    except ImportError:
        pass

    # Clear error message with setup instructions
    available_providers = list(provider_map.keys())
    if not available_providers:
        raise RuntimeError(
            "No embedding providers installed. Install at least one:\n"
            "  - pip install cogency[openai]\n"
            "  - pip install cogency[nomic]\n"
            "  - pip install cogency[sentence-transformers]"
        )
    
    raise RuntimeError(
        f"No embedding provider configured. Available providers: {', '.join(available_providers)}\n"
        "Set an API key for one of the supported providers:\n"
        "  - OPENAI_API_KEY\n"
        "  - NOMIC_API_KEY\n"
        "or install sentence-transformers: pip install cogency[sentence-transformers]"
    )