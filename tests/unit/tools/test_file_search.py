import pytest

from cogency.tools.file.search import FileSearch


@pytest.mark.asyncio
async def test_rejects_wildcard_without_content(tmp_path):
    tool = FileSearch()

    result = await tool.execute(pattern="*", sandbox_dir=str(tmp_path), access="sandbox")

    assert result.error is True
    assert "too broad" in result.outcome


@pytest.mark.asyncio
async def test_truncates_large_results(tmp_path):
    tool = FileSearch()

    for i in range(150):
        (tmp_path / f"file_{i}.txt").write_text("test")

    result = await tool.execute(pattern="*.txt", sandbox_dir=str(tmp_path), access="sandbox")

    assert "Found 150 matches" in result.outcome
    assert "Truncated: showing 100 of 150" in result.content
    assert result.content.count("\n") < 110


@pytest.mark.asyncio
async def test_allows_wildcard_with_content(tmp_path):
    tool = FileSearch()

    (tmp_path / "match.txt").write_text("findme")
    (tmp_path / "nomatch.txt").write_text("other")

    result = await tool.execute(
        pattern="*", content="findme", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert not result.error
    assert "match.txt" in result.content
    assert "nomatch.txt" not in result.content
