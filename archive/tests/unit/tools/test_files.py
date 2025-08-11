"""File tool tests."""

import tempfile

import pytest

from cogency.tools.files import Files


@pytest.mark.asyncio
async def test_create_read():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)

        result = await tool.run(action="create", path="test.txt", content="hello")
        assert result.success
        assert "Created file" in result.data["result"]

        result = await tool.run(action="read", path="test.txt")
        assert result.success
        assert result.data["content"] == "hello"


@pytest.mark.asyncio
async def test_list():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)
        await tool.run(action="create", path="test.txt", content="test")

        result = await tool.run(action="list")
        assert result.success
        assert any(item["name"] == "test.txt" for item in result.data["items"])


@pytest.mark.asyncio
async def test_edit_single():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)
        await tool.run(action="create", path="test.txt", content="line1\nline2\nline3")

        result = await tool.run(action="edit", path="test.txt", line=2, content="EDITED")
        assert result.success

        result = await tool.run(action="read", path="test.txt")
        assert "EDITED" in result.data["content"]


@pytest.mark.asyncio
async def test_edit_range():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)
        await tool.run(action="create", path="test.txt", content="line1\nline2\nline3\nline4")

        result = await tool.run(
            action="edit", path="test.txt", start=2, end=3, content="NEW\nLINES"
        )
        assert result.success

        result = await tool.run(action="read", path="test.txt")
        content = result.data["content"]
        assert "line1" in content
        assert "NEW" in content
        assert "LINES" in content
        assert "line4" in content


@pytest.mark.asyncio
async def test_edit_full():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)
        await tool.run(action="create", path="test.txt", content="old")

        result = await tool.run(action="edit", path="test.txt", content="new content")
        assert result.success

        result = await tool.run(action="read", path="test.txt")
        assert result.data["content"] == "new content"


@pytest.mark.asyncio
async def test_errors():
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = Files(base_dir=temp_dir)

        # File not found
        result = await tool.run(action="read", path="missing.txt")
        assert not result.success

        # Unsafe path
        result = await tool.run(action="read", path="../etc/passwd")
        assert not result.success
        assert "Unsafe path" in result.error

        # File exists
        await tool.run(action="create", path="exists.txt", content="test")
        result = await tool.run(action="create", path="exists.txt", content="test")
        assert not result.success

        # Invalid line range
        await tool.run(action="create", path="lines.txt", content="a\nb\nc")
        result = await tool.run(action="edit", path="lines.txt", line=99, content="x")
        assert not result.success
