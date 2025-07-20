"""Test File tool business logic."""
import pytest
import tempfile
from pathlib import Path

from cogency.tools.file import File


class TestFile:
    """Test File tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """File tool implements required interface."""
        file_tool = File()
        
        # Required attributes
        assert file_tool.name == "file"
        assert file_tool.description
        assert hasattr(file_tool, 'run')
        
        # Schema and examples
        schema = file_tool.get_schema()
        examples = file_tool.get_usage_examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_create_and_read_file(self):
        """File tool can create and read files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_tool = File(base_dir=temp_dir)
            
            # Create file
            result = await file_tool.run(action="create_file", filename="test.txt", content="hello world")
            assert "result" in result
            assert "Created file" in result["result"]
            
            # Read file
            result = await file_tool.run(action="read_file", filename="test.txt")
            assert "content" in result
            assert result["content"] == "hello world"
    
    @pytest.mark.asyncio
    async def test_list_files(self):
        """File tool can list files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_tool = File(base_dir=temp_dir)
            
            # Create a test file
            await file_tool.run(action="create_file", filename="test.txt", content="test")
            
            # List files
            result = await file_tool.run(action="list_files")
            assert "items" in result
            assert len(result["items"]) >= 1
            assert any(item["name"] == "test.txt" for item in result["items"])
    
    @pytest.mark.asyncio
    async def test_unsafe_path_access(self):
        """File tool blocks unsafe path access."""
        file_tool = File()
        
        # Try to access parent directory
        result = await file_tool.run(action="read_file", filename="../../../etc/passwd")
        assert "error" in result
        assert "Unsafe path access" in result["error"]
    
    @pytest.mark.asyncio
    async def test_empty_filename(self):
        """File tool handles empty filename."""
        file_tool = File()
        
        result = await file_tool.run(action="read_file", filename="")
        assert "error" in result
        assert "Path cannot be empty" in result["error"]