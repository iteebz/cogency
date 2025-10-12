from pathlib import Path

import pytest

from cogency.tools import Shell


@pytest.mark.asyncio
async def test_sandbox_mode_runs_in_sandbox_dir(tmp_path):
    tool = Shell()

    result = await tool.execute(command="pwd", sandbox_dir=str(tmp_path), access="sandbox")

    assert not result.error
    assert str(tmp_path) in result.content


@pytest.mark.asyncio
async def test_project_mode_runs_in_cwd():
    tool = Shell()

    result = await tool.execute(command="pwd", access="project")

    assert not result.error
    assert str(Path.cwd()) in result.content


@pytest.mark.asyncio
async def test_sandbox_dir_ignored_when_not_sandbox(tmp_path):
    tool = Shell()

    result = await tool.execute(command="pwd", sandbox_dir=str(tmp_path), access="project")

    assert not result.error
    assert str(Path.cwd()) in result.content
    assert str(tmp_path) not in result.content


@pytest.mark.asyncio
async def test_timeout_enforcement():
    tool = Shell()

    result = await tool.execute(command="/bin/sleep 5", timeout=1, access="sandbox")

    assert result.error
    assert "timed out" in result.outcome


@pytest.mark.asyncio
async def test_glob_expansion_in_project_mode(tmp_path, monkeypatch):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()

    monkeypatch.chdir(tmp_path)

    tool = Shell()

    result = await tool.execute(command="ls -d */", access="project")

    assert not result.error
    assert "alpha/" in result.content
    assert "beta/" in result.content


@pytest.mark.asyncio
async def test_cwd_absolute_path(tmp_path):
    tool = Shell()
    subdir = tmp_path / "custom"
    subdir.mkdir()

    result = await tool.execute(command="pwd", cwd=str(subdir), access="sandbox")

    assert not result.error
    assert str(subdir) in result.content


@pytest.mark.asyncio
async def test_cwd_relative_path_sandbox(tmp_path):
    tool = Shell()

    result = await tool.execute(
        command="pwd", cwd="subdir", sandbox_dir=str(tmp_path), access="sandbox"
    )

    assert not result.error
    assert str(tmp_path / "subdir") in result.content


@pytest.mark.asyncio
async def test_cwd_relative_path_project():
    tool = Shell()

    result = await tool.execute(command="pwd", cwd="tests", access="project")

    assert not result.error
    assert str(Path.cwd() / "tests") in result.content
