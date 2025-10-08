import pytest

from cogency.tools import Edit


@pytest.mark.asyncio
async def test_overwrites_empty_file_with_blank_old(tmp_path):
    tool = Edit()
    target = tmp_path / "fib.txt"
    target.write_text("")

    result = await tool.execute(
        file="fib.txt", old="", new="267914296", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is False
    assert "Edited fib.txt" in result.outcome
    assert target.read_text() == "267914296"


@pytest.mark.asyncio
async def test_overwrites_existing_file_when_old_blank(tmp_path):
    tool = Edit()
    target = tmp_path / "fib.txt"
    target.write_text("previous")

    result = await tool.execute(
        file="fib.txt", old="", new="next", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is False
    assert result.outcome.endswith("(+1/-1)")
    assert target.read_text() == "next"
