"""Test Profile functionality."""

from datetime import datetime

from cogency.memory.compression import compress
from cogency.state import Profile


def test_constructor():
    """Test Profile constructor."""
    profile = Profile(user_id="test_user")

    assert profile.user_id == "test_user"
    assert profile.preferences == {}
    assert profile.goals == []
    assert profile.expertise_areas == []
    assert profile.communication_style == ""
    assert profile.projects == {}
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.last_updated, datetime)


def test_compress_empty():
    """Test compression with empty profile."""
    profile = Profile(user_id="test_user")

    result = compress(profile)
    assert result == ""


def test_compress_populated():
    """Test compression with populated profile."""
    profile = Profile(user_id="test_user")
    profile.communication_style = "concise"
    profile.goals = ["goal1", "goal2", "goal3"]
    profile.preferences = {"format": "json", "detail": "high"}
    profile.projects = {"proj1": "description1", "proj2": "description2"}
    profile.expertise_areas = ["python", "ml", "data"]

    result = compress(profile)

    assert "COMMUNICATION: concise" in result
    assert "CURRENT GOALS:" in result
    assert "goal1" in result
    assert "PREFERENCES:" in result
    assert "format: json" in result
    assert "ACTIVE PROJECTS:" in result
    assert "proj1: description1" in result
    assert "EXPERTISE: python, ml, data" in result


def test_compress_truncation():
    """Test compression respects max_tokens limit."""
    profile = Profile(user_id="test_user")
    profile.communication_style = "very detailed and comprehensive style"
    profile.goals = ["very long goal description"] * 10

    result = compress(profile, max_tokens=50)
    assert len(result) <= 50


def test_compress_recent():
    """Test compression shows most recent items."""
    profile = Profile(user_id="test_user")

    # Add many goals to test recent selection
    profile.goals = [f"goal_{i}" for i in range(10)]

    result = compress(profile)

    # Should show last 3 goals
    assert "goal_7" in result
    assert "goal_8" in result
    assert "goal_9" in result
    assert "goal_0" not in result


def test_profile_mutability():
    """Test Profile fields can be modified."""
    profile = Profile(user_id="test_user")

    # Update preferences
    profile.preferences["theme"] = "dark"
    profile.preferences["format"] = "markdown"
    assert profile.preferences == {"theme": "dark", "format": "markdown"}

    # Update goals
    profile.goals.append("learn python")
    profile.goals.append("build app")
    assert len(profile.goals) == 2
    assert "learn python" in profile.goals

    # Update expertise areas
    profile.expertise_areas.extend(["python", "web development"])
    assert len(profile.expertise_areas) == 2
    assert "python" in profile.expertise_areas

    # Update communication style
    profile.communication_style = "technical and detailed"
    assert profile.communication_style == "technical and detailed"

    # Update projects
    profile.projects["project1"] = "description1"
    profile.projects["project2"] = "description2"
    assert len(profile.projects) == 2
    assert profile.projects["project1"] == "description1"


def test_profile_independence():
    """Test that different Profile instances are independent."""
    profile1 = Profile(user_id="user1")
    profile2 = Profile(user_id="user2")

    # Modify profile1
    profile1.preferences["theme"] = "dark"
    profile1.goals.append("goal1")
    profile1.communication_style = "technical"

    # profile2 should be unaffected
    assert profile2.preferences == {}
    assert profile2.goals == []
    assert profile2.communication_style == ""
    assert profile2.user_id == "user2"


def test_timestamps():
    """Test timestamp behavior."""
    profile = Profile(user_id="test_user")

    # Timestamps should be set
    assert profile.created_at is not None
    assert profile.last_updated is not None

    # Both should be datetime objects
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.last_updated, datetime)

    # Initially they should be equal
    assert profile.created_at == profile.last_updated
