"""Path management for cogency directories."""

from pathlib import Path


def get_cogency_dir(base_dir: str = None) -> Path:
    """Get cogency directory, configurable like requests."""
    if base_dir:
        cogency_dir = Path(base_dir)
    else:
        cogency_dir = Path(".cogency")  # Local to current directory
    cogency_dir.mkdir(exist_ok=True)
    return cogency_dir


class Paths:
    """Clean path management for cogency directories."""

    @staticmethod
    def db(subpath: str = None, base_dir: str = None) -> Path:
        """Get database path with optional subpath."""
        base = get_cogency_dir(base_dir) / "store.db"
        return base / subpath if subpath else base

    @staticmethod
    def sandbox(subpath: str = None, base_dir: str = None) -> Path:
        """Get sandbox path with optional subpath."""
        base = get_cogency_dir(base_dir) / "sandbox"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base

    @staticmethod
    def evals(subpath: str = None, base_dir: str = None) -> Path:
        """Get evaluations path with optional subpath."""
        base = get_cogency_dir(base_dir) / "evals"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base
