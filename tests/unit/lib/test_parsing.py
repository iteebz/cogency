"""Test signature-based parsing."""

from cogency.lib.parsing import parse_with_signature
from cogency.tools.retrieve import Retrieve


def test_positional():
    """Test positional argument mapping using tool signature."""
    tool = Retrieve()
    result = parse_with_signature('USE: retrieve("Python docs, tutorials")', tool)

    assert result.success
    data = result.unwrap()
    assert data["tool"] == "retrieve"
    assert data["args"]["query"] == "Python docs, tutorials"
    assert data["args"]["limit"] == 3


def test_mixed():
    """Test mixed positional and keyword arguments."""
    tool = Retrieve()
    result = parse_with_signature('USE: retrieve("machine learning", limit=5)', tool)

    assert result.success
    data = result.unwrap()
    assert data["args"]["query"] == "machine learning"
    assert data["args"]["limit"] == 5


def test_comma_strings():
    """Test comma handling within string arguments."""
    tool = Retrieve()
    result = parse_with_signature('USE: retrieve("query, with commas, everywhere")', tool)

    assert result.success
    data = result.unwrap()
    assert data["args"]["query"] == "query, with commas, everywhere"


def test_types():
    """Test that types are preserved correctly."""
    tool = Retrieve()
    result = parse_with_signature('USE: retrieve("test", limit=10)', tool)

    assert result.success
    data = result.unwrap()
    assert data["args"]["limit"] == 10
    assert isinstance(data["args"]["limit"], int)
