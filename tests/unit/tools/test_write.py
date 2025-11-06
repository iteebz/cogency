import pytest

from cogency.tools import Write

# --- Success Cases (Creation) ---


@pytest.mark.asyncio
async def test_creates_new_file(tmp_path):
    target = tmp_path / "new_file.txt"
    content = "Hello, world!"

    result = await Write.execute(
        file=str(target.name), content=content, sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert result.error is False
    assert "Wrote new_file.txt" in result.outcome
    assert target.read_text() == content


@pytest.mark.asyncio
async def test_creates_parent_directories(tmp_path):
    nested_path = "a/b/c/test.txt"
    content = "data"

    result = await Write.execute(
        file=nested_path, content=content, sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert "Wrote" in result.outcome
    target = tmp_path / nested_path
    assert target.exists()
    assert target.read_text() == content


# --- Success Cases (Overwrite) ---


@pytest.mark.asyncio
async def test_succeeds_on_overwrite(tmp_path):
    target = tmp_path / "existing_file.txt"
    target.write_text("initial content")
    content = "new content"

    result = await Write.execute(
        file=str(target.name),
        content=content,
        sandbox_dir=str(tmp_path),
        access="sandbox",
        overwrite=True,
    )

    assert result.error is False
    assert "Wrote existing_file.txt" in result.outcome
    assert target.read_text() == content


# --- Error Cases ---


@pytest.mark.asyncio
async def test_fails_without_overwrite(tmp_path):
    target = tmp_path / "existing_file.txt"
    target.write_text("initial content")
    content = "new content"

    result = await Write.execute(
        file=str(target.name),
        content=content,
        sandbox_dir=str(tmp_path),
        access="sandbox",
        overwrite=False,
    )

    assert result.error is True
    assert "already exists" in result.outcome
    assert target.read_text() == "initial content"
