from pathlib import Path

import pytest

from cogency.tools import Ls


@pytest.mark.asyncio
async def test_tree_with_pattern_matching(tmp_path: Path):
    """The tree tool should correctly filter files by glob pattern."""
    tool = Ls()
    (tmp_path / "file1.py").write_text("content")
    (tmp_path / "file2.txt").write_text("content")
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    (sub_dir / "file3.py").write_text("content")

    result = await tool.execute(
        path=".", pattern="*.py", access="sandbox", sandbox_dir=str(tmp_path)
    )

    assert not result.error
    assert "files" in result.outcome.lower()
    assert "dirs" in result.outcome.lower()
    assert "file1.py" in result.content
    assert "file2.txt" not in result.content
    assert "sub/" in result.content
    assert "file3.py" in result.content


@pytest.mark.asyncio
async def test_tree_with_multiple_asterisk_pattern(tmp_path: Path):
    """The tree tool should correctly filter files by glob pattern with multiple asterisks."""
    tool = Ls()
    (tmp_path / "file1.py").write_text("content")

    result = await tool.execute(
        path=".", pattern="f*1*.py", access="sandbox", sandbox_dir=str(tmp_path)
    )

    assert not result.error
    assert result.outcome.startswith("Listed 1")
    assert "file1.py" in result.content
