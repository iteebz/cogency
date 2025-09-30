import os
import tempfile
from pathlib import Path

import pytest

from cogency.tools.security import (
    resolve_file,
    sanitize_shell_input,
    timeout_context,
    validate_path,
)

# Comprehensive attack vectors for systematic security coverage
SHELL_INJECTION_ATTACKS = [
    # Command chaining and execution
    "ls; rm -rf /",
    "ls && rm -rf /",
    "ls || rm -rf /",
    "ls & rm -rf /",
    # Command substitution
    "ls `rm -rf /`",
    "ls $(rm -rf /)",
    # Piping and redirection
    "ls | rm -rf /",
    "ls > /etc/passwd",
    "ls >> ~/.ssh/keys",
    "cat < /etc/shadow",
    # Environment variable expansion
    "ls $HOME/../../../etc",
    "ls ${PATH}/../../etc",
    "cat $USER_CONFIG",
    # Control character injection
    "ls\x00; rm -rf /",
    "ls\nrm -rf /",
    "ls\r\nrm",
    "ls\t&& rm",
    # Unicode variants and exotic characters
    "ls；rm -rf /",
    "ls｜rm -rf /",
    "ls\x01\x02 && rm",
    "ls\x7f && rm",
]

PATH_TRAVERSAL_ATTACKS = [
    # Directory traversal
    "../../../etc/passwd",
    "../../bin/sh",
    "../etc/hosts",
    # Absolute system paths
    "/etc/passwd",
    "/bin/sh",
    "/sbin/init",
    "/usr/bin/sudo",
    "/System/Library/Kernels",
    "/private/etc/passwd",
    "C:\\Windows\\System32\\cmd.exe",
    "C:\\System32\\notepad.exe",
    # Null byte attacks
    "file.txt\x00",
    "\x00../etc/passwd",
    "file\x00.txt",
]

SEMANTIC_SECURITY_BOUNDARY_ATTACKS = [
    # URL encoded (semantic security handles these)
    "%2e%2e%2f%2e%2e%2fetc",
    "%252e%252e%252fetc",
    # Unicode variants (too many to catch practically)
    "\u002e\u002e/\u002e\u002e/etc",
    "\uff0e\uff0e/\uff0e\uff0e/etc",
    # Mixed encoding complexity
    "../%2e%2e/../etc",
    "\xc0\xae\xc0\xae/etc",
]

LEGITIMATE_INPUTS = {
    "commands": [
        "ls -la",
        "grep 'pattern' file.txt",
        "find . -name '*.py' -type f",
        "python -c 'print(\"hello\")'",
        "git status --porcelain",
        "echo 'Safe message'",
    ],
    "paths": ["file.txt", "subdir/file.txt", "./config.json", "data/logs/app.log"],
}


def test_attack_blocking():
    # Shell injection attacks must be blocked
    for attack in SHELL_INJECTION_ATTACKS:
        with pytest.raises(ValueError, match="Invalid shell command syntax"):
            sanitize_shell_input(attack)

    # Legitimate commands must pass
    for cmd in LEGITIMATE_INPUTS["commands"]:
        result = sanitize_shell_input(cmd)
        assert isinstance(result, str) and len(result) > 0

    # Path traversal attacks blocked in sandbox mode
    with tempfile.TemporaryDirectory() as temp_dir:
        sandbox = Path(temp_dir)
        for attack in PATH_TRAVERSAL_ATTACKS:
            with pytest.raises(ValueError, match="Path outside sandbox|Invalid path"):
                validate_path(attack, sandbox)

    # System paths blocked in non-sandbox mode
    system_paths = [p for p in PATH_TRAVERSAL_ATTACKS if p.startswith("/") or "C:\\" in p]
    for path in system_paths:
        with pytest.raises(ValueError, match="Invalid path"):
            validate_path(path)

    # Legitimate paths work in both modes
    for path in LEGITIMATE_INPUTS["paths"]:
        assert isinstance(validate_path(path), Path)
        with tempfile.TemporaryDirectory() as temp_dir:
            assert isinstance(validate_path(path, Path(temp_dir)), Path)

    # Edge case validation
    edge_cases = [
        ("", "Path cannot be empty"),
        ("   ", "Path cannot be empty"),
        ("unclosed 'quote", "Invalid shell command syntax"),
    ]

    for invalid_input, error_pattern in edge_cases:
        with pytest.raises(ValueError, match=error_pattern):
            if invalid_input.strip() == "":
                validate_path(invalid_input)
            else:
                sanitize_shell_input(invalid_input)


def test_timeout_enforcement():
    import time

    # Fast operations complete normally
    with timeout_context(5):
        assert sum(range(1000)) == 499500

    # Platform-specific timeout behavior
    if os.name == "nt":
        # Windows: ensure no crashes
        with timeout_context(1):
            time.sleep(0.1)
    else:
        # Unix: actual timeout enforcement
        with pytest.raises(TimeoutError):
            with timeout_context(1):
                time.sleep(2)


def test_semantic_security_boundaries():
    # Shell injection blocked at security layer
    shell_attacks_with_paths = [
        "ls `cat /etc/passwd`",
        "../../../etc/passwd; rm -rf /",
        "%2e%2e%2f$(rm -rf /)",
    ]

    for attack in shell_attacks_with_paths:
        with pytest.raises(ValueError, match="Invalid shell command syntax"):
            sanitize_shell_input(attack)

    # Path traversal without shell injection passes shell security
    legitimate_shell = sanitize_shell_input("cat ../../../etc/passwd")
    assert isinstance(legitimate_shell, str)

    # Exotic encodings pass path security (semantic layer handles these)
    for attack in SEMANTIC_SECURITY_BOUNDARY_ATTACKS:
        try:
            result = validate_path(attack)
            assert isinstance(result, Path)
        except ValueError:
            pass  # Some may fail due to filesystem restrictions

    # Security functions are deterministic
    assert sanitize_shell_input("ls -la") == sanitize_shell_input("ls -la")
    assert validate_path("file.txt") == validate_path("file.txt")


def test_shell_input_sanitization():
    from cogency.tools.security import sanitize_shell_input

    # Test dangerous commands are blocked
    for cmd in SHELL_INJECTION_ATTACKS[:5]:  # Test subset
        with pytest.raises(ValueError):
            sanitize_shell_input(cmd)

    # Test safe commands are allowed
    safe_commands = ["ls", "pwd", "echo hello"]
    for cmd in safe_commands:
        result = sanitize_shell_input(cmd)
        assert result == cmd


def test_resolve_file_access_levels(tmp_path: Path):
    # SANDBOX access - restricts to sandbox directory
    with pytest.raises(ValueError, match="Invalid path"):
        resolve_file("/etc/passwd", "sandbox", base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="Invalid path"):
        resolve_file("../../../etc/passwd", "sandbox", base_dir=str(tmp_path))

    # Should work for relative paths in a custom sandbox
    result = resolve_file("test.txt", "sandbox", base_dir=str(tmp_path))
    assert isinstance(result, Path)
    assert str(tmp_path) in str(result)

    # Should prevent path doubling when 'sandbox/' is in the file path
    result_doubling = resolve_file("sandbox/app.py", "sandbox", base_dir=str(tmp_path))
    assert isinstance(result_doubling, Path)
    assert str(tmp_path) in str(result_doubling)
    assert "sandbox/sandbox" not in str(result_doubling)
    assert str(result_doubling).endswith("sandbox/app.py")
    # PROJECT access - restricts to project directory (base_dir)
    with pytest.raises(ValueError, match="Invalid path"):
        resolve_file("/etc/passwd", "project", base_dir=str(tmp_path))

    # Should work for relative paths in project
    result = resolve_file("test.txt", "project", base_dir=str(tmp_path))
    assert isinstance(result, Path)
    assert str(tmp_path) in str(result)

    # SYSTEM access - blocks dangerous paths but allows absolute paths
    with pytest.raises(ValueError, match="Invalid path"):
        resolve_file("/etc/passwd", "system")

    with pytest.raises(ValueError, match="Invalid path"):
        resolve_file("../../../etc/passwd", "system")

    # Should work for safe absolute paths
    with tempfile.NamedTemporaryFile() as tmp:
        result = resolve_file(tmp.name, "system")
        assert isinstance(result, Path)
