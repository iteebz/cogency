from pathlib import Path

import pytest

from cogency.tools import List


@pytest.fixture
def setup_test_dir(tmp_path):
    # Create a directory structure for testing
    (tmp_path / "regular_dir").mkdir()
    (tmp_path / "another_dir").mkdir()
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / ".hidden_file").write_text("hidden")

    # Ignored directories
    (tmp_path / "node_modules").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".ruff_cache").mkdir()
    (tmp_path / ".mypy_cache").mkdir()
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".idea").mkdir()

    # Files within ignored directories (should not appear)
    (tmp_path / "node_modules" / "package.json").write_text("{}")
    (tmp_path / ".venv" / "pyvenv.cfg").write_text("")

    return tmp_path


# --- Basic Listing & Ignore Logic ---


@pytest.mark.asyncio
async def test_hides_ignored_directories(setup_test_dir):
    result = await List.execute(path=str(setup_test_dir), access="system")

    assert not result.error
    content = result.content
    assert content is not None

    # Assert that ignored directories are NOT in the output
    assert "node_modules/" not in content
    assert ".venv/" not in content
    assert "__pycache__/" not in content
    assert "dist/" not in content
    assert ".git/" not in content
    assert ".pytest_cache/" not in content
    assert ".ruff_cache/" not in content
    assert ".mypy_cache/" not in content
    assert ".vscode/" not in content
    assert ".idea/" not in content

    # Assert that hidden files (starting with .) are NOT in the output
    assert ".hidden_file" not in content

    # Assert that regular directories and files ARE in the output
    assert "regular_dir/" in content
    assert "another_dir/" in content
    assert "file.txt" in content


@pytest.mark.asyncio
async def test_hides_ignored_directories_recursive(setup_test_dir):
    # Create a nested ignored directory
    (setup_test_dir / "regular_dir" / "node_modules").mkdir()
    (setup_test_dir / "regular_dir" / "node_modules" / "nested_package.json").write_text("{}")

    result = await List.execute(path=str(setup_test_dir), access="system")

    assert not result.error
    content = result.content
    assert content is not None

    # Assert that the nested ignored directory is NOT in the output
    assert "node_modules/" not in content
    assert "nested_package.json" not in content

    # Assert that the parent directory is still listed
    assert "regular_dir/" in content


@pytest.mark.asyncio
async def test_empty_directory_with_ignored_dirs(tmp_path):
    # Create an empty directory, then add an ignored dir inside
    (tmp_path / "empty_but_ignored").mkdir()
    (tmp_path / "empty_but_ignored" / "node_modules").mkdir()

    result = await List.execute(path=str(tmp_path / "empty_but_ignored"), access="system")

    assert not result.error
    assert result.content is not None
    assert result.content is not None
    assert "No files found" in result.content or not result.content.strip()
    assert result.content is not None
    assert "node_modules/" not in result.content


@pytest.mark.asyncio
async def test_only_ignored_dirs_in_root(tmp_path):
    # Create a directory containing only ignored directories
    (tmp_path / "only_ignored").mkdir()
    (tmp_path / "only_ignored" / "node_modules").mkdir()
    (tmp_path / "only_ignored" / ".venv").mkdir()

    result = await List.execute(path=str(tmp_path / "only_ignored"), access="system")

    assert not result.error
    assert result.content is not None
    assert result.content is not None
    assert "No files found" in result.content or not result.content.strip()
    assert result.content is not None
    assert "node_modules/" not in result.content
    assert result.content is not None
    assert ".venv/" not in result.content


# --- Pattern Matching ---


@pytest.mark.asyncio
async def test_simple_pattern_matching(tmp_path: Path):
    """The ls tool should correctly filter files by glob pattern."""
    (tmp_path / "file1.py").write_text("content")
    (tmp_path / "file2.txt").write_text("content")
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    (sub_dir / "file3.py").write_text("content")

    result = await List.execute(
        path=".", pattern="*.py", access="sandbox", sandbox_dir=str(tmp_path)
    )

    assert not result.error
    assert "files" in result.outcome.lower()
    assert "dirs" in result.outcome.lower()
    assert result.content is not None
    assert "file1.py" in result.content
    assert result.content is not None
    assert "file2.txt" not in result.content
    assert result.content is not None
    assert "sub/" in result.content
    assert result.content is not None
    assert "file3.py" in result.content


@pytest.mark.asyncio
async def test_complex_pattern_matching(tmp_path: Path):
    """The ls tool should correctly filter files by glob pattern with multiple asterisks."""
    (tmp_path / "file1.py").write_text("content")

    result = await List.execute(
        path=".", pattern="f*1*.py", access="sandbox", sandbox_dir=str(tmp_path)
    )

    assert not result.error
    assert result.outcome.startswith("Listed 1")
    assert result.content is not None
    assert "file1.py" in result.content


@pytest.mark.asyncio
async def test_pattern_does_not_override_ignored_dirs(setup_test_dir):
    # Try to list a file within an ignored directory using a pattern
    (setup_test_dir / "node_modules" / "important.js").write_text("console.log('important');")

    result = await List.execute(path=str(setup_test_dir), pattern="*.js", access="system")

    assert not result.error
    content = result.content
    assert content is not None

    # Assert that the file within the ignored directory is NOT in the output
    assert "important.js" not in content
