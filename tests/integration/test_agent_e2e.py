"""End-to-end system tests - full CLI integration."""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_cli_basic():
    """CLI executes basic query successfully."""
    result = subprocess.run(
        ["python", "-m", "cogency", "What is 2+2?"], capture_output=True, text=True, timeout=30
    )

    # Should complete successfully
    assert result.returncode == 0

    # Should contain reasonable response
    assert len(result.stdout.strip()) > 0
    assert "4" in result.stdout or "four" in result.stdout.lower()


@pytest.mark.asyncio
async def test_cli_with_tools():
    """CLI can execute tool-based workflows."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory for sandboxed execution
        result = subprocess.run(
            ["python", "-m", "cogency", "Create a file called test.txt with content 'hello'"],
            capture_output=True,
            text=True,
            cwd=temp_dir,
            timeout=30,
        )

        # Should complete successfully
        assert result.returncode == 0

        # Should have created the file
        test_file = Path(temp_dir) / "test.txt"
        if test_file.exists():
            assert test_file.read_text().strip() == "hello"


@pytest.mark.asyncio
async def test_cli_error_handling():
    """CLI handles errors gracefully."""
    # Invalid command structure
    result = subprocess.run(
        ["python", "-m", "cogency", "--invalid-flag", "query"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Should exit with error code
    assert result.returncode != 0

    # Should provide helpful error message
    assert len(result.stderr) > 0 or "error" in result.stdout.lower()
