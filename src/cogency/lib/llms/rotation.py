import asyncio
import os
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from dotenv import load_dotenv

T = TypeVar("T")

load_dotenv(override=True)

# Base delay between key rotation attempts. Accounts for typical API rate limit
# reset windows (1-2s) and network round-trip time. Additional random jitter (0-1s)
# is added during rotation to prevent thundering herd when multiple processes retry.
KEY_ROTATION_DELAY = 1.0


def load_keys(prefix: str) -> list[str]:
    """Load API keys supporting numbered keys and service aliases (e.g., GEMINI→GOOGLE)."""
    keys: list[str] = []
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
    keys = load_keys(service.upper())
    return keys[0] if keys else None


def is_rate_limit_error(error: str) -> bool:
    rate_signals = [
        "quota",
        "rate limit",
        "429",
        "throttle",
        "exceeded",
        "503",
        "unavailable",
        "resource_exhausted",
        "exhausted",
    ]
    return any(signal in error.lower() for signal in rate_signals)


async def with_rotation(prefix: str, func: Callable[[str], Awaitable[T]], *args: object, **kwargs: object) -> T:
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

            if offset < len(keys) - 1:
                await asyncio.sleep(KEY_ROTATION_DELAY + random.uniform(0, 1))
            else:
                raise e
    raise RuntimeError(f"No {prefix} API keys available")
