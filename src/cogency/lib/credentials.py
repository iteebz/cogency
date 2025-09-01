"""Credential detection and environment management."""

import os
from pathlib import Path
from typing import Optional


def load_env():
    """Load .env file if present."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def detect_api_key(service: str) -> Optional[str]:
    """Detect API key with intelligent service mappings and rotation support."""
    load_env()

    patterns = [
        f"{service.upper()}_API_KEY",
        f"{service.upper()}_KEY",
        f"{service}_API_KEY",
        f"{service}_KEY",
    ]

    # Service aliases
    if service == "gemini":
        patterns.extend(["GOOGLE_API_KEY", "GOOGLE_KEY"])

    # Check standard patterns first
    for pattern in patterns:
        if pattern in os.environ:
            return os.environ[pattern]

    # Check rotation keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for pattern in patterns:
        if pattern.endswith("_API_KEY"):
            for i in range(1, 10):  # Check _1 through _9
                rotation_key = f"{pattern}_{i}"
                if rotation_key in os.environ:
                    return os.environ[rotation_key]

    return None
