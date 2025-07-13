"""Simple configuration management for Cogency."""

import os
from dataclasses import dataclass
from typing import List

from dotenv import find_dotenv, load_dotenv


@dataclass
class Config:
    """Simple configuration container."""

    # LLM settings
    api_keys: List[str]
    model: str = "gemini-2.5-flash"
    timeout: float = 15.0
    temperature: float = 0.7

    # Agent settings
    agent_name: str = "CogencyAgent"
    max_depth: int = 10

    # Tool settings
    file_base_dir: str = "workspace"
    web_max_results: int = 5
    web_rate_limit: float = 1.0


def load_api_keys() -> List[str]:
    """Load API keys from environment variables."""
    keys = []

    # Try numbered keys first (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for i in range(1, 10):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key and key.strip():
            keys.append(key.strip())
        else:
            break

    # Fallback to single key
    if not keys:
        single_key = os.getenv("GEMINI_API_KEY")
        if single_key and single_key.strip():
            keys.append(single_key.strip())

    return keys


def get_config() -> Config:
    """Get configuration from environment variables."""
    # Load .env file if present
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file)

    api_keys = load_api_keys()
    if not api_keys:
        raise ValueError(
            "No API keys found. Set GEMINI_API_KEY or GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc."
        )

    return Config(
        api_keys=api_keys,
        model=os.getenv("COGENCY_MODEL", "gemini-2.5-flash"),
        timeout=float(os.getenv("COGENCY_TIMEOUT", "15.0")),
        temperature=float(os.getenv("COGENCY_TEMPERATURE", "0.7")),
        agent_name=os.getenv("COGENCY_AGENT_NAME", "CogencyAgent"),
        max_depth=int(os.getenv("COGENCY_MAX_DEPTH", "10")),
        file_base_dir=os.getenv("COGENCY_FILE_BASE_DIR", "workspace"),
        web_max_results=int(os.getenv("COGENCY_WEB_MAX_RESULTS", "5")),
        web_rate_limit=float(os.getenv("COGENCY_WEB_RATE_LIMIT", "1.0")),
    )
