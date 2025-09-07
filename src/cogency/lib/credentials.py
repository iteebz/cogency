"""Credential detection and environment management."""

import os

from dotenv import load_dotenv

# Load environment variables with override=True to ensure .env values replace empty env vars
load_dotenv(override=True)


def detect_api_key(service: str) -> str | None:
    """Detect API key with intelligent service mappings and rotation support."""
    # Dotenv is loaded at import time, so we can just check env vars
    patterns = [
        f"{service.upper()}_API_KEY",
        f"{service.upper()}_KEY",
        f"{service}_API_KEY",
        f"{service}_KEY",
    ]

    # Service aliases
    if service == "gemini":
        patterns.extend(["GOOGLE_API_KEY", "GOOGLE_KEY"])

    # Check standard patterns
    for pattern in patterns:
        if pattern in os.environ and os.environ[pattern]:
            return os.environ[pattern]

    # Check rotation keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for pattern in patterns:
        if pattern.endswith("_API_KEY"):
            for i in range(1, 10):  # Check _1 through _9
                rotation_key = f"{pattern}_{i}"
                if rotation_key in os.environ and os.environ[rotation_key]:
                    return os.environ[rotation_key]

    return None

    # Check rotation keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for pattern in patterns:
        if pattern.endswith("_API_KEY"):
            for i in range(1, 10):  # Check _1 through _9
                rotation_key = f"{pattern}_{i}"
                if rotation_key in os.environ:
                    return os.environ[rotation_key]

    return None
