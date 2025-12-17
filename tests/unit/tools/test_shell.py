from pathlib import Path

import pytest

from cogency.tools import Shell


@pytest.mark.asyncio
async def test_runs_in_sandbox_dir(tmp_path):
    result = await Shell.execute(command="pwd", sandbox_dir=str(tmp_path), access="sandbox")

    assert not result.error
    assert result.content is not None
    assert str(tmp_path) in result.content


@pytest.mark.asyncio
async def test_runs_in_cwd():
    result = await Shell.execute(command="pwd", access="project")

    assert not result.error
    assert result.content is not None
    assert str(Path.cwd()) in result.content


@pytest.mark.asyncio
async def test_sandbox_ignored_when_not_sandbox(tmp_path):
    result = await Shell.execute(command="pwd", sandbox_dir=str(tmp_path), access="project")

    assert not result.error
    assert result.content is not None
    assert str(Path.cwd()) in result.content
    assert str(tmp_path) not in result.content


@pytest.mark.asyncio
async def test_timeout_enforcement():
    result = await Shell.execute(command="/bin/sleep 5", timeout=1, access="sandbox")

    assert result.error
    assert result.outcome is not None
    assert "timed out" in result.outcome


@pytest.mark.asyncio
async def test_lists_directories_in_project(tmp_path, monkeypatch):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()

    monkeypatch.chdir(tmp_path)

    result = await Shell.execute(command="ls", access="project")

    assert not result.error
    assert result.content is not None
    assert "alpha" in result.content
    assert "beta" in result.content


@pytest.mark.asyncio
async def test_cwd_absolute(tmp_path):
    subdir = tmp_path / "custom"
    subdir.mkdir()

    result = await Shell.execute(command="pwd", cwd=str(subdir), access="sandbox")

    assert not result.error
    assert result.content is not None
    assert str(subdir) in result.content


@pytest.mark.asyncio
async def test_cwd_relative_sandbox(tmp_path):
    result = await Shell.execute(
        command="pwd", cwd="subdir", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert not result.error
    assert result.content is not None
    assert str(tmp_path / "subdir") in result.content


@pytest.mark.asyncio
async def test_cwd_relative_project():
    result = await Shell.execute(command="pwd", cwd="tests", access="project")

    assert not result.error
    assert result.content is not None
    assert str(Path.cwd() / "tests") in result.content
