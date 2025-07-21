"""Test File tool business logic."""
import pytest
import tempfile

from cogency.tools.files import Files


@pytest.mark.asyncio
async def test_files_create_read():
    """Test file creation and reading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)
        
        # Create and read file
        result = await files_tool.run(action="create", filename="test.txt", content="hello world")
        assert "Created file" in result["result"]
        
        result = await files_tool.run(action="read", filename="test.txt")
        assert result["content"] == "hello world"


@pytest.mark.asyncio  
async def test_files_list():
    """Test file listing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)
        
        await files_tool.run(action="create", filename="test.txt", content="test")
        
        result = await files_tool.run(action="list")
        assert "items" in result
        assert any(item["name"] == "test.txt" for item in result["items"])


@pytest.mark.asyncio
async def test_files_edit():
    """Test file editing operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files_tool = Files(base_dir=temp_dir)
        
        # Create file with multiple lines
        content = "line 1\nline 2\nline 3"
        await files_tool.run(action="create", filename="test.txt", content=content)
        
        # Edit single line
        result = await files_tool.run(action="edit", filename="test.txt", line=2, content="EDITED LINE 2")
        assert "Edited line 2" in result["result"]
        
        result = await files_tool.run(action="read", filename="test.txt")
        assert "EDITED LINE 2" in result["content"]


@pytest.mark.asyncio
async def test_files_security():
    """Test security protections."""
    files_tool = Files()
    
    # Path traversal protection
    result = await files_tool.run(action="read", filename="../../../etc/passwd")
    assert "error" in result
    assert "Unsafe path access" in result["error"]
    
    # Empty filename protection  
    result = await files_tool.run(action="read", filename="")
    assert "error" in result
    assert "Path cannot be empty" in result["error"]
