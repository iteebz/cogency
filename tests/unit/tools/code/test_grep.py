import shlex

import pytest

from cogency.tools import Grep


@pytest.mark.asyncio
async def test_grep_reports_zero_matches(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "app.py").write_text("print('hello world')\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    tool = Grep()
    result = await tool.execute(content="missing", path=".", access="project")

    assert result.outcome == "Found 0 matches"
    assert "Search root: ." in result.content
    assert "Content: missing" in result.content


@pytest.mark.asyncio
async def test_grep_returns_relative_paths_with_counts(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    pkg_dir = workspace / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "alpha.py").write_text("def foo():\n    return 'alpha'\n", encoding="utf-8")
    (pkg_dir / "beta.py").write_text("def bar():\n    return 'alpha'\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    tool = Grep()
    result = await tool.execute(content="alpha", path="pkg", access="project")

    assert result.outcome == "Found 2 matches"
    lines = [line for line in result.content.splitlines() if line and ":" in line]
    assert any(line.startswith("pkg/alpha.py:2:") for line in lines)
    assert any(line.startswith("pkg/beta.py:2:") for line in lines)

    second = await tool.execute(pattern="alpha.py", path="pkg", access="project")
    assert second.outcome == "Found 1 match"
    entries = [
        line
        for line in second.content.splitlines()
        if line.startswith("pkg/") and line.endswith(".py")
    ]
    assert entries == ["pkg/alpha.py"]
    # Ensure sanitised output preserves shell-friendly quoting if used downstream
    shlex.split(entries[0])
