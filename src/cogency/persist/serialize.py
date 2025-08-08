"""Serialization utilities for persistence - handles enums, datetime, dataclasses."""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from cogency.state.user import UserProfile


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


def serialize_profile(profile: UserProfile) -> Dict[str, Any]:
    """Convert profile to dict with datetime serialization."""
    profile_dict = asdict(profile)
    profile_dict["created_at"] = profile.created_at.isoformat()
    profile_dict["last_updated"] = profile.last_updated.isoformat()
    return profile_dict


def deserialize_profile(profile_data: Dict[str, Any]) -> UserProfile:
    """Convert dict to profile with datetime deserialization."""
    data = profile_data.copy()

    # Handle datetime deserialization
    if "created_at" in data:
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    if "last_updated" in data:
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])

    return UserProfile(**data)
