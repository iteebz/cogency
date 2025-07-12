"""Tests for FileManagerTool."""

import shutil
import tempfile
from pathlib import Path

import pytest

from cogency.tools.file_manager import FileManagerTool


class TestFileManagerTool:
    """Test suite for FileManagerTool."""

    def setup_method(self):
        """Setup test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManagerTool(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_file_manager_initialization(self):
        """Test file manager initialization."""
        assert self.file_manager.name == "file_manager"
        assert "manage files and directories" in self.file_manager.description.lower()
        assert self.file_manager.base_dir == Path(self.temp_dir).resolve()

    @pytest.mark.asyncio
    async def test_create_file_success(self):
        """Test successful file creation."""
        result = await self.file_manager.run(
            action="create_file", filename="test.txt", content="Hello, World!"
        )

        assert result["success"] is True
        assert result["path"] == "test.txt"
        assert result["size"] == 13
        assert "Created file" in result["message"]

        # Verify file exists and has correct content
        file_path = Path(self.temp_dir) / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_create_file_with_subdirectory(self):
        """Test file creation in subdirectory."""
        result = await self.file_manager.run(
            action="create_file", filename="subdir/test.txt", content="Nested file"
        )

        assert result["success"] is True
        assert result["path"] == "subdir/test.txt"

        # Verify subdirectory and file exist
        file_path = Path(self.temp_dir) / "subdir" / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Nested file"

    @pytest.mark.asyncio
    async def test_create_file_empty_filename(self):
        """Test file creation with empty filename."""
        result = await self.file_manager.run(
            action="create_file", filename="", content="Some content"
        )

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"
        assert "filename" in result["details"]["empty_params"]

    @pytest.mark.asyncio
    async def test_read_file_success(self):
        """Test successful file reading."""
        # Create a file first
        test_content = "This is test content"
        await self.file_manager.run(
            action="create_file", filename="read_test.txt", content=test_content
        )

        # Read the file
        result = await self.file_manager.run(action="read_file", filename="read_test.txt")

        assert result["success"] is True
        assert result["content"] == test_content
        assert result["path"] == "read_test.txt"
        assert result["size"] == len(test_content)

    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test reading non-existent file."""
        result = await self.file_manager.run(action="read_file", filename="nonexistent.txt")

        assert "error" in result
        assert result["error_code"] == "FILE_NOT_FOUND"
        assert "nonexistent.txt" in result["details"]["filename"]

    @pytest.mark.asyncio
    async def test_read_file_empty_filename(self):
        """Test reading with empty filename."""
        result = await self.file_manager.run(action="read_file", filename="")

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"

    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self):
        """Test listing files in empty directory."""
        result = await self.file_manager.run(action="list_files", filename=".")

        assert result["success"] is True
        assert result["items"] == []
        assert result["total"] == 0
        assert result["directory"] == "."

    @pytest.mark.asyncio
    async def test_list_files_with_content(self):
        """Test listing files with content."""
        # Create some test files and directories
        await self.file_manager.run(action="create_file", filename="file1.txt", content="content1")
        await self.file_manager.run(action="create_file", filename="file2.txt", content="content2")
        await self.file_manager.run(
            action="create_file", filename="subdir/nested.txt", content="nested"
        )

        result = await self.file_manager.run(action="list_files", filename=".")

        assert result["success"] is True
        assert result["total"] == 3  # file1.txt, file2.txt, subdir

        # Check that we have the expected items
        item_names = [item["name"] for item in result["items"]]
        assert "file1.txt" in item_names
        assert "file2.txt" in item_names
        assert "subdir" in item_names

        # Check item details
        for item in result["items"]:
            if item["name"] == "file1.txt":
                assert item["type"] == "file"
                assert item["size"] == 8  # len("content1")
            elif item["name"] == "subdir":
                assert item["type"] == "directory"
                assert item["size"] is None

    @pytest.mark.asyncio
    async def test_list_files_subdirectory(self):
        """Test listing files in subdirectory."""
        await self.file_manager.run(
            action="create_file", filename="subdir/nested.txt", content="nested"
        )

        result = await self.file_manager.run(action="list_files", filename="subdir")

        assert result["success"] is True
        assert result["total"] == 1
        assert result["items"][0]["name"] == "nested.txt"
        assert result["items"][0]["type"] == "file"

    @pytest.mark.asyncio
    async def test_list_files_nonexistent_directory(self):
        """Test listing files in non-existent directory."""
        result = await self.file_manager.run(action="list_files", filename="nonexistent")

        assert "error" in result
        assert result["error_code"] == "DIRECTORY_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test successful file deletion."""
        # Create a file first
        await self.file_manager.run(action="create_file", filename="delete_me.txt", content="bye")

        # Delete the file
        result = await self.file_manager.run(action="delete_file", filename="delete_me.txt")

        assert result["success"] is True
        assert result["path"] == "delete_me.txt"
        assert "Deleted file" in result["message"]

        # Verify file no longer exists
        file_path = Path(self.temp_dir) / "delete_me.txt"
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self):
        """Test deleting non-existent file."""
        result = await self.file_manager.run(action="delete_file", filename="nonexistent.txt")

        assert "error" in result
        assert result["error_code"] == "FILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_file_empty_filename(self):
        """Test deleting with empty filename."""
        result = await self.file_manager.run(action="delete_file", filename="")

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action."""
        result = await self.file_manager.run(action="invalid_action", filename="test.txt")

        assert "error" in result
        assert result["error_code"] == "INVALID_ACTION"
        assert "valid_actions" in result["details"]

    @pytest.mark.asyncio
    async def test_safe_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented."""
        # Try to access parent directory
        result = await self.file_manager.run(
            action="create_file", filename="../outside.txt", content="malicious"
        )

        assert "error" in result
        assert result["error_code"] == "PATH_TRAVERSAL_ATTEMPT"

        # Try absolute path outside base dir
        result = await self.file_manager.run(
            action="create_file", filename="/etc/passwd", content="malicious"
        )

        assert "error" in result
        assert result["error_code"] == "PATH_TRAVERSAL_ATTEMPT"

    @pytest.mark.asyncio
    async def test_read_directory_as_file(self):
        """Test reading a directory as if it were a file."""
        # Create a subdirectory
        await self.file_manager.run(
            action="create_file", filename="subdir/test.txt", content="test"
        )

        # Try to read the directory
        result = await self.file_manager.run(action="read_file", filename="subdir")

        assert "error" in result
        assert result["error_code"] == "NOT_A_FILE"
        assert result["details"]["path_type"] == "directory"

    @pytest.mark.asyncio
    async def test_list_file_as_directory(self):
        """Test listing a file as if it were a directory."""
        # Create a file
        await self.file_manager.run(action="create_file", filename="test.txt", content="test")

        # Try to list the file
        result = await self.file_manager.run(action="list_files", filename="test.txt")

        assert "error" in result
        assert result["error_code"] == "NOT_A_DIRECTORY"
        assert result["details"]["path_type"] == "file"

    @pytest.mark.asyncio
    async def test_delete_directory_as_file(self):
        """Test deleting a directory as if it were a file."""
        # Create a subdirectory
        await self.file_manager.run(
            action="create_file", filename="subdir/test.txt", content="test"
        )

        # Try to delete the directory
        result = await self.file_manager.run(action="delete_file", filename="subdir")

        assert "error" in result
        assert result["error_code"] == "NOT_A_FILE"

    @pytest.mark.asyncio
    async def test_get_schema(self):
        """Test get_schema method."""
        schema = self.file_manager.get_schema()

        assert "file_manager" in schema
        assert "action=" in schema
        assert "filename=" in schema
        assert "content=" in schema

    @pytest.mark.asyncio
    async def test_get_usage_examples(self):
        """Test get_usage_examples method."""
        examples = self.file_manager.get_usage_examples()

        assert len(examples) > 0
        assert all("file_manager(" in example for example in examples)
        assert any("create_file" in example for example in examples)
        assert any("read_file" in example for example in examples)
        assert any("list_files" in example for example in examples)
        assert any("delete_file" in example for example in examples)

    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """Test handling of unicode content."""
        unicode_content = "Hello 世界! 🌍"

        result = await self.file_manager.run(
            action="create_file", filename="unicode.txt", content=unicode_content
        )

        assert result["success"] is True

        # Read back and verify
        result = await self.file_manager.run(action="read_file", filename="unicode.txt")
        assert result["success"] is True
        assert result["content"] == unicode_content
