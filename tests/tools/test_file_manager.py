"""File manager tool unit tests."""
import pytest
import tempfile
import os
from pathlib import Path
from cogency.tools.file_manager import FileManagerTool


class TestFileManagerTool:
    """Test file manager tool functionality."""
    
    @pytest.mark.asyncio
    async def test_create_and_read_file(self):
        """Test creating and reading a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManagerTool(base_dir=tmpdir)
            file_path = os.path.join(tmpdir, "test.txt")
            
            # Create file
            create_result = await file_manager.run("create_file", filename=file_path, content="Hello World")
            assert "result" in create_result
            assert "Created file" in create_result["result"]
            
            # Read file
            read_result = await file_manager.run("read_file", filename=file_path)
            assert read_result["content"] == "Hello World"
    
    @pytest.mark.asyncio
    async def test_list_directory(self):
        """Test listing directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManagerTool(base_dir=tmpdir)
            
            # Create test files
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).write_text("test content")
            
            # List directory
            result = await file_manager.run("list_files", filename=tmpdir)
            assert "items" in result
            assert any(item["name"] == "test.txt" for item in result["items"])
    
    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManagerTool(base_dir=tmpdir)
            file_path = os.path.join(tmpdir, "test.txt")
            
            # Create file
            Path(file_path).write_text("test content")
            
            # Delete file
            delete_result = await file_manager.run("delete_file", filename=file_path)
            assert "result" in delete_result
            assert "Deleted file" in delete_result["result"]
            
            # Verify deleted
            assert not os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManagerTool(base_dir=tmpdir)
            result = await file_manager.run("invalid_action", "filename")
            assert "error" in result
            assert "Unknown action" in result["error"]