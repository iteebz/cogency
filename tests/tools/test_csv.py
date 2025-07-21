"""Test CSV tool."""

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
async def test_read_write(csv_tool, temp_csv):
    """Test basic read/write operations."""
    data = [{"name": "Alice", "age": "30"}]

    # Write
    result = await csv_tool.run("write", temp_csv, data=data)
    assert result["success"]

    # Read
    result = await csv_tool.run("read", temp_csv)
    assert result["success"]
    assert result["data"][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_filter(csv_tool, temp_csv):
    """Test filter operation."""
    data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "20"}]
    await csv_tool.run("write", temp_csv, data=data)

    result = await csv_tool.run("filter", temp_csv, filter_condition="int(row['age']) > 25")
    assert result["success"]
    assert len(result["filtered_data"]) == 1
    assert result["filtered_data"][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_analyze(csv_tool, temp_csv):
    """Test analyze operation."""
    data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "20"}]
    await csv_tool.run("write", temp_csv, data=data)

    result = await csv_tool.run("analyze", temp_csv)
    assert result["success"]
    assert result["total_rows"] == 2
    assert result["total_columns"] == 2


@pytest.mark.asyncio
async def test_append(csv_tool, temp_csv):
    """Test append operation."""
    data1 = [{"name": "Alice", "age": "30"}]
    data2 = [{"name": "Bob", "age": "20"}]

    await csv_tool.run("write", temp_csv, data=data1)
    await csv_tool.run("append", temp_csv, data=data2)

    result = await csv_tool.run("read", temp_csv)
    assert result["success"]
    assert len(result["data"]) == 2


@pytest.mark.asyncio
async def test_transform(csv_tool, temp_csv):
    """Test transform operation."""
    data = [{"name": "alice", "age": "30"}]
    await csv_tool.run("write", temp_csv, data=data)

    result = await csv_tool.run(
        "transform", temp_csv, transform="row['name'] = row['name'].upper()"
    )
    assert result["success"]


@pytest.mark.asyncio
async def test_error_handling(csv_tool):
    """Test error cases."""
    result = await csv_tool.run("invalid", "test.csv")
    assert "error" in result

    result = await csv_tool.run("read", "/nonexistent.csv")
    assert "error" in result
