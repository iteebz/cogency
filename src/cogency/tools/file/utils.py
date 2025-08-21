"""File utilities: Shared logic for file operations."""

from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format file size human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


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
