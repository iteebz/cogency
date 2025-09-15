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
def shell_tool():
    return SystemShell()


@pytest.fixture
def file_tool():
    return FileRead()


@pytest.mark.asyncio
async def test_shell_injection_blocked(shell_tool):
    """Shell injection is blocked at input sanitization layer."""
    injection_attacks = [
        "ls; rm -rf /",
        "ls && rm -rf /",
        "ls | rm -rf /",
        "ls `rm -rf /`",
        "ls $(rm -rf /)",
        "ls > /etc/passwd",
    ]

    for attack in injection_attacks:
        result = await shell_tool.execute(attack, sandbox=True)
        assert "Invalid shell command syntax" in result.outcome


@pytest.mark.asyncio
async def test_path_traversal_blocked(file_tool):
    """Path traversal is blocked at path resolution layer."""
    traversal_attacks = [
        "../../../etc/passwd",
        "../../../../etc/shadow",
        "../../../bin/bash",
        "..\\..\\..\\windows\\system32",
    ]

    for attack in traversal_attacks:
        result = await file_tool.execute(attack, sandbox=True)
        assert "Invalid path" in result.outcome


@pytest.mark.asyncio
async def test_system_paths_blocked(file_tool):
    """System directory access is blocked at path resolution."""
    system_paths = [
        "/etc/passwd",
        "/etc/shadow",
        "/bin/bash",
        "/usr/bin/sudo",
        "/System/Library/",
        "C:\\Windows\\System32\\",
    ]

    for path in system_paths:
        result = await file_tool.execute(path, sandbox=True)
        assert "Invalid path" in result.outcome


@pytest.mark.asyncio
async def test_sandbox_boundaries_enforced(file_tool):
    """Absolute paths are blocked in sandbox mode."""
    absolute_paths = [
        "/home/user/file.txt",
        "/tmp/test.txt",
        "/var/log/system.log",
        "C:\\Users\\test\\file.txt",
    ]

    for path in absolute_paths:
        result = await file_tool.execute(path, sandbox=True)
        assert (
            "Path outside sandbox" in result.outcome or "Invalid path" in result.outcome
        )  # Security layer blocks absolute paths


@pytest.mark.asyncio
async def test_legitimate_operations_allowed(shell_tool, file_tool):
    """Legitimate operations pass through security layers."""
    # Safe shell commands
    shell_result = await shell_tool.execute("echo hello", sandbox=True)
    assert "Command completed" in shell_result.outcome

    # Safe file operations (relative paths in sandbox)
    try:
        file_result = await file_tool.execute("test.txt", sandbox=True)
        # If we get a result, security allowed it (no security violation)
        assert (
            "Invalid path" not in file_result.outcome
            and "Security violation" not in file_result.outcome
        )
    except FileNotFoundError:
        # FileNotFoundError means security allowed the operation but file doesn't exist
        pass  # This is the expected behavior for non-existent files


@pytest.mark.asyncio
async def test_security_in_non_sandbox_mode(file_tool):
    """Security validation works in non-sandbox mode too."""
    # System paths still blocked
    result1 = await file_tool.execute("/etc/passwd", sandbox=False)
    assert "Invalid path" in result1.outcome

    # Traversal still blocked
    result2 = await file_tool.execute("../../../etc/passwd", sandbox=False)
    assert "Invalid path" in result2.outcome
