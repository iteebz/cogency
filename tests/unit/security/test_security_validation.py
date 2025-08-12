"""Tests for input validation and security checks."""

import pytest

from cogency.security.validation import MAX_QUERY_LENGTH, validate_query


def test_validate_query_valid():
    """Test validate_query with valid inputs."""
    # Normal query
    result = validate_query("What is the weather today?")
    assert result is None

    # Query with special characters
    result = validate_query("How do I use @mentions and #hashtags?")
    assert result is None

    # Query with numbers
    result = validate_query("Calculate 2 + 2")
    assert result is None

    # Query with newlines
    result = validate_query("First line\nSecond line")
    assert result is None

    # Query with Unicode
    result = validate_query("What is the meaning of 生活?")
    assert result is None


def test_validate_query_empty():
    """Test validate_query with empty inputs."""
    # Empty string
    result = validate_query("")
    assert result is not None
    assert "Empty query not allowed" in result

    # None input
    result = validate_query(None)
    assert result is not None
    assert "Empty query not allowed" in result

    # Whitespace only
    result = validate_query("   ")
    assert result is not None
    assert "Empty query not allowed" in result

    # Tab and newline only
    result = validate_query("\t\n  \r")
    assert result is not None
    assert "Empty query not allowed" in result


def test_validate_query_too_long():
    """Test validate_query with overly long inputs."""
    # Query exactly at limit should be valid
    max_query = "x" * MAX_QUERY_LENGTH
    result = validate_query(max_query)
    assert result is None

    # Query over limit should be invalid
    over_limit_query = "x" * (MAX_QUERY_LENGTH + 1)
    result = validate_query(over_limit_query)
    assert result is not None
    assert "Query too long" in result
    assert f"max {MAX_QUERY_LENGTH:,} characters" in result

    # Much longer query
    very_long_query = "x" * (MAX_QUERY_LENGTH * 2)
    result = validate_query(very_long_query)
    assert result is not None
    assert "Query too long" in result


def test_validate_query_edge_cases():
    """Test validate_query with edge cases."""
    # Single character
    result = validate_query("?")
    assert result is None

    # Single space (should be invalid after strip)
    result = validate_query(" ")
    assert result is not None
    assert "Empty query not allowed" in result

    # Query with only whitespace at boundaries
    result = validate_query("  valid query  ")
    assert result is None  # Should be valid after strip check

    # Query with mixed whitespace
    result = validate_query("\t\nvalid\r\n")
    assert result is None


def test_validate_query_unicode_handling():
    """Test validate_query handles Unicode correctly."""
    # Unicode characters should count correctly for length
    unicode_query = "🤖" * 1000  # 1000 emoji characters
    result = validate_query(unicode_query)
    assert result is None  # Should be under limit

    # Unicode that would exceed limit
    long_unicode = "🤖" * (MAX_QUERY_LENGTH + 1)
    result = validate_query(long_unicode)
    assert result is not None
    assert "Query too long" in result


def test_validate_query_return_format():
    """Test validate_query return format."""
    # Valid queries return None
    result = validate_query("valid query")
    assert result is None

    # Invalid queries return string error messages
    result = validate_query("")
    assert isinstance(result, str)
    assert len(result) > 0

    result = validate_query("x" * (MAX_QUERY_LENGTH + 1))
    assert isinstance(result, str)
    assert len(result) > 0


def test_max_query_length_constant():
    """Test MAX_QUERY_LENGTH constant."""
    # Should be a reasonable positive integer
    assert isinstance(MAX_QUERY_LENGTH, int)
    assert MAX_QUERY_LENGTH > 0
    assert MAX_QUERY_LENGTH == 10000  # Current expected value


def test_validate_query_security_characters():
    """Test validate_query with potentially problematic characters."""
    # HTML/XML tags - should be allowed (handled by downstream processing)
    result = validate_query("<script>alert('test')</script>")
    assert result is None  # Validation doesn't filter content, just structure

    # SQL injection patterns - should be allowed (not SQL context)
    result = validate_query("'; DROP TABLE users; --")
    assert result is None

    # Command injection patterns - should be allowed (validation is structural)
    result = validate_query("$(rm -rf /)")
    assert result is None

    # Path traversal - should be allowed
    result = validate_query("../../../etc/passwd")
    assert result is None


def test_validate_query_various_lengths():
    """Test validate_query with various lengths around the limit."""
    test_lengths = [
        MAX_QUERY_LENGTH - 10,  # Just under limit
        MAX_QUERY_LENGTH - 1,  # One under limit
        MAX_QUERY_LENGTH,  # At limit
        MAX_QUERY_LENGTH + 1,  # One over limit
        MAX_QUERY_LENGTH + 10,  # Just over limit
    ]

    for length in test_lengths:
        query = "x" * length
        result = validate_query(query)

        if length <= MAX_QUERY_LENGTH:
            assert result is None, f"Query of length {length} should be valid"
        else:
            assert result is not None, f"Query of length {length} should be invalid"
            assert "Query too long" in result


def test_validate_query_whitespace_variants():
    """Test validate_query with different whitespace scenarios."""
    whitespace_cases = [
        "",  # Empty
        " ",  # Single space
        "\t",  # Tab
        "\n",  # Newline
        "\r",  # Carriage return
        "  \t\n  ",  # Mixed whitespace
        "\u00a0",  # Non-breaking space
        "\u2000",  # En quad
        "\u2028",  # Line separator
    ]

    for case in whitespace_cases:
        result = validate_query(case)
        assert result is not None, f"Whitespace case '{repr(case)}' should be invalid"
        assert "Empty query not allowed" in result


def test_validate_query_with_meaningful_content():
    """Test validate_query with content that has meaning after stripping."""
    cases_with_content = [
        "  hello  ",
        "\thello\n",
        "\n\n  meaningful content  \r\n",
        "  question?  ",
    ]

    for case in cases_with_content:
        result = validate_query(case)
        assert result is None, f"Case with content '{case}' should be valid"


def test_error_message_formatting():
    """Test error message formatting includes helpful details."""
    # Empty query error
    result = validate_query("")
    assert "⚠️" in result  # Has warning emoji
    assert "Empty query not allowed" in result

    # Length error
    result = validate_query("x" * (MAX_QUERY_LENGTH + 1))
    assert "⚠️" in result  # Has warning emoji
    assert "Query too long" in result
    assert "10,000" in result or str(MAX_QUERY_LENGTH) in result  # Shows the limit
    assert "characters" in result


def test_validate_query_boolean_logic():
    """Test validate_query boolean return logic."""
    # Valid cases should return falsy (None)
    valid_result = validate_query("valid query")
    assert not valid_result

    # Invalid cases should return truthy (string)
    invalid_result = validate_query("")
    assert invalid_result

    # Can be used in if statements
    query = "test"
    error = validate_query(query)
    if error:
        pytest.fail("Valid query should not produce error")

    empty_query = ""
    error = validate_query(empty_query)
    if not error:
        pytest.fail("Invalid query should produce error")
