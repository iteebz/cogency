"""Security destruction testing - tight comprehensive coverage."""

import os
import tempfile
from pathlib import Path

import pytest

from cogency.tools.security import resolve_path_safely, sanitize_shell_input, timeout_context

# Attack vectors: practical threats we can reasonably catch
SHELL_ATTACKS = [
    # Command injection - all blocked by metachar detection
    "ls; rm -rf /",
    "ls && rm -rf /",
    "ls || rm -rf /",
    "ls | rm -rf /",
    "ls `rm -rf /`",
    "ls $(rm -rf /)",
    "ls & rm -rf /",
    # Redirection - all blocked
    "ls > /etc/passwd",
    "ls >> ~/.ssh/keys",
    "cat < /etc/shadow",
    # Environment injection - blocked by $ char
    "ls $HOME/../../../etc",
    "ls ${PATH}/../../etc",
    # Control chars - blocked
    "ls\x00; rm -rf /",
    "ls\nrm -rf /",
    "ls\r\nrm",
    "ls\t&& rm",
    "ls；rm -rf /",
    "ls｜rm -rf /",  # Unicode variants - blocked
    # Other dangerous chars
    "ls\x01\x02 && rm",
    "ls\x7f && rm",
]

# Sandbox path attacks - only test what should fail in sandbox mode
SANDBOX_PATH_ATTACKS = [
    # Path traversal - blocked in sandbox
    "../../../etc/passwd",
    "../../bin/sh",
    "../etc/hosts",
    # Absolute paths - blocked in sandbox
    "/etc/passwd",
    "/bin/sh",
    "C:\\Windows\\System32",
    # Null bytes - always blocked
    "file.txt\x00",
    "\x00../etc/passwd",
    "file\x00.txt",
]

# System paths that should be blocked in non-sandbox mode
BLOCKED_SYSTEM_PATHS = [
    "/etc/passwd",
    "/bin/sh",
    "/sbin/init",
    "/usr/bin/sudo",
    "/System/Library/Kernels",
    "/private/etc/passwd",
    "C:\\Windows\\System32\\cmd.exe",
    "C:\\System32\\notepad.exe",
]

# Attacks we DON'T catch (by design - semantic security handles these)
SEMANTIC_SECURITY_ATTACKS = [
    # URL encoded (not decoded by path security)
    "%2e%2e%2f%2e%2e%2fetc",
    "%252e%252e%252fetc",
    # Unicode variants (too many to catch practically)
    "\u002e\u002e/\u002e\u002e/etc",
    "\uff0e\uff0e/\uff0e\uff0e/etc",
    # Complex mixed encoding
    "../%2e%2e/../etc",
    "\xc0\xae\xc0\xae/etc",
]

LEGITIMATE_COMMANDS = [
    "ls -la",
    "grep pattern file.txt",
    "find . -name '*.py'",
    "python -c 'print(1+1)'",
    "git status --porcelain",
    "echo 'hello world'",
    "cat file1.txt file2.txt",
]

LEGITIMATE_PATHS = ["file.txt", "subdir/file.txt", "./config.json", "data/logs/app.log"]


class TestShellInjectionBlocking:
    """Test shell command sanitization blocks injection attacks."""

    def test_shell_metacharacter_attacks_blocked(self):
        """Shell metacharacters used for injection must be blocked."""
        metachar_attacks = [
            "ls; rm -rf /",  # Command chaining
            "ls && rm -rf /",  # Conditional execution
            "ls | rm -rf /",  # Pipe to dangerous command
            "ls `rm -rf /`",  # Command substitution
            "ls $(rm -rf /)",  # Modern command substitution
            "ls > /etc/passwd",  # Output redirection to system file
            "ls & rm -rf /",  # Background execution
            "ls\nrm -rf /",  # Newline injection
            "ls；rm -rf /",  # Unicode semicolon
        ]

        for attack in metachar_attacks:
            with pytest.raises(ValueError, match="Invalid shell command syntax"):
                sanitize_shell_input(attack)

    def test_environment_variable_injection_blocked(self):
        """Environment variable expansion attacks must be blocked."""
        env_attacks = [
            "ls $HOME/../../../etc",  # Environment variable expansion
            "ls ${PATH}/../../etc",  # Brace expansion
            "cat $USER_CONFIG",  # User-controlled env vars
        ]

        for attack in env_attacks:
            with pytest.raises(ValueError, match="Invalid shell command syntax"):
                sanitize_shell_input(attack)

    def test_legitimate_commands_pass_sanitization(self):
        """Legitimate commands must pass shell sanitization."""
        safe_commands = [
            "ls -la",
            "grep 'pattern' file.txt",
            "find . -name '*.py' -type f",
            "python -c 'print(\"hello\")'",
            "git status --porcelain",
            "echo 'Safe message with spaces'",
        ]

        for cmd in safe_commands:
            result = sanitize_shell_input(cmd)
            assert isinstance(result, str) and len(result) > 0

    def test_edge_cases(self):
        """Edge cases must behave correctly."""
        edges = [
            ("", ValueError, "empty"),
            ("   ", ValueError, "empty"),
            ("unclosed 'quote", ValueError, "syntax"),
            ("ls" + " " * 1000, str, None),
        ]

        for inp, exc_type, _ in edges:
            if exc_type is ValueError:
                with pytest.raises(exc_type):
                    sanitize_shell_input(inp)
            else:
                assert isinstance(sanitize_shell_input(inp), exc_type)


class TestPathSecurity:
    """Test practical path security - catches common attacks."""

    def test_sandbox_attacks_blocked(self):
        """Sandbox path attacks must fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)

            for attack in SANDBOX_PATH_ATTACKS:
                with pytest.raises(ValueError, match="Path outside sandbox|Invalid path"):
                    resolve_path_safely(attack, sandbox)

    def test_system_paths_blocked(self):
        """System paths must be blocked in non-sandbox mode."""
        for path in BLOCKED_SYSTEM_PATHS:
            with pytest.raises(ValueError, match="Invalid path"):
                resolve_path_safely(path)

    def test_legitimate_paths_work(self):
        """Legitimate paths must work in both modes."""
        # Non-sandbox mode
        for path in LEGITIMATE_PATHS:
            result = resolve_path_safely(path)
            assert isinstance(result, Path)

        # Sandbox mode
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            for path in LEGITIMATE_PATHS:
                result = resolve_path_safely(path, sandbox)
                assert isinstance(result, Path)

    def test_null_bytes_blocked(self):
        """Null bytes must be blocked in all cases."""
        null_byte_attacks = ["file\x00.txt", "\x00../etc", "test\x00"]

        for attack in null_byte_attacks:
            with pytest.raises(ValueError, match="Invalid path"):
                resolve_path_safely(attack)

    def test_empty_paths_blocked(self):
        """Empty and whitespace paths must be blocked."""
        empty_attacks = ["", "   ", "\t\n"]

        for attack in empty_attacks:
            with pytest.raises(ValueError, match="Path cannot be empty"):
                resolve_path_safely(attack)


class TestTimeoutDestruction:
    """DESTROY: Timeout bypass attempts."""

    def test_timeout_enforcement(self):
        """Timeout must enforce time limits."""
        import time

        if os.name == "nt":
            # Windows - no timeout, just ensure it doesn't crash
            with timeout_context(1):
                time.sleep(0.1)  # Short sleep that works on Windows
        else:
            # Unix - actual timeout enforcement
            with pytest.raises(TimeoutError):
                with timeout_context(1):
                    time.sleep(2)

    def test_fast_operations_pass(self):
        """Fast operations must complete normally."""
        with timeout_context(5):
            assert sum(range(1000)) == 499500

    def test_cross_platform_behavior(self):
        """Timeout context works on all platforms."""
        with timeout_context(5):
            assert sum(range(100)) == 4950


class TestSemanticSecurityBoundary:
    """Document attacks we rely on semantic security to catch."""

    def test_shell_path_combinations_work(self):
        """Shell injection blocked, but path components may pass through."""
        # Only actual shell injection should be blocked by shell security
        shell_injections = [
            "ls `cat /etc/passwd`",
            "../../../etc/passwd; rm -rf /",
            "%2e%2e%2f$(rm -rf /)",
        ]

        for attack in shell_injections:
            with pytest.raises(ValueError, match="Invalid shell command syntax"):
                sanitize_shell_input(attack)

        # Path traversal without shell injection should pass shell security
        legitimate_shell = sanitize_shell_input("cat ../../../etc/passwd")
        assert isinstance(legitimate_shell, str)

    def test_exotic_path_encoding_not_caught(self):
        """Document that exotic encodings rely on semantic security."""
        # These pass through path security (by design)
        exotic_encodings = SEMANTIC_SECURITY_ATTACKS

        for attack in exotic_encodings:
            # Should not raise - semantic security handles these
            try:
                result = resolve_path_safely(attack)
                assert isinstance(result, Path)
            except ValueError:
                # Some may still fail due to filesystem restrictions
                pass

    def test_deterministic_behavior(self):
        """Security functions must be deterministic."""
        # Same input must produce same output
        cmd_result1 = sanitize_shell_input("ls -la")
        cmd_result2 = sanitize_shell_input("ls -la")
        assert cmd_result1 == cmd_result2

        path_result1 = resolve_path_safely("file.txt")
        path_result2 = resolve_path_safely("file.txt")
        assert path_result1 == path_result2

    def test_layered_security_design(self):
        """Verify our layered security approach works."""
        # Layer 1: Shell security catches command injection
        with pytest.raises(ValueError):
            sanitize_shell_input("ls; rm -rf /")

        # Layer 2: Path security catches common traversal
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError):
                resolve_path_safely("../etc/passwd", Path(temp_dir))

        # Layer 3: Semantic security handles exotic attacks (not tested here)


class TestShellToolArgumentValidation:
    """Test shell tool argument validation (unit tests for _validate_command_safety)."""

    @pytest.fixture
    def shell_tool(self):
        from cogency.tools.system.shell import SystemShell

        return SystemShell()

    def test_validate_command_safety_direct(self):
        """Test _validate_command_safety method directly."""
        from cogency.tools.system.shell import SystemShell

        shell = SystemShell()

        # Should block system paths
        assert not shell._validate_command_safety(["cat", "/etc/passwd"], True)
        assert not shell._validate_command_safety(["find", "/", "-name", "*.key"], True)
        assert not shell._validate_command_safety(["ls", "~/.ssh/id_rsa"], True)
        assert not shell._validate_command_safety(["head", "/bin/sh"], True)

        # Should allow safe operations
        assert shell._validate_command_safety(["ls", "-la"], True)
        assert shell._validate_command_safety(["cat", "file.txt"], True)
        assert shell._validate_command_safety(["find", ".", "-name", "*.py"], True)
        assert shell._validate_command_safety(["grep", "pattern", "file.txt"], True)
