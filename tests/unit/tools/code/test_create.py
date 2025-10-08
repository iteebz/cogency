import pytest

from cogency.tools import Write


@pytest.mark.asyncio
async def test_creates_parent_dirs(tmp_path):
    tool = Write()

    result = await tool.execute(
        file="a/b/c/test.txt", content="data", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert "Wrote" in result.outcome
    nested = tmp_path / "a" / "b" / "c" / "test.txt"
    assert nested.exists()
    assert nested.read_text() == "data"


@pytest.mark.asyncio
async def test_rejects_existing_file(tmp_path):
    tool = Write()
    test_file = tmp_path / "existing.txt"
    test_file.write_text("original")

    result = await tool.execute(
        file="existing.txt", content="new", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is True
    assert "already exists" in result.outcome
    assert "edit" in result.outcome
    assert test_file.read_text() == "original"
