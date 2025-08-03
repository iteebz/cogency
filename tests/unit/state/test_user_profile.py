"""Test UserProfile functionality."""

from datetime import datetime

from cogency.memory.compression import compress
from cogency.state.user_profile import UserProfile


def test_constructor():
    """Test UserProfile constructor."""
    profile = UserProfile(user_id="test_user")

    assert profile.user_id == "test_user"
    assert profile.preferences == {}
    assert profile.goals == []
    assert profile.expertise_areas == []
    assert profile.communication_style == ""
    assert profile.projects == {}
    assert profile.interests == []
    assert profile.constraints == []
    assert profile.success_patterns == []
    assert profile.failure_patterns == []
    assert profile.interaction_count == 0
    assert profile.synthesis_version == 1
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.last_updated, datetime)


def testcompress_empty():
    """Test compression with empty profile."""
    profile = UserProfile(user_id="test_user")

    result = compress(profile)
    assert result == ""


def testcompress_populated():
    """Test compression with populated profile."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "concise"
    profile.goals = ["goal1", "goal2", "goal3"]
    profile.preferences = {"format": "json", "detail": "high"}
    profile.projects = {"proj1": "description1", "proj2": "description2"}
    profile.expertise_areas = ["python", "ml", "data"]
    profile.constraints = ["time", "budget"]

    result = compress(profile)

    assert "COMMUNICATION: concise" in result
    assert "CURRENT GOALS:" in result
    assert "goal1" in result
    assert "PREFERENCES:" in result
    assert "format: json" in result
    assert "ACTIVE PROJECTS:" in result
    assert "proj1: description1" in result
    assert "EXPERTISE: python, ml, data" in result
    assert "CONSTRAINTS: time; budget" in result


def testcompress_truncation():
    """Test compression respects max_tokens limit."""
    profile = UserProfile(user_id="test_user")
    profile.communication_style = "very detailed and comprehensive style"
    profile.goals = ["very long goal description"] * 10

    result = compress(profile, max_tokens=50)
    assert len(result) <= 50


def testcompress_recent():
    """Test compression shows most recent items."""
    profile = UserProfile(user_id="test_user")

    # Add many goals to test recent selection
    profile.goals = [f"goal_{i}" for i in range(10)]

    result = compress(profile)

    # Should show last 3 goals
    assert "goal_7" in result
    assert "goal_8" in result
    assert "goal_9" in result
    assert "goal_0" not in result


def test_update_preferences():
    """Test updating preferences from interaction."""
    profile = UserProfile(user_id="test_user")

    insights = {"preferences": {"format": "markdown", "style": "detailed"}}

    profile.update_from_interaction(insights)

    assert profile.preferences == {"format": "markdown", "style": "detailed"}
    assert profile.interaction_count == 1
    assert profile.last_updated > profile.created_at


def test_update_goals():
    """Test updating goals with bounded growth."""
    profile = UserProfile(user_id="test_user")

    # Add initial goals
    insights = {"goals": ["goal1", "goal2"]}
    profile.update_from_interaction(insights)

    assert "goal1" in profile.goals
    assert "goal2" in profile.goals

    # Add duplicate goal (should be ignored)
    insights = {"goals": ["goal1", "goal3"]}
    profile.update_from_interaction(insights)

    assert len([g for g in profile.goals if g == "goal1"]) == 1
    assert "goal3" in profile.goals

    # Test bounded growth
    for i in range(15):
        insights = {"goals": [f"goal_{i}"]}
        profile.update_from_interaction(insights)

    assert len(profile.goals) <= 10


def test_update_expertise():
    """Test updating expertise areas with bounded growth."""
    profile = UserProfile(user_id="test_user")

    insights = {"expertise": ["python", "machine learning"]}
    profile.update_from_interaction(insights)

    assert "python" in profile.expertise_areas
    assert "machine learning" in profile.expertise_areas

    # Test bounded growth
    for i in range(20):
        insights = {"expertise": [f"skill_{i}"]}
        profile.update_from_interaction(insights)

    assert len(profile.expertise_areas) <= 15


def test_update_projects():
    """Test updating projects with bounded growth."""
    profile = UserProfile(user_id="test_user")

    insights = {"project_context": {"proj1": "desc1", "proj2": "desc2"}}
    profile.update_from_interaction(insights)

    assert profile.projects["proj1"] == "desc1"
    assert profile.projects["proj2"] == "desc2"

    # Test bounded growth
    for i in range(15):
        insights = {"project_context": {f"proj_{i}": f"desc_{i}"}}
        profile.update_from_interaction(insights)

    assert len(profile.projects) <= 10


def test_update_patterns():
    """Test updating success/failure patterns."""
    profile = UserProfile(user_id="test_user")

    # Add success pattern
    insights = {"success_pattern": "clear requirements work well"}
    profile.update_from_interaction(insights)

    assert "clear requirements work well" in profile.success_patterns

    # Add failure pattern
    insights = {"failure_pattern": "vague requests cause confusion"}
    profile.update_from_interaction(insights)

    assert "vague requests cause confusion" in profile.failure_patterns

    # Test duplicate patterns are ignored
    insights = {"success_pattern": "clear requirements work well"}
    profile.update_from_interaction(insights)

    assert len([p for p in profile.success_patterns if p == "clear requirements work well"]) == 1

    # Test bounded growth
    for i in range(10):
        insights = {"success_pattern": f"pattern_{i}"}
        profile.update_from_interaction(insights)

    assert len(profile.success_patterns) <= 5


def test_update_comprehensive():
    """Test updating all fields in one interaction."""
    profile = UserProfile(user_id="test_user")

    insights = {
        "preferences": {"format": "json"},
        "goals": ["complete project"],
        "expertise": ["python"],
        "communication_style": "technical",
        "project_context": {"proj1": "test project"},
        "success_pattern": "detailed specs work",
        "failure_pattern": "rushed work fails",
    }

    profile.update_from_interaction(insights)

    assert profile.preferences["format"] == "json"
    assert "complete project" in profile.goals
    assert "python" in profile.expertise_areas
    assert profile.communication_style == "technical"
    assert profile.projects["proj1"] == "test project"
    assert "detailed specs work" in profile.success_patterns
    assert "rushed work fails" in profile.failure_patterns
    assert profile.interaction_count == 1
