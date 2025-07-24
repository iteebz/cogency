"""Identity processing - keep it simple."""

from typing import Optional


def process_identity(raw_identity: Optional[str]) -> str:
    """Simple identity processing."""
    return raw_identity or ""
