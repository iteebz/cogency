"""Centralized configuration for Cogency."""
import os
from dotenv import load_dotenv

load_dotenv()


def get_api_keys(provider: str) -> list:
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
