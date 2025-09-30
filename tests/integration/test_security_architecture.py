"""Security architecture integration tests.

Tests that security layers work together correctly:
- Input sanitization blocks injection
- Path resolution blocks traversal
- File operations respect boundaries
"""

import pytest

from cogency.tools.file.read import FileRead
from cogency.tools.system.shell import SystemShell


@pytest.fixture
def shell_tool(tmp_path):
    return SystemShell(), str(tmp_path)


@pytest.fixture
def file_tool(tmp_path):
    return FileRead(), str(tmp_path), "sandbox"


@pytest.mark.asyncio
async def test_shell_injection_blocked(shell_tool):
    """Shell injection is blocked at input sanitization layer."""
    tool, base_dir = shell_tool
    injection_attacks = [
        "ls; rm -rf /",
        "ls && rm -rf /",
        "ls | rm -rf /",
        "ls `rm -rf /`",
        "ls $(rm -rf /)",
        "ls > /etc/passwd",
    ]

    for attack in injection_attacks:
        result = await tool.execute(attack, base_dir=base_dir)
        assert "Invalid shell command syntax" in result.outcome


@pytest.mark.asyncio
async def test_path_traversal_blocked(file_tool):
    """Path traversal is blocked at path resolution layer."""
    tool, base_dir, access = file_tool
    traversal_attacks = [
        "../../../etc/passwd",
        "../../../../etc/shadow",
        "../../../bin/bash",
        "..\\..\\..\\windows\\system32",
    ]

    for attack in traversal_attacks:
        result = await tool.execute(attack, base_dir=base_dir, access=access)
        assert "Invalid path" in result.outcome


@pytest.mark.asyncio
async def test_system_paths_blocked(file_tool):
    """System directory access is blocked at path resolution."""
    tool, base_dir, access = file_tool
    system_paths = [
        "/etc/passwd",
        "/etc/shadow",
        "/bin/bash",
        "/usr/bin/sudo",
        "/System/Library/",
        "C:\\Windows\\System32\\",
    ]

    for path in system_paths:
        result = await tool.execute(path, base_dir=base_dir, access=access)
        assert "Invalid path" in result.outcome


@pytest.mark.asyncio
async def test_sandbox_boundaries_enforced(file_tool):
    """Absolute paths are blocked in sandbox mode."""
    tool, base_dir, access = file_tool
    absolute_paths = [
        "/home/user/file.txt",
        "/tmp/test.txt",
        "/var/log/system.log",
        "C:\\Users\\test\\file.txt",
    ]

    for path in absolute_paths:
        result = await tool.execute(path, base_dir=base_dir, access=access)
        assert (
            "Path outside sandbox" in result.outcome or "Invalid path" in result.outcome
        )  # Security layer blocks absolute paths


@pytest.mark.asyncio
async def test_legitimate_operations_allowed(shell_tool, file_tool):
    """Legitimate operations pass through security layers."""
    # Safe shell commands
    shell, shell_base = shell_tool
    shell_result = await shell.execute("echo hello", base_dir=shell_base)
    assert "Command completed" in shell_result.outcome

    # Safe file operations (relative paths in sandbox)
    file, file_base, access = file_tool
    try:
        file_result = await file.execute("test.txt", base_dir=file_base, access=access)
        # If we get a result, security allowed it (no security violation)
        assert (
            "Invalid path" not in file_result.outcome
            and "Security violation" not in file_result.outcome
        )
    except FileNotFoundError:
        # FileNotFoundError means security allowed the operation but file doesn't exist
        pass  # This is the expected behavior for non-existent files


@pytest.mark.asyncio
async def test_project_access_mode(tmp_path):
    """PROJECT access allows project files but blocks system paths."""
    project_tool = FileRead()
    base_dir = str(tmp_path)

    # System paths still blocked in project mode
    result1 = await project_tool.execute("/etc/passwd", base_dir=base_dir, access="project")
    assert "Invalid path" in result1.outcome

    # Path traversal still blocked
    result2 = await project_tool.execute("../../../etc/passwd", base_dir=base_dir, access="project")
    assert "Invalid path" in result2.outcome

    # Project-relative paths should work (if they exist)
    try:
        result3 = await project_tool.execute("README.md", base_dir=base_dir, access="project")
        assert "Invalid path" not in result3.outcome
    except FileNotFoundError:
        pass  # File doesn't exist, but security allowed it


@pytest.mark.asyncio
async def test_system_access_mode(tmp_path):
    """SYSTEM access blocks dangerous paths but allows absolute paths."""
    system_tool = FileRead()
    base_dir = str(tmp_path)

    # System paths still blocked
    result1 = await system_tool.execute("/etc/passwd", base_dir=base_dir, access="system")
    assert "Invalid path" in result1.outcome

    # Traversal still blocked
    result2 = await system_tool.execute("../../../etc/passwd", base_dir=base_dir, access="system")
    assert "Invalid path" in result2.outcome
