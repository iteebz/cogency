"""Security utilities tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cogency.tools.security import (
    redact_secrets,
    safe_path,
    validate_input,
)


def test_validate_input_safe():
    """validate_input allows safe content."""
    assert validate_input("Hello world")
    assert validate_input("python script.py")
    assert validate_input("./relative/path")
    assert validate_input("")
    assert validate_input("file.txt")


def test_validate_input_dangerous():
    """validate_input blocks dangerous patterns."""
    assert not validate_input("rm -rf /")
    assert not validate_input("format c:")
    assert not validate_input("shutdown now")
    assert not validate_input("del /s")
    assert not validate_input("../../../etc/passwd")
    assert not validate_input("..\\..\\..\\windows")
    assert not validate_input("path%2e%2e%2ftraversal")


def test_validate_input_case_insensitive():
    """validate_input is case insensitive."""
    assert not validate_input("RM -RF /")
    assert not validate_input("FORMAT C:")
    assert not validate_input("SHUTDOWN")


def test_safe_path_valid():
    """safe_path resolves valid paths."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Valid relative paths - use resolved base for comparison
        base_resolved = base.resolve()

        result = safe_path(base, "file.txt")
        assert result == base_resolved / "file.txt"

        result = safe_path(base, "subdir/file.txt")
        assert result == base_resolved / "subdir" / "file.txt"

        result = safe_path(base, "./file.txt")
        assert result == base_resolved / "file.txt"


def test_safe_path_traversal():
    """safe_path blocks path traversal."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Path traversal attempts
        with pytest.raises(ValueError, match="escapes base directory"):
            safe_path(base, "../outside")

        with pytest.raises(ValueError, match="escapes base directory"):
            safe_path(base, "../../etc/passwd")

        with pytest.raises(ValueError, match="escapes base directory"):
            safe_path(base, "/absolute/path")


def test_safe_path_empty():
    """safe_path rejects empty path."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        with pytest.raises(ValueError, match="empty"):
            safe_path(base, "")

        with pytest.raises(ValueError, match="empty"):
            safe_path(base, None)


def test_redact_secrets_api_keys():
    """redact_secrets removes API keys."""
    text = "My key is sk-abc123def456 for OpenAI"
    result = redact_secrets(text)
    assert "sk-abc123def456" not in result
    assert "[REDACTED]" in result
    assert "OpenAI" in result


def test_redact_secrets_aws_keys():
    """redact_secrets removes AWS keys."""
    text = "AWS key: AKIA1234567890ABCDEF"
    result = redact_secrets(text)
    assert "AKIA1234567890ABCDEF" not in result
    assert "[REDACTED]" in result


def test_redact_secrets_multiple():
    """redact_secrets handles multiple secrets."""
    text = "OpenAI: sk-abc123 and AWS: AKIA9876543210FEDCBA"
    result = redact_secrets(text)
    assert "sk-abc123" not in result
    assert "AKIA9876543210FEDCBA" not in result
    assert result.count("[REDACTED]") == 2


def test_redact_secrets_safe_text():
    """redact_secrets preserves safe text."""
    text = "Just normal text with no secrets"
    result = redact_secrets(text)
    assert result == text
    assert "[REDACTED]" not in result
