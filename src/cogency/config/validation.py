"""Configuration validation for Union patterns per council ruling."""

from typing import Any, Dict


def _init_advanced_config(**config) -> Dict[str, Any]:
    """Initialize advanced configuration options.

    Args:
        **config: Configuration parameters

    Returns:
        Validated configuration dictionary
    """

    # Known configuration keys with defaults
    known_keys = {
        "identity": None,
        "output_schema": None,
        "llm": None,
        "embed": None,
        "mode": "adapt",
        "max_iterations": 10,
        "notify": True,
        "debug": False,
        "formatter": None,
        "on_notify": None,
        "robust": False,
        "observe": False,
    }

    # Filter out persist (always enabled) and validate remaining keys
    filtered_config = {k: v for k, v in config.items() if k != "persist"}
    unknown_keys = set(filtered_config.keys()) - set(known_keys.keys())
    if unknown_keys:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown_keys))}")

    # Return config with defaults applied
    result = known_keys.copy()
    result.update(filtered_config)
    return result


def validate_unions(config):
    """Validate Union pattern usage per council ruling."""
    # No conflicting configurations allowed
    if (
        hasattr(config, "memory")
        and config.memory is False
        and any(
            hasattr(config, attr) and getattr(config, attr)
            for attr in ["memory_threshold", "memory_persist", "memory_user_id"]
        )
    ):
        raise ValueError("Cannot disable memory while setting memory-specific parameters")

    if (
        hasattr(config, "robust")
        and config.robust is False
        and any(
            hasattr(config, attr) and getattr(config, attr)
            for attr in ["retry_attempts", "timeout", "rate_limit_rps"]
        )
    ):
        raise ValueError("Cannot disable robust while setting robustness parameters")

    if (
        hasattr(config, "observe")
        and config.observe is False
        and any(
            hasattr(config, attr) and getattr(config, attr)
            for attr in ["metrics", "export_format", "timing"]
        )
    ):
        raise ValueError("Cannot disable observe while setting observability parameters")
