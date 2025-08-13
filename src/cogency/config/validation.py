"""Configuration validation for Union patterns per council ruling."""

from typing import Any


def validate_config_keys(**config) -> dict[str, Any]:
    """Validate configuration keys to prevent typos.

    Args:
        **config: Configuration parameters

    Returns:
        Original config dict (no modification)
    """
    # Known configuration keys (no defaults - dataclass handles that)
    known_keys = {"identity", "llm", "embed", "mode", "max_iterations", "notify"}

    # Validate keys (no filtering needed)
    unknown_keys = set(config.keys()) - known_keys
    if unknown_keys:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown_keys))}")

    # Return original config unchanged
    return config
