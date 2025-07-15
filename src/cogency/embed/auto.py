import os
from typing import Optional

from dotenv import load_dotenv

from .base import BaseEmbed
from .openai import OpenAIEmbed
from .nomic import NomicEmbed  
from .sentence import SentenceEmbed

# Auto-load .env file if it exists
load_dotenv()


def _detect_keys(prefix: str) -> Optional[list]:
    """Auto-detect API keys from environment with numbered fallback."""
    # Try numbered keys first (PREFIX_1, PREFIX_2, etc.)
    detected_keys = []
    for i in range(1, 10):  # Check 1-9
        key = os.getenv(f'{prefix}_{i}')
        if key:
            detected_keys.append(key)
    
    # Fall back to base key
    if not detected_keys:
        base_key = os.getenv(prefix)
        if base_key:
            detected_keys = [base_key]
    
    return detected_keys if detected_keys else None


def auto_detect_embedder() -> BaseEmbed:
    """Auto-detect embedding provider from environment variables.
    
    Returns:
        BaseEmbed: Configured embedder instance
        
    Raises:
        RuntimeError: If no API keys found
    """
    # Check for API keys in order of preference
    if openai_keys := _detect_keys("OPENAI_API_KEY"):
        return OpenAIEmbed(api_keys=openai_keys)
    
    if nomic_keys := _detect_keys("NOMIC_API_KEY"):
        return NomicEmbed(api_keys=nomic_keys)
    
    # Fall back to local sentence transformers (no API key needed)
    try:
        return SentenceEmbed()
    except ImportError:
        pass
    
    # Clear error message with setup instructions
    raise RuntimeError(
        "No embedding provider configured. Set one of:\n"
        "  export OPENAI_API_KEY=your_key\n"
        "  export NOMIC_API_KEY=your_key\n"
        "  or install sentence-transformers: pip install sentence-transformers"
    )
