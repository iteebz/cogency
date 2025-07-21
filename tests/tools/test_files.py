"""Test File tool business logic."""
import pytest
import tempfile
from pathlib import Path

from cogency.tools.files import Files


class TestFiles:
    """Test Files tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Files tool implements required interface."""
        files_tool = Files()
        
        # Required attributes
        assert files_tool.name == "files"
        assert files_tool.description
        assert hasattr(files_tool, 'run')
        
        # Schema and examples
        schema = files_tool.schema()
        examples = files_tool.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_create_and_read_file(self):
        """Files tool can create and read files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create file
            result = await files_tool.run(action="create", filename="test.txt", content="hello world")
            assert "result" in result
            assert "Created file" in result["result"]
            
            # Read file
            result = await files_tool.run(action="read", filename="test.txt")
            assert "content" in result
            assert result["content"] == "hello world"
    
    @pytest.mark.asyncio
    async def test_list_files(self):
        """Files tool can list files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create a test file
            await files_tool.run(action="create", filename="test.txt", content="test")
            
            # List files
            result = await files_tool.run(action="list")
            assert "items" in result
            assert len(result["items"]) >= 1
            assert any(item["name"] == "test.txt" for item in result["items"])
    
    @pytest.mark.asyncio
    async def test_edit_single_line(self):
        """Files tool can edit single lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create file with multiple lines
            content = "line 1\nline 2\nline 3"
            await files_tool.run(action="create", filename="test.txt", content=content)
            
            # Edit line 2
            result = await files_tool.run(action="edit", filename="test.txt", line=2, content="EDITED LINE 2")
            assert "result" in result
            assert "Edited line 2" in result["result"]
            
            # Verify edit
            result = await files_tool.run(action="read", filename="test.txt")
            expected = "line 1\nEDITED LINE 2\nline 3"
            assert result["content"] == expected
    
    @pytest.mark.asyncio
    async def test_edit_line_range(self):
        """Files tool can edit line ranges."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create file with multiple lines
            content = "line 1\nline 2\nline 3\nline 4\nline 5"
            await files_tool.run(action="create", filename="test.txt", content=content)
            
            # Edit lines 2-4
            result = await files_tool.run(action="edit", filename="test.txt", start=2, end=4, content="NEW LINE A\nNEW LINE B")
            assert "result" in result
            assert "Edited lines 2-4" in result["result"]
            
            # Verify edit
            result = await files_tool.run(action="read", filename="test.txt")
            expected = "line 1\nNEW LINE A\nNEW LINE B\nline 5"
            assert result["content"] == expected
    
    @pytest.mark.asyncio
    async def test_edit_full_file(self):
        """Files tool can replace entire file content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create file
            await files_tool.run(action="create", filename="test.txt", content="old content")
            
            # Replace entire file
            result = await files_tool.run(action="edit", filename="test.txt", content="completely new content\nmultiple lines")
            assert "result" in result
            assert "Replaced entire file" in result["result"]
            
            # Verify edit
            result = await files_tool.run(action="read", filename="test.txt")
            assert result["content"] == "completely new content\nmultiple lines"
    
    @pytest.mark.asyncio
    async def test_edit_line_out_of_range(self):
        """Files tool handles line out of range errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create small file
            await files_tool.run(action="create", filename="test.txt", content="line 1\nline 2")
            
            # Try to edit non-existent line
            result = await files_tool.run(action="edit", filename="test.txt", line=5, content="won't work")
            assert "error" in result
            assert "out of range" in result["error"]
    
    @pytest.mark.asyncio
    async def test_edit_invalid_range(self):
        """Files tool handles invalid range errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Create small file
            await files_tool.run(action="create", filename="test.txt", content="line 1\nline 2")
            
            # Try invalid range
            result = await files_tool.run(action="edit", filename="test.txt", start=3, end=5, content="won't work")
            assert "error" in result
            assert "Invalid range" in result["error"]
    
    @pytest.mark.asyncio
    async def test_edit_nonexistent_file(self):
        """Files tool handles editing non-existent files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files_tool = Files(base_dir=temp_dir)
            
            # Try to edit non-existent file
            result = await files_tool.run(action="edit", filename="nonexistent.txt", content="won't work")
            assert "error" in result
            assert "File not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unsafe_path_access(self):
        """Files tool blocks unsafe path access."""
        files_tool = Files()
        
        # Try to access parent directory
        result = await files_tool.run(action="read", filename="../../../etc/passwd")
        assert "error" in result
        assert "Unsafe path access" in result["error"]
    
    @pytest.mark.asyncio
    async def test_empty_filename(self):
        """Files tool handles empty filename."""
        files_tool = Files()
        
        result = await files_tool.run(action="read", filename="")
        assert "error" in result
        assert "Path cannot be empty" in result["error"]
