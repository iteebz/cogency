"""API key rotation with automatic rate limit handling and service aliases."""

import asyncio
import os
import random
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

# Load .env with override to replace empty environment variables
load_dotenv(override=True)


def load_keys(prefix: str) -> list[str]:
    """Load API keys supporting numbered keys and service aliases (e.g., GEMINI→GOOGLE)."""
    keys = []

    patterns = [
        f"{prefix}_API_KEY",
        f"{prefix}_KEY",
    ]

    if prefix == "GEMINI":
        patterns.extend(["GOOGLE_API_KEY", "GOOGLE_KEY"])

    for pattern in patterns:
        for i in range(1, 21):
            key = os.environ.get(f"{pattern}_{i}")
            if key and key not in keys:
                keys.append(key)

    for pattern in patterns:
        key = os.environ.get(pattern)
        if key and key not in keys:
            keys.append(key)

    return keys


def get_api_key(service: str) -> str | None:
    """Get API key for service."""
    keys = load_keys(service.upper())
    return keys[0] if keys else None


def is_rate_limit_error(error: str) -> bool:
    """Detect rate limit errors."""
    rate_signals = [
        "quota",
        "rate limit",
        "429",
        "throttle",
        "exceeded",
        "503",
        "unavailable",
        "resource_exhausted",
    ]
    return any(signal in error.lower() for signal in rate_signals)


async def with_rotation(prefix: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with random start + cycle on rate limits."""
    keys = load_keys(prefix.upper())
    if not keys:
        raise RuntimeError(f"No {prefix} API keys found")

    # Random start for natural load distribution
    start = random.randint(0, len(keys) - 1)

    # Try all keys starting from random position
    for offset in range(len(keys)):
        key = keys[(start + offset) % len(keys)]
        try:
            return await func(key, *args, **kwargs)
        except Exception as e:
            # Only retry on rate limits
            if not is_rate_limit_error(str(e)):
                raise e

            # Simple backoff: wait before trying next key
            if offset < len(keys) - 1:  # Not last key
                await asyncio.sleep(1.0 + random.uniform(0, 1))  # 1-2s jitter
            else:  # Last key
                raise e  # All keys exhausted
    return None
