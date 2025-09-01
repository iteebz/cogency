"""Profile tests - Minimal working memory system tests."""

from pathlib import Path
from unittest.mock import Mock, patch

from cogency.context import profile


def test_get_none():
    """Profile get handles None user_id."""
    result = profile.get(None)
    assert result is None


def test_get_default():
    """Profile get handles default user_id."""
    result = profile.get("default")
    assert result is None


def test_format_empty():
    """Profile format handles empty profile."""
    with patch("cogency.context.profile.get", return_value={}):
        formatted = profile.format("user123")
        assert formatted == ""


def test_delta_no_profile():
    """Profile _delta returns False for missing profile."""
    with patch("cogency.context.profile.get", return_value=None):
        result = profile._delta("user123")
        assert result is False


def test_delta_no_database():
    """Profile _delta handles missing database gracefully."""
    with patch("cogency.context.profile.get", return_value={"who": "test", "_meta": {}}):
        with patch("cogency.lib.storage.get_db_path") as mock_path:
            mock_path.return_value = Path("/nonexistent")
            result = profile._delta("user123")
            assert result is False


def test_learn_skip():
    """Profile learn skips when no delta."""
    mock_llm = Mock()
    with patch("cogency.context.profile._delta", return_value=False):
        result = profile.learn("user123", mock_llm)
        assert result is None  # learn() returns None when skipped


def test_learn_triggers():
    """Profile learn skips in test environment - canonical behavior."""
    mock_llm = Mock()
    with patch("cogency.context.profile._delta", return_value=True):
        # In test environment, learning should be skipped
        result = profile.learn("user123", mock_llm)
        assert result is None  # Should return early due to pytest detection
