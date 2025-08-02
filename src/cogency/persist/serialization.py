"""Datetime serialization utilities for profiles."""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from cogency.state.user_profile import UserProfile


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
