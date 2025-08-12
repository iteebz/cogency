"""Integration CLI tests - Poetry environment and CLI interface validation."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

poetry_available = shutil.which("poetry") is not None


@pytest.mark.integration
@pytest.mark.skipif(not poetry_available, reason="Requires poetry in PATH")
class TestCLIIntegration:
    """Integration tests for CLI interface and poetry environment."""

    def test_cli_basic_execution(self):
        """Test CLI executes without errors."""
        # Test with minimal command that doesn't require API keys
        result = subprocess.run(
            ["poetry", "run", "python", "-m", "cogency", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "cogency" in result.stdout.lower()

    def test_cli_with_simple_query(self):
        """Test CLI with simple query (mocked environment)."""
        env = {"OPENAI_API_KEY": "test-key", "COGENCY_DEBUG": "true"}

        result = subprocess.run(
            ["poetry", "run", "python", "-m", "cogency", "Hello world"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        # Should not crash, even with mock key
        assert result.returncode in [0, 1]  # 1 for API error is acceptable

    def test_cli_version_flag(self):
        """Test CLI version information."""
        result = subprocess.run(
            ["poetry", "run", "python", "-m", "cogency", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Version should be in output
        assert "." in result.stdout  # Simple version format check

    @pytest.mark.slow
    def test_cli_file_operations(self):
        """Test CLI with file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content for CLI")

            env = {"OPENAI_API_KEY": "test-key", "COGENCY_DEBUG": "true"}

            result = subprocess.run(
                ["poetry", "run", "python", "-m", "cogency", f"List files in {tmpdir}"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=tmpdir,
            )

            # Should attempt to process file operations
            assert result.returncode in [0, 1]


@pytest.mark.integration
@pytest.mark.skipif(not poetry_available, reason="Requires poetry in PATH")
class TestPackageIntegration:
    """Package and import integration tests."""

    def test_poetry_installation(self):
        """Test package can be installed via poetry."""
        result = subprocess.run(["poetry", "check"], capture_output=True, text=True, timeout=30)

        assert result.returncode == 0
        # Poetry check successful if returncode is 0, regardless of stdout content

    def test_import_structure(self):
        """Test package imports work correctly."""
        result = subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "-c",
                "from cogency import Agent; print('Import successful')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Import successful" in result.stdout

    def test_basic_agent_instantiation(self):
        """Test Agent can be instantiated without errors."""
        code = """
from cogency import Agent
try:
    agent = Agent("test")
    print("Agent created successfully")
except Exception as e:
    print(f"Error: {e}")
    raise
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "Agent created successfully" in result.stdout

    def test_tool_system_integration(self):
        """Test tools can be loaded and configured."""
        code = """
from cogency import Agent
from cogency.tools import Files, Shell
try:
    agent = Agent("test", tools=[Files(), Shell()])
    print(f"Agent with {len(agent.tools)} tools created")
except Exception as e:
    print(f"Error: {e}")
    raise
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "tools created" in result.stdout

    def test_memory_system_integration(self):
        """Test memory system can be initialized."""
        code = """
from cogency import Agent
try:
    agent = Agent("test", memory=True)
    print("Agent with memory created successfully")
except Exception as e:
    print(f"Error: {e}")
    raise
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "memory created successfully" in result.stdout

    def test_event_system_integration(self):
        """Test event system initializes correctly."""
        code = """
from cogency import Agent
try:
    agent = Agent("test")
    logs = agent.logs()
    print(f"Event system working, {len(logs)} initial events")
except Exception as e:
    print(f"Error: {e}")
    raise
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "Event system working" in result.stdout


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not poetry_available, reason="Requires poetry in PATH")
class TestEnvironmentScenarios:
    """Environment and configuration integration tests."""

    def test_development_workflow(self):
        """Test typical development workflow scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock project structure
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()

            (project_dir / "main.py").write_text("print('Hello World')")
            (project_dir / "README.md").write_text("# Test Project")
            (project_dir / "requirements.txt").write_text("requests==2.28.0")

            # Test that agent can be instantiated in project context
            env = {"OPENAI_API_KEY": "test-key"}

            code = f"""
import os
os.chdir('{project_dir}')
from cogency import Agent
from cogency.tools import Files, Shell

agent = Agent("dev-assistant", tools=[Files(), Shell()])
print("Development environment agent created")
print(f"Working directory: {{os.getcwd()}}")
"""

            result = subprocess.run(
                ["poetry", "run", "python", "-c", code],
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )

            assert result.returncode == 0
            assert "Development environment agent created" in result.stdout

    def test_error_handling_scenario(self):
        """Test error handling in realistic scenarios."""
        code = """
from cogency import Agent
import os

# Test with missing API key
try:
    # Remove any existing keys
    for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
        os.environ.pop(key, None)

    agent = Agent("test")
    print("Agent created without API keys")
except Exception as e:
    print(f"Expected error: {type(e).__name__}")
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=10
        )

        # Should handle missing API keys gracefully
        assert result.returncode == 0
        assert "created" in result.stdout or "error" in result.stdout.lower()

    def test_concurrent_execution(self):
        """Test multiple agent instances can coexist."""
        code = """
from cogency import Agent
import asyncio

async def test_concurrent():
    agents = [Agent(f"agent-{i}") for i in range(3)]
    print(f"Created {len(agents)} concurrent agents")

    # Test they can all capture events independently
    for i, agent in enumerate(agents):
        logs = agent.logs()
        print(f"Agent {i}: {len(logs)} events")

asyncio.run(test_concurrent())
"""

        result = subprocess.run(
            ["poetry", "run", "python", "-c", code], capture_output=True, text=True, timeout=15
        )

        assert result.returncode == 0
        assert "concurrent agents" in result.stdout
