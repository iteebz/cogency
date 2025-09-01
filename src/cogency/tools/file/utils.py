"""File utilities: Shared logic for file operations."""

import time
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format file size human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


def format_relative_time(timestamp: float) -> str:
    """Format timestamp as ultra-short relative time."""
    now = time.time()
    diff = now - timestamp

    # Handle future timestamps (shouldn't happen, but be safe)
    if diff < 0:
        return "just now"

    # Less than a minute
    if diff < 60:
        return "just now"

    # Minutes - ultra short
    if diff < 3600:  # < 1 hour
        minutes = int(diff / 60)
        return f"{minutes}m"

    # Hours - ultra short
    if diff < 86400:  # < 24 hours
        hours = int(diff / 3600)
        return f"{hours}h"

    # Days - hybrid approach
    if diff < 604800:  # < 1 week
        days = int(diff / 86400)
        if days == 1:
            return "yesterday"  # Keep this human word
        return f"{days}d"

    # Weeks - ultra short
    if diff < 2592000:  # < 30 days
        weeks = int(diff / 604800)
        return f"{weeks}w"

    # Months - ultra short
    if diff < 31536000:  # < 1 year
        months = int(diff / 2592000)
        return f"{months}mo"

    # Years - ultra short
    years = int(diff / 31536000)
    return f"{years}y"


def categorize_file(file_path: Path) -> str:
    """Smart file categorization for context."""
    ext = file_path.suffix.lower()
    name = file_path.name.lower()

    # Configuration files
    if any(x in name for x in ["config", "settings", ".env", ".ini"]) or ext in [
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".ini",
    ]:
        return "config"

    # Source code
    if ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"]:
        return "code"

    # Documentation
    if ext in [".md", ".rst", ".txt", ".doc", ".docx"] or name in [
        "readme",
        "license",
        "changelog",
    ]:
        return "docs"

    # Data files
    if ext in [".csv", ".json", ".xml", ".sql", ".db", ".sqlite"]:
        return "data"

    # Tests
    if "test" in name or name.startswith("spec_"):
        return "test"

    # Build/Package
    if name in ["package.json", "requirements.txt", "cargo.toml", "pom.xml", "build.gradle"]:
        return "build"

    return "misc"
