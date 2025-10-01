import pytest

from cogency.tools.file.write import FileWrite


@pytest.mark.asyncio
async def test_creates_parent_dirs(tmp_path):
    tool = FileWrite()

    result = await tool.execute(
        file="a/b/c/test.txt", content="data", base_dir=str(tmp_path), access="project"
    )

    assert "Created" in result.outcome
    nested = tmp_path / "a" / "b" / "c" / "test.txt"
    assert nested.exists()
    assert nested.read_text() == "data"
