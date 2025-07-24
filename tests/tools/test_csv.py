"""Test simplified CSV tool."""

import tempfile
from pathlib import Path

import pytest

from cogency.tools.csv import CSV


@pytest.fixture
def csv_tool():
    return CSV()


@pytest.fixture
def temp_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_path = f.name
    yield csv_path
    Path(csv_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_write_read(csv_tool, temp_csv):
    """Test basic write then read operations."""
    data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    # Write
    result = await csv_tool.run("write", temp_csv, data=data)
    assert result.success
    assert result.data["rows_written"] == 2

    # Read
    result = await csv_tool.run("read", temp_csv)
    assert result.success
    assert result.data["row_count"] == 2
    assert result.data["data"][0]["name"] == "Alice"
    assert result.data["data"][1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_append(csv_tool, temp_csv):
    """Test append operation."""
    data1 = [{"name": "Alice", "age": "30"}]
    data2 = [{"name": "Bob", "age": "25"}]

    # Write initial data
    await csv_tool.run("write", temp_csv, data=data1)

    # Append more data
    result = await csv_tool.run("append", temp_csv, data=data2)
    assert result.success
    assert result.data["rows_appended"] == 1

    # Read all data
    result = await csv_tool.run("read", temp_csv)
    assert result.success
    assert result.data["row_count"] == 2
    assert result.data["data"][0]["name"] == "Alice"
    assert result.data["data"][1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_append_to_nonexistent_file(csv_tool, temp_csv):
    """Test append creates file if it doesn't exist."""
    data = [{"name": "Alice", "age": "30"}]

    # Remove the temp file so it doesn't exist
    Path(temp_csv).unlink(missing_ok=True)

    # Append should create the file
    result = await csv_tool.run("append", temp_csv, data=data)
    assert result.success
    assert result.data["rows_written"] == 1  # Returns write result when creating new file


@pytest.mark.asyncio
async def test_error_handling(csv_tool):
    """Test error cases."""
    # Invalid operation
    result = await csv_tool.run("invalid", "test.csv")
    assert not result.success
    assert "Invalid operation" in result.error

    # Read nonexistent file
    result = await csv_tool.run("read", "/nonexistent.csv")
    assert not result.success
    assert "File not found" in result.error

    # Write without data
    result = await csv_tool.run("write", "test.csv", data=None)
    assert not result.success
    assert "No data provided" in result.error

    # Append without data
    result = await csv_tool.run("append", "test.csv", data=None)
    assert not result.success
    assert "No data provided" in result.error


@pytest.mark.asyncio
async def test_empty(csv_tool, temp_csv):
    """Test handling empty CSV data."""
    data = []

    result = await csv_tool.run("write", temp_csv, data=data)
    assert not result.success
    assert "No data provided" in result.error
