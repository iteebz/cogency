"""Tests for memory namespace API.

Tests define the expected memory.* namespace interface for user profile
and persistent memory management.
"""

import pytest

from cogency.context import memory


def test_get_empty_memory():
    """Get returns None or empty dict for new user."""
    user_id = "test_user_1"
    # Clear any existing profile first
    memory.clear(user_id)
    result = memory.get(user_id)
    assert result is None or result == {}


def test_update_user_memory():
    """Update stores user profile data."""
    user_id = "test_user_2"
    profile_data = {
        "name": "John Doe",
        "preferences": {"theme": "dark", "language": "en"},
        "context": "Software engineer working on AI projects",
    }

    memory.update(user_id, profile_data)
    retrieved = memory.get(user_id)

    assert retrieved == profile_data


def test_user_memory_isolation():
    """Memory isolated between different users."""
    user_a = "user_a"
    user_b = "user_b"

    profile_a = {"name": "Alice", "role": "designer"}
    profile_b = {"name": "Bob", "role": "developer"}

    memory.update(user_a, profile_a)
    memory.update(user_b, profile_b)

    assert memory.get(user_a) == profile_a
    assert memory.get(user_b) == profile_b
    assert memory.get(user_a) != memory.get(user_b)


def test_clear_user_memory():
    """Clear removes all memory for specific user."""
    user_id = "test_clear"
    profile = {"name": "To Be Cleared", "data": "temporary"}

    memory.update(user_id, profile)
    assert memory.get(user_id) == profile

    memory.clear(user_id)
    result = memory.get(user_id)
    assert result is None or result == {}


def test_memory_namespace_api_consistency():
    """Verify memory namespace provides consistent API."""
    user_id = "api_test"

    # These should all work without error
    memory.get(user_id)
    memory.update(user_id, {})
    memory.clear(user_id)

    # Verify the API is available
    assert hasattr(memory, "get")
    assert hasattr(memory, "update")
    assert hasattr(memory, "clear")
    assert callable(memory.get)
    assert callable(memory.update)
    assert callable(memory.clear)


def test_concurrent_memory_access():
    """Multiple users can access memory simultaneously."""
    users = [f"concurrent_user_{i}" for i in range(5)]

    # Each user stores their profile
    for i, user_id in enumerate(users):
        profile = {"id": i, "name": f"User {i}", "timestamp": f"2025-01-{i+1:02d}"}
        memory.update(user_id, profile)

    # Verify each user has independent memory
    for i, user_id in enumerate(users):
        retrieved = memory.get(user_id)
        assert retrieved["id"] == i
        assert retrieved["name"] == f"User {i}"


def test_none_user_id():
    """Should validate None user_id."""
    with pytest.raises(ValueError):
        memory.get(None)


def test_empty_user_id_memory():
    """Should handle empty string user_id."""
    user_id = ""
    data = {"empty_user": True}

    memory.update(user_id, data)
    assert memory.get(user_id) == data


def test_none_memory_data():
    """Should handle None memory data."""
    user_id = "none_data_user"

    memory.update(user_id, None)
    result = memory.get(user_id)

    # Should handle None gracefully
    assert result is None or result == {}


def test_nested_dict_data():
    """Should handle deeply nested dictionary data."""
    user_id = "nested_user"
    data = {
        "profile": {
            "personal": {"name": "Deep User", "age": 30},
            "professional": {"role": "Engineer", "skills": ["Python", "AI"]},
        },
        "settings": {"ui": {"theme": "dark"}},
    }

    memory.update(user_id, data)
    retrieved = memory.get(user_id)

    assert retrieved == data
    assert retrieved["profile"]["personal"]["name"] == "Deep User"
