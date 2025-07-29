"""Test SQL tool."""

import tempfile
from pathlib import Path

import pytest

from cogency.tools.sql import SQL


@pytest.fixture
def sql_tool():
    return SQL()


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield f"sqlite:///{db_path}"
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_crud(sql_tool, temp_db):
    """Test complete CRUD operations in SQLite."""
    # Create table
    result = await sql_tool.run(
        query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
        connection=temp_db,
    )
    assert result.success
    assert result.data["query_type"] == "modify"

    # Insert data
    result = await sql_tool.run(
        query="INSERT INTO users (name, age) VALUES ('Alice', 30), ('Bob', 25)",
        connection=temp_db,
    )
    assert result.success
    assert result.data["rows_affected"] == 2

    # Select data
    result = await sql_tool.run(query="SELECT * FROM users ORDER BY name", connection=temp_db)
    assert result.success
    assert result.data["query_type"] == "select"
    assert len(result.data["rows"]) == 2
    assert result.data["rows"][0]["name"] == "Alice"

    # Update data
    result = await sql_tool.run(
        query="UPDATE users SET age = 31 WHERE name = 'Alice'", connection=temp_db
    )
    assert result.success
    assert result.data["rows_affected"] == 1

    # Delete data
    result = await sql_tool.run(query="DELETE FROM users WHERE name = 'Bob'", connection=temp_db)
    assert result.success
    assert result.data["rows_affected"] == 1


@pytest.mark.asyncio
async def test_pragma(sql_tool, temp_db):
    """Test SQLite PRAGMA commands."""
    result = await sql_tool.run(query="PRAGMA table_info(sqlite_master)", connection=temp_db)
    assert result.success


@pytest.mark.asyncio
async def test_params(sql_tool, temp_db):
    """Test parameterized queries."""
    # Create table first
    await sql_tool.run(query="CREATE TABLE test (id INTEGER, name TEXT)", connection=temp_db)

    # Test with parameters
    result = await sql_tool.run(
        query="INSERT INTO test (id, name) VALUES (?, ?)",
        connection=temp_db,
        params=[1, "Alice"],
    )
    assert result.success


@pytest.mark.asyncio
async def test_errors(sql_tool, temp_db):
    """Test various error conditions."""
    # Syntax error
    result = await sql_tool.run(query="INVALID SQL QUERY", connection=temp_db)
    assert not result.success
