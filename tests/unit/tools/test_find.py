import shlex

import pytest

from cogency.tools import find


@pytest.mark.asyncio
async def test_reports_zero_matches(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "app.py").write_text("print('hello world')\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="missing", path=".", access="project")

    assert result.outcome == "Found 0 matches"
    assert result.content is not None
    assert "Root: ." in result.content
    assert "Content: missing" in result.content


@pytest.mark.asyncio
async def test_returns_relative_paths_with_counts(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    pkg_dir = workspace / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "alpha.py").write_text("def foo():\n    return 'alpha'\n", encoding="utf-8")
    (pkg_dir / "beta.py").write_text("def bar():\n    return 'alpha'\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="alpha", path="pkg", access="project")

    assert result.outcome == "Found 2 matches"
    assert result.content is not None
    lines = [line for line in result.content.splitlines() if line and ":" in line]
    assert any(line.startswith("pkg/alpha.py:2:") for line in lines)
    assert any(line.startswith("pkg/beta.py:2:") for line in lines)

    second = await find.execute(pattern="alpha.py", path="pkg", access="project")
    assert second.outcome == "Found 1 match"
    assert second.content is not None
    entries = [
        line
        for line in second.content.splitlines()
        if line.startswith("pkg/") and line.endswith(".py")
    ]
    assert entries == ["pkg/alpha.py"]
    # Ensure sanitised output preserves shell-friendly quoting if used downstream
    shlex.split(entries[0])


# --- Access Scope Denial ---


@pytest.mark.asyncio
async def test_rejects_absolute_path_in_sandbox(tmp_path):
    result = await find.execute(
        path="/etc", content="x", sandbox_dir=str(tmp_path), access="sandbox"
    )
    assert result.error is True
    assert "Invalid path" in result.outcome or "outside sandbox" in result.outcome


@pytest.mark.asyncio
async def test_rejects_traversal_in_sandbox(tmp_path):
    result = await find.execute(
        path="../../../etc", content="x", sandbox_dir=str(tmp_path), access="sandbox"
    )
    assert result.error is True
    assert "Invalid path" in result.outcome or "outside sandbox" in result.outcome


@pytest.mark.asyncio
async def test_rejects_absolute_path_in_project(tmp_path):
    result = await find.execute(
        path="/etc", content="x", sandbox_dir=str(tmp_path), access="project"
    )
    assert result.error is True
    assert "Invalid path" in result.outcome or "outside sandbox" in result.outcome


@pytest.mark.asyncio
async def test_rejects_traversal_in_project(tmp_path):
    result = await find.execute(
        path="../../../etc", content="x", sandbox_dir=str(tmp_path), access="project"
    )
    assert result.error is True
    assert "Invalid path" in result.outcome or "outside sandbox" in result.outcome


@pytest.mark.asyncio
async def test_wildcard_pattern_matches_all(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "foo.py").write_text("x", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(pattern="*", content="x", path=".", access="project")
    assert result.outcome == "Found 1 match"


@pytest.mark.asyncio
async def test_glob_pattern_matches(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "test_foo.py").write_text("x", encoding="utf-8")
    (workspace / "main.py").write_text("x", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(pattern="test_*.py", path=".", access="project")
    assert result.content is not None
    assert "test_foo.py" in result.content


@pytest.mark.asyncio
async def test_partial_name_match(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "utils.py").write_text("x", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(pattern="util", path=".", access="project")
    assert result.content is not None
    assert "utils.py" in result.content


@pytest.mark.asyncio
async def test_search_content_skips_binary(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "binary.dat").write_bytes(b"\x00\x01\x02\xff")
    monkeypatch.chdir(workspace)

    result = await find.execute(pattern="*.dat", content="foo", path=".", access="project")
    assert result.outcome == "Found 0 matches"


@pytest.mark.asyncio
async def test_search_single_file(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "target.py").write_text("needle", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="needle", path="target.py", access="project")
    assert result.outcome == "Found 1 match"


@pytest.mark.asyncio
async def test_skips_hidden_and_venv(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = workspace / ".hidden"
    hidden.mkdir()
    (hidden / "secret.py").write_text("needle", encoding="utf-8")
    venv = workspace / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("needle", encoding="utf-8")
    (workspace / "visible.py").write_text("needle", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="needle", path=".", access="project")
    assert result.outcome == "Found 1 match"
    assert result.content is not None
    assert "visible.py" in result.content


@pytest.mark.asyncio
async def test_validates_no_params():
    result = await find.execute(access="project")
    assert result.error is True
    assert "Must specify" in result.outcome


@pytest.mark.asyncio
async def test_validates_broad_pattern():
    result = await find.execute(pattern="*", access="project")
    assert result.error is True
    assert "too broad" in result.outcome


@pytest.mark.asyncio
async def test_sandbox_creates_dir(tmp_path):
    sandbox = tmp_path / "sandbox"
    await find.execute(
        pattern="*.py", content="x", path=".", sandbox_dir=str(sandbox), access="sandbox"
    )
    assert sandbox.exists()


@pytest.mark.asyncio
async def test_system_access_uses_search_path_as_root(tmp_path):
    (tmp_path / "test.py").write_text("content", encoding="utf-8")
    result = await find.execute(content="content", path=str(tmp_path), access="system")
    assert result.outcome == "Found 1 match"


@pytest.mark.asyncio
async def test_nonexistent_directory(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    result = await find.execute(content="x", path="missing", access="project")
    assert result.error is True
    assert "does not exist" in result.outcome


@pytest.mark.asyncio
async def test_truncates_large_results(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for i in range(150):
        (workspace / f"file{i:03d}.py").write_text("needle", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="needle", path=".", access="project")
    assert result.content is not None
    assert "Truncated" in result.content
    assert "150" in result.content


@pytest.mark.asyncio
async def test_recurses_into_nested_directories(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    nested = workspace / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "deep.py").write_text("needle", encoding="utf-8")
    monkeypatch.chdir(workspace)

    result = await find.execute(content="needle", path=".", access="project")
    assert result.outcome == "Found 1 match"
    assert result.content is not None
    assert "a/b/c/deep.py" in result.content
