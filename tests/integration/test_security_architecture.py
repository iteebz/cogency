import pytest

from cogency.tools import Read, Shell


@pytest.fixture
def shell_tool(tmp_path):
    return Shell, str(tmp_path)


@pytest.fixture
def file_tool(tmp_path):
    return Read, str(tmp_path), "sandbox"


@pytest.mark.asyncio
async def test_shell_injection(shell_tool):
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
        result = await tool.execute(command=attack, sandbox_dir=base_dir)
        assert "Invalid shell command syntax" in result.outcome or "not supported" in result.outcome


@pytest.mark.asyncio
async def test_path_traversal(file_tool):
    tool, base_dir, access = file_tool
    traversal_attacks = [
        "../../../etc/passwd",
        "../../../../etc/shadow",
        "../../../bin/bash",
        "..\\..\\..\\windows\\system32",
    ]

    for attack in traversal_attacks:
        result = await tool.execute(file=attack, sandbox_dir=base_dir, access=access)
        assert (
            "Invalid path" in result.outcome
            or "not found" in result.outcome
            or "directory" in result.outcome
        )


@pytest.mark.asyncio
async def test_system_paths(file_tool):
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
        result = await tool.execute(file=path, sandbox_dir=base_dir, access=access)
        assert "Invalid path" in result.outcome or "not found" in result.outcome


@pytest.mark.asyncio
async def test_sandbox_boundaries(file_tool):
    tool, base_dir, access = file_tool
    absolute_paths = [
        "/home/user/file.txt",
        "/tmp/test.txt",
        "/var/log/system.log",
        "C:\\Users\\test\\file.txt",
    ]

    for path in absolute_paths:
        result = await tool.execute(file=path, sandbox_dir=base_dir, access=access)
        assert (
            "Path outside sandbox" in result.outcome
            or "Invalid path" in result.outcome
            or "not found" in result.outcome
        )


@pytest.mark.asyncio
async def test_legitimate_ops(shell_tool, file_tool):
    shell, shell_base = shell_tool
    shell_result = await shell.execute(command="echo hello", sandbox_dir=shell_base)
    assert not shell_result.error
    assert shell_result.content == "hello"

    file, file_base, access = file_tool

    # Create test file first to ensure legitimate operation succeeds
    from pathlib import Path

    test_file = Path(file_base) / "test.txt"
    test_file.write_text("test content")

    file_result = await file.execute(file="test.txt", sandbox_dir=file_base, access=access)
    assert not file_result.error
    assert "Invalid path" not in file_result.outcome
    assert "Security violation" not in file_result.outcome


@pytest.mark.asyncio
async def test_project_access(tmp_path):
    base_dir = str(tmp_path)

    result1 = await Read.execute(file="/etc/passwd", sandbox_dir=base_dir, access="project")
    assert "Invalid path" in result1.outcome

    result2 = await Read.execute(file="../../../etc/passwd", sandbox_dir=base_dir, access="project")
    assert "Invalid path" in result2.outcome

    try:
        result3 = await Read.execute(file="README.md", sandbox_dir=base_dir, access="project")
        assert "Invalid path" not in result3.outcome
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
async def test_system_access(tmp_path):
    base_dir = str(tmp_path)

    result1 = await Read.execute(file="/etc/passwd", sandbox_dir=base_dir, access="system")
    assert "Invalid path" in result1.outcome

    result2 = await Read.execute(file="../../../etc/passwd", sandbox_dir=base_dir, access="system")
    assert "Invalid path" in result2.outcome
