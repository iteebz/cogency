"""File tools tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cogency.tools.files import FileList, FileRead, FileWrite


def test_file_read_init():
    """FileRead initialization."""
    tool = FileRead()
    assert tool.name == "read"
    assert "read file content" in tool.description.lower()


@pytest.mark.asyncio
async def test_file_read_execute_success():
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
async def test_file_read_execute_empty_filename():
    """FileRead rejects empty filename."""
    tool = FileRead()
    result = await tool.execute("")

    assert result.failure
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_file_read_execute_file_not_found():
    """FileRead handles missing file."""
    tool = FileRead()
    result = await tool.execute("nonexistent.txt")

    assert result.failure
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_file_read_execute_path_traversal():
    """FileRead blocks path traversal."""
    tool = FileRead()
    result = await tool.execute("../../../etc/passwd")

    assert result.failure
    assert "security violation" in result.error.lower()


def test_file_write_init():
    """FileWrite initialization."""
    tool = FileWrite()
    assert tool.name == "write"
    assert "write content" in tool.description.lower()


@pytest.mark.asyncio
async def test_file_write_execute_success():
    """FileWrite creates file with content."""
    with TemporaryDirectory() as tmpdir:
        import os

        old_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            tool = FileWrite()
            result = await tool.execute("test.txt", "Hello world\nLine 2")

            assert result.success
            assert "Created 'test.txt'" in result.unwrap()
            assert "2 lines" in result.unwrap()

            # Verify file was created
            created_file = Path(".sandbox/test.txt")
            assert created_file.exists()
            assert created_file.read_text() == "Hello world\nLine 2"
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_file_write_execute_empty_filename():
    """FileWrite rejects empty filename."""
    tool = FileWrite()
    result = await tool.execute("", "content")

    assert result.failure
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_file_write_execute_unsafe_content():
    """FileWrite blocks unsafe content."""
    tool = FileWrite()
    result = await tool.execute("test.txt", "rm -rf /")

    assert result.failure
    assert "unsafe patterns" in result.error.lower()


@pytest.mark.asyncio
async def test_file_write_execute_path_traversal():
    """FileWrite blocks path traversal."""
    tool = FileWrite()
    result = await tool.execute("../../../evil.txt", "content")

    assert result.failure
    assert "security violation" in result.error.lower()


def test_file_list_init():
    """FileList initialization."""
    tool = FileList()
    assert tool.name == "list"
    assert "hierarchical structure" in tool.description.lower()


@pytest.mark.asyncio
async def test_file_list_execute_empty_directory():
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
async def test_file_list_execute_with_files():
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
            # Check for files in new hierarchical format
            result_text = result.unwrap()
            assert "file1.txt" in result_text
            assert "file2.txt" in result_text
            # New format shows summary
            assert "Total:" in result_text
            # New hierarchical format includes summary
            result_text = result.unwrap()
            assert len(result_text) > 0
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_file_list_execute_no_sandbox():
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
