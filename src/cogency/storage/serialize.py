"""Serialization utilities for persistence - handles enums, datetime, dataclasses."""

from dataclasses import asdict


def serialize_dataclass(obj) -> dict:
    """Serialize dataclass to dict, handling enums and datetime objects."""
    result = asdict(obj)

    def convert_values(item):
        if hasattr(item, "value"):  # Enum object
            return item.value
        elif hasattr(item, "isoformat"):  # datetime object
            return item.isoformat()
        elif isinstance(item, dict):
            return {k: convert_values(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [convert_values(v) for v in item]
        return item

    return convert_values(result)
