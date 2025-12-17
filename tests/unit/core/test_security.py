import os
import tempfile
from pathlib import Path

import pytest

from cogency.core.errors import ToolError
from cogency.core.security import (
    resolve_file,
    sanitize_shell_input,
    timeout_context,
    validate_path,
)


@pytest.fixture
def attacks():
    return {
        "shell": [
            "ls; rm -rf /",
            "ls && rm",
            "ls | cat",
            "ls > file",
            "ls `cmd`",
            "ls $(cmd)",
            "ls $VAR",
            "ls\nrm",
            "ls\x00rm",
        ],
        "path": [
            "../../../etc/passwd",
            "/etc/passwd",
            "/bin/sh",
            "C:\\Windows\\System32",
            "file\x00.txt",
        ],
    }


@pytest.fixture
def safe():
    return {
        "shell": [
            "ls -la",
            "grep 'pattern' file.txt",
            "python -c 'print(\"hi\")'",
            "echo '$HOME'",
        ],
        "path": ["file.txt", "subdir/file.txt", "./config.json"],
    }


def test_shell_blocks_injection(attacks):
    for cmd in attacks["shell"]:
        with pytest.raises(ToolError):
            sanitize_shell_input(cmd)


def test_shell_allows_safe(safe):
    for cmd in safe["shell"]:
        result = sanitize_shell_input(cmd)
        assert isinstance(result, str)


def test_shell_empty():
    with pytest.raises(ToolError):
        sanitize_shell_input("")


def test_shell_unbalanced_quotes():
    with pytest.raises(ToolError, match="Invalid shell command syntax"):
        sanitize_shell_input("echo 'unbalanced")


def test_path_blocks_traversal(attacks):
    with tempfile.TemporaryDirectory() as tmp:
        for path in attacks["path"]:
            with pytest.raises(ToolError, match="Path outside sandbox|Invalid path"):
                validate_path(path, Path(tmp))


def test_path_blocks_system(attacks):
    system = [p for p in attacks["path"] if p.startswith("/") or "C:\\" in p]
    for path in system:
        with pytest.raises(ToolError, match="Invalid path"):
            validate_path(path)


def test_path_allows_safe(safe):
    for path in safe["path"]:
        result = validate_path(path)
        assert isinstance(result, Path)


def test_path_empty():
    with pytest.raises(ToolError):
        validate_path("")


def test_timeout_completes():
    with timeout_context(5):
        assert sum(range(1000)) == 499500


@pytest.mark.skipif(os.name == "nt", reason="Unix only")
def test_timeout_enforces():
    import time

    with pytest.raises(TimeoutError), timeout_context(1):
        time.sleep(2)


def test_resolve_sandbox(tmp_path):
    result = resolve_file("test.txt", "sandbox", sandbox_dir=str(tmp_path))
    assert str(tmp_path) in str(result)


def test_resolve_sandbox_blocks_absolute(tmp_path):
    with pytest.raises(ToolError):
        resolve_file("/etc/passwd", "sandbox", sandbox_dir=str(tmp_path))


def test_resolve_sandbox_strips_doubling(tmp_path):
    result = resolve_file("sandbox/app.py", "sandbox", sandbox_dir=str(tmp_path))
    assert "sandbox/sandbox" not in str(result)
    assert str(result).endswith("app.py")


def test_resolve_project():
    result = resolve_file("test.txt", "project")
    assert result == Path.cwd() / "test.txt"


def test_resolve_project_blocks_system():
    with pytest.raises(ToolError):
        resolve_file("/etc/passwd", "project")


def test_resolve_system_blocks_dangerous():
    with pytest.raises(ToolError):
        resolve_file("/etc/passwd", "system")


def test_resolve_system_allows_safe():
    with tempfile.NamedTemporaryFile() as tmp:
        result = resolve_file(tmp.name, "system")
        assert isinstance(result, Path)
