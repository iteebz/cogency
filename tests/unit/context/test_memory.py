"""Memory context tests."""

from cogency.context import memory


def test_graceful_none():
    """Memory handles None user_id gracefully."""
    result = memory(None)
    assert result == ""


def test_graceful_invalid():
    """Memory handles invalid user_id gracefully."""
    result = memory("nonexistent_user_12345")
    assert result == ""


def test_graceful_empty():
    """Memory handles empty user_id gracefully."""
    result = memory("")
    assert result == ""


def test_valid_user():
    """Memory returns string for valid user_id."""
    result = memory("test")
    assert isinstance(result, str)
