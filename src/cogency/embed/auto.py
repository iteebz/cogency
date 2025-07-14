import os
from typing import Optional

from dotenv import load_dotenv

from .base import BaseEmbed
from .nomic import NomicEmbed


def auto_detect_embedder() -> BaseEmbed:
    """Auto-detect embedding provider from environment variables.
    
    Returns:
        BaseEmbed: Configured embedder instance
        
    Raises:
        RuntimeError: If no API keys found
    """
    load_dotenv() # Load .env file

    # Check for API keys in order of preference
    if nomic_key := os.getenv("NOMIC_API_KEY"):
        return NomicEmbed(api_key=nomic_key)
    
    # Clear error message with setup instructions
    raise RuntimeError(
        "No embedding provider configured. Set one of:\n"
        "  export NOMIC_API_KEY=your_key"
    )
