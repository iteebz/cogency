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
    tool, base_dir, access = file_tool
    absolute_paths = [
        "/home/user/file.txt",
        "/tmp/test.txt",
        "/var/log/system.log",
        "C:\\Users\\test\\file.txt",
    ]

    for path in absolute_paths:
        result = await tool.execute(path, base_dir=base_dir, access=access)
        assert "Path outside sandbox" in result.outcome or "Invalid path" in result.outcome


@pytest.mark.asyncio
async def test_legitimate_operations_allowed(shell_tool, file_tool):
    shell, shell_base = shell_tool
    shell_result = await shell.execute("echo hello", base_dir=shell_base)
    assert "Command completed" in shell_result.outcome

    file, file_base, access = file_tool
    try:
        file_result = await file.execute("test.txt", base_dir=file_base, access=access)
        assert "Invalid path" not in file_result.outcome and "Security violation" not in file_result.outcome
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
async def test_project_access_mode(tmp_path):
    project_tool = FileRead()
    base_dir = str(tmp_path)

    result1 = await project_tool.execute("/etc/passwd", base_dir=base_dir, access="project")
    assert "Invalid path" in result1.outcome

    result2 = await project_tool.execute("../../../etc/passwd", base_dir=base_dir, access="project")
    assert "Invalid path" in result2.outcome

    try:
        result3 = await project_tool.execute("README.md", base_dir=base_dir, access="project")
        assert "Invalid path" not in result3.outcome
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
async def test_system_access_mode(tmp_path):
    system_tool = FileRead()
    base_dir = str(tmp_path)

    result1 = await system_tool.execute("/etc/passwd", base_dir=base_dir, access="system")
    assert "Invalid path" in result1.outcome

    result2 = await system_tool.execute("../../../etc/passwd", base_dir=base_dir, access="system")
    assert "Invalid path" in result2.outcome