from pathlib import Path

import pytest

from cogency.tools import Read


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test_file.txt"
    lines = [f"Line {i}" for i in range(10)]
    file_path.write_text("\n".join(lines))
    return file_path


@pytest.mark.asyncio
async def test_read_default(temp_file: Path):
    """Test that reading a file with no pagination args reads the whole file."""
    result = await Read.execute(file=str(temp_file), access="system")

    assert not result.error
    assert f"Read {temp_file!s} (10 lines)" == result.outcome
    assert result.content is not None
    assert len(result.content.splitlines()) == 10
    assert "Line 0" in result.content
    assert "Line 9" in result.content


@pytest.mark.asyncio
async def test_read_with_lines(temp_file: Path):
    """Test that reading with `lines` paginates correctly from the start."""
    result = await Read.execute(file=str(temp_file), lines=5, access="system")

    assert not result.error
    assert f"Read {temp_file!s} (5 lines)" == result.outcome
    assert result.content is not None
    assert len(result.content.splitlines()) == 5
    assert "0: Line 0" in result.content
    assert "4: Line 4" in result.content
    assert "Line 5" not in result.content


@pytest.mark.asyncio
async def test_read_with_start_and_lines(temp_file: Path):
    """Test that reading with `start` and `lines` paginates correctly."""
    result = await Read.execute(file=str(temp_file), start=5, lines=3, access="system")

    assert not result.error
    assert f"Read {temp_file!s} (3 lines)" == result.outcome
    assert result.content is not None
    assert len(result.content.splitlines()) == 3
    assert "5: Line 5" in result.content
    assert "7: Line 7" in result.content
    assert "Line 4" not in result.content
    assert "Line 8" not in result.content


@pytest.mark.asyncio
async def test_read_file_not_found():
    """Test that reading a non-existent file returns an error."""
    result = await Read.execute(file="non_existent_file.txt", access="system")

    assert result.error
    assert "not found" in result.outcome
