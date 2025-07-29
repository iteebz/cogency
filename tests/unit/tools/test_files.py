"""File tool business logic tests."""

import tempfile

import pytest

from cogency.tools.files import Files


@pytest.mark.asyncio
async def test_files_create_read():
    """Test file creation and reading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)

        # Create and read file
        result = await files_tool.run(action="create", filename="test.txt", content="hello world")
        assert result.success
        assert "Created file" in result.data["result"]

        result = await files_tool.run(action="read", filename="test.txt")
        assert result.success
        assert result.data["content"] == "hello world"


@pytest.mark.asyncio
async def test_files_list():
    """Test file listing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)

        await files_tool.run(action="create", filename="test.txt", content="test")

        result = await files_tool.run(action="list")
        assert result.success
        data = result.data
        assert "items" in data
        assert any(item["name"] == "test.txt" for item in data["items"])


@pytest.mark.asyncio
async def test_files_edit():
    """Test file editing operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)

        # Create file with multiple lines
        content = "line 1\nline 2\nline 3"
        await files_tool.run(action="create", filename="test.txt", content=content)

        # Edit single line
        result = await files_tool.run(
            action="edit", filename="test.txt", line=2, content="EDITED LINE 2"
        )
        assert result.success
        assert "Edited line 2" in result.data["result"]

        result = await files_tool.run(action="read", filename="test.txt")
        assert result.success
        assert "EDITED LINE 2" in result.data["content"]


@pytest.mark.asyncio
async def test_secure():
    """Test security protections."""
    files_tool = Files()

    # Path traversal protection
    result = await files_tool.run(action="read", filename="../../../etc/passwd")
    assert not result.success
    assert "Unsafe path access" in result.error
