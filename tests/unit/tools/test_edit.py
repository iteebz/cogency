import pytest

from cogency.tools import Edit

# --- Success Cases ---


@pytest.mark.asyncio
async def test_replace(tmp_path):
    target = tmp_path / "test.txt"
    target.write_text("previous content")

    result = await Edit.execute(
        file=str(target.name),
        old="previous",
        new="next",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert result.error is False
    assert "Edited test.txt" in result.outcome
    assert target.read_text() == "next content"


@pytest.mark.asyncio
async def test_diff_report(tmp_path):
    target = tmp_path / "test.txt"
    initial_content = """line 1
line 2 old
line 3
"""
    target.write_text(initial_content)

    result = await Edit.execute(
        file=str(target.name),
        old="line 2 old",
        new="line 2 new",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert not result.error, f"Tool error: {result.outcome}"
    assert "Edited test.txt (+1/-1)" in result.outcome
    assert (
        target.read_text()
        == """line 1
line 2 new
line 3
"""
    )

    # Verify the diff content contract
    assert result.content is not None
    assert "--- " in result.content
    assert "+++ " in result.content
    assert "-line 2 old" in result.content
    assert "+line 2 new" in result.content


@pytest.mark.asyncio
async def test_no_op_when_same(tmp_path):
    target = tmp_path / "test.txt"
    initial_content = """line 1
line 2
line 3
"""
    target.write_text(initial_content)

    result = await Edit.execute(
        file=str(target.name),
        old="line 2",
        new="line 2",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert not result.error, f"Tool error: {result.outcome}"
    assert "Edited test.txt (+0/-0)" in result.outcome
    assert target.read_text() == initial_content


# --- Error Cases ---


@pytest.mark.asyncio
async def test_fail_when_not_found(tmp_path):
    target = tmp_path / "test.txt"
    initial_content = """line 1
line 2
line 3
"""
    target.write_text(initial_content)

    result = await Edit.execute(
        file=str(target.name),
        old="non-existent line",
        new="some new text",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert result.error
    assert "Text not found" in result.outcome
    assert target.read_text() == initial_content


@pytest.mark.asyncio
async def test_fail_blank_on_empty(tmp_path):
    target = tmp_path / "test.txt"
    target.write_text("")

    result = await Edit.execute(
        file=str(target.name), old="", new="content", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is True
    assert "Text to replace cannot be empty" in result.outcome
    assert target.read_text() == ""


@pytest.mark.asyncio
async def test_fail_blank_on_existing(tmp_path):
    target = tmp_path / "test.txt"
    target.write_text("previous")

    result = await Edit.execute(
        file=str(target.name), old="", new="next", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is True
    assert "Text to replace cannot be empty" in result.outcome
    assert target.read_text() == "previous"
