"""Auto-detection of embedding providers from environment variables."""
from cogency.config import get_api_keys
from .base import BaseEmbed
from .openai import OpenAIEmbed
from .nomic import NomicEmbed
from .sentence import SentenceEmbed

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
    provider_map = {
        "openai": OpenAIEmbed,
        "nomic": NomicEmbed,
    }

    for provider_name, embedder_class in provider_map.items():
        api_keys = get_api_keys(provider_name)
        if api_keys:
            return embedder_class(api_keys=api_keys)

    # Fall back to local sentence transformers (no API key needed)
    try:
        return SentenceEmbed()
    except ImportError:
        pass

    # Clear error message with setup instructions
    raise RuntimeError(
        "No embedding provider configured. Set an API key for one of the supported providers:\n"
        "  - OPENAI_API_KEY\n"
        "  - NOMIC_API_KEY\n"
        "or install sentence-transformers: pip install sentence-transformers"
    )