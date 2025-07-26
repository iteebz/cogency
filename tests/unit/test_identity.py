"""Identity processing tests."""

from cogency.identity import process_identity


def test_with_value():
    result = process_identity("test-agent")
    assert result == "test-agent"


def test_identity_none():
    result = process_identity(None)
    assert result == ""


def test_empty_string():
    result = process_identity("")
    assert result == ""
