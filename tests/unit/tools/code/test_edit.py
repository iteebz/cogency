import pytest

from cogency.tools import Edit

# --- Success Cases ---


@pytest.mark.asyncio
async def test_replaces_content_simple(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    target.write_text("previous content")

    result = await tool.execute(
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
async def test_reports_correct_diff_counts(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    initial_content = "line 1\nline 2 old\nline 3\n"
    target.write_text(initial_content)

    result = await tool.execute(
        file=str(target.name),
        old="line 2 old",
        new="line 2 new",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert not result.error, f"Tool error: {result.outcome}"
    assert "Edited test.txt (+1/-1)" in result.outcome
    assert target.read_text() == "line 1\nline 2 new\nline 3\n"


@pytest.mark.asyncio
async def test_no_replacement_when_old_equals_new(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    initial_content = "line 1\nline 2\nline 3\n"
    target.write_text(initial_content)

    result = await tool.execute(
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
async def test_fails_when_old_string_not_found(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    initial_content = "line 1\nline 2\nline 3\n"
    target.write_text(initial_content)

    result = await tool.execute(
        file=str(target.name),
        old="non-existent line",
        new="some new text",
        sandbox_dir=str(tmp_path),
        access="sandbox",
    )

    assert result.error
    assert "Text not found: 'non-existent line'" in result.outcome
    assert target.read_text() == initial_content


@pytest.mark.asyncio
async def test_fails_when_old_blank_on_empty_file(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    target.write_text("")

    result = await tool.execute(
        file=str(target.name), old="", new="content", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is True
    assert "Text to replace cannot be empty" in result.outcome
    assert target.read_text() == ""


@pytest.mark.asyncio
async def test_fails_when_old_blank_on_existing_file(tmp_path):
    tool = Edit()
    target = tmp_path / "test.txt"
    target.write_text("previous")

    result = await tool.execute(
        file=str(target.name), old="", new="next", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is True
    assert "Text to replace cannot be empty" in result.outcome
    assert target.read_text() == "previous"
