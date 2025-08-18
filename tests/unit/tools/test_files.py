"""File tools tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cogency.tools.files import FileList, FileRead, FileWrite


class TestFileRead:
    """FileRead tool tests."""

    def test_init(self):
        """FileRead initialization."""
        tool = FileRead()
        assert tool.name == "file_read"
        assert "read content" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """FileRead returns file content."""
        with TemporaryDirectory() as tmpdir:
            # Create test file in actual .sandbox
            sandbox = Path(tmpdir) / ".sandbox"
            sandbox.mkdir(parents=True)
            test_file = sandbox / "test.txt"
            test_file.write_text("Hello world\nLine 2")

            # Change to temp directory for test
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                tool = FileRead()
                result = await tool.execute("test.txt")

                assert result.success
                assert "Hello world" in result.unwrap()
                assert "Line 2" in result.unwrap()
                assert "2 lines" in result.unwrap()
            finally:
                os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_execute_empty_filename(self):
        """FileRead rejects empty filename."""
        tool = FileRead()
        result = await tool.execute("")

        assert result.failure
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self):
        """FileRead handles missing file."""
        tool = FileRead()
        result = await tool.execute("nonexistent.txt")

        assert result.failure
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_path_traversal(self):
        """FileRead blocks path traversal."""
        tool = FileRead()
        result = await tool.execute("../../../etc/passwd")

        assert result.failure
        assert "security violation" in result.error.lower()


class TestFileWrite:
    """FileWrite tool tests."""

    def test_init(self):
        """FileWrite initialization."""
        tool = FileWrite()
        assert tool.name == "file_write"
        assert "write content" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """FileWrite creates file with content."""
        with TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                tool = FileWrite()
                result = await tool.execute("test.txt", "Hello world\nLine 2")

                assert result.success
                assert "Wrote 'test.txt'" in result.unwrap()
                assert "2 lines" in result.unwrap()

                # Verify file was created
                created_file = Path(".sandbox/test.txt")
                assert created_file.exists()
                assert created_file.read_text() == "Hello world\nLine 2"
            finally:
                os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_execute_empty_filename(self):
        """FileWrite rejects empty filename."""
        tool = FileWrite()
        result = await tool.execute("", "content")

        assert result.failure
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_unsafe_content(self):
        """FileWrite blocks unsafe content."""
        tool = FileWrite()
        result = await tool.execute("test.txt", "rm -rf /")

        assert result.failure
        assert "unsafe patterns" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_path_traversal(self):
        """FileWrite blocks path traversal."""
        tool = FileWrite()
        result = await tool.execute("../../../evil.txt", "content")

        assert result.failure
        assert "security violation" in result.error.lower()


class TestFileList:
    """FileList tool tests."""

    def test_init(self):
        """FileList initialization."""
        tool = FileList()
        assert tool.name == "file_list"
        assert "list files" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_empty_directory(self):
        """FileList handles empty sandbox."""
        with TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                tool = FileList()
                result = await tool.execute()

                assert result.success
                assert "empty" in result.unwrap().lower()
            finally:
                os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_execute_with_files(self):
        """FileList shows directory contents."""
        with TemporaryDirectory() as tmpdir:
            # Create test files
            sandbox = Path(tmpdir) / ".sandbox"
            sandbox.mkdir(parents=True)
            (sandbox / "file1.txt").write_text("content1")
            (sandbox / "file2.txt").write_text("longer content")
            (sandbox / "subdir").mkdir()

            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                tool = FileList()
                result = await tool.execute()

                assert result.success
                assert "file1.txt" in result.unwrap()
                assert "file2.txt" in result.unwrap()
                assert "subdir/" in result.unwrap()
                assert "bytes" in result.unwrap()
            finally:
                os.chdir(old_cwd)

    @pytest.mark.asyncio
    async def test_execute_no_sandbox(self):
        """FileList handles missing sandbox directory."""
        with TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                tool = FileList()
                result = await tool.execute()

                assert result.success
                assert "empty" in result.unwrap().lower()
            finally:
                os.chdir(old_cwd)
