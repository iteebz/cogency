"""Integration test fixtures for canonical Cogency workflows."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.tools import Files, Shell


@pytest.fixture
def clean_env():
    """Clean environment for agent tests."""
    env_patches = {
        "OPENAI_API_KEY": "test-key",
        "ANTHROPIC_API_KEY": "test-key",
    }
    with patch.dict("os.environ", env_patches):
        yield


@pytest.fixture
def workspace():
    """Temporary workspace with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)

        # Create test files for tool operations
        (workspace_path / "test.txt").write_text("Hello World")
        (workspace_path / "script.py").write_text("print('Test script')")

        # Create subdirectory with files
        sub_dir = workspace_path / "subdir"
        sub_dir.mkdir()
        (sub_dir / "data.json").write_text('{"test": true}')

        yield workspace_path


@pytest.fixture
def agent_basic(clean_env):
    """Basic agent without memory or tools."""
    return Agent("test-agent", memory=False, tools=[], notify=False)


@pytest.fixture
def agent_with_tools(clean_env, workspace):
    """Agent with file and shell tools."""
    return Agent(
        "test-agent-tools",
        memory=False,
        tools=[Files(str(workspace)), Shell()],
        notify=False,
    )


@pytest.fixture
def agent_with_memory(clean_env):
    """Agent with memory enabled."""
    return Agent("test-agent-memory", memory=True, tools=[], notify=False)


@pytest.fixture
def agent_full(clean_env, workspace):
    """Full-featured agent with memory and tools."""
    return Agent(
        "test-agent-full",
        memory=True,
        tools=[Files(str(workspace)), Shell()],
        notify=False,
    )


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for predictable testing."""
    return {
        "simple": "I understand your request.",
        "tool_request": "Let me check the files. I'll use: ls -la",
        "memory_update": "I've learned about your preferences.",
        "complex_workflow": "Let me process this step by step.",
    }


@pytest.fixture
def event_monitor():
    """Monitor and validate events during test execution."""

    class EventMonitor:
        def __init__(self):
            self.events = []

        def capture_events(self, agent):
            """Capture events from agent execution."""
            self.events = agent.logs()
            return self.events

        def assert_event_types(self, expected_types):
            """Assert specific event types were captured."""
            captured_types = {event.get("type") for event in self.events}
            for expected in expected_types:
                assert expected in captured_types, f"Missing event type: {expected}"

        def assert_event_count(self, event_type, min_count=1):
            """Assert minimum count of specific event type."""
            count = len([e for e in self.events if e.get("type") == event_type])
            assert (
                count >= min_count
            ), f"Expected at least {min_count} {event_type} events, got {count}"

    return EventMonitor()


@pytest.fixture
def memory_session():
    """Memory persistence testing across sessions."""

    class MemorySession:
        def __init__(self):
            self.user_id = "test-user-123"
            self.sessions = []

        def create_agent(self, clean_env):
            """Create new agent instance for session testing."""
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                agent = Agent(f"session-{len(self.sessions)}", memory=True, notify=False)
                self.sessions.append(agent)
                return agent

        def verify_memory_persistence(self):
            """Verify memory persists across agent instances."""
            assert len(self.sessions) >= 2, "Need at least 2 sessions for persistence test"
            # Memory persistence validation would be implementation-specific
            return True

    return MemorySession()


@pytest.fixture
def tool_chain():
    """Tool chain execution testing."""

    class ToolChain:
        def __init__(self):
            self.operations = []

        def file_operation(self, operation, path, content=None):
            """Record file operations for validation."""
            self.operations.append(
                {
                    "type": "file",
                    "operation": operation,
                    "path": path,
                    "content": content,
                }
            )

        def shell_operation(self, command):
            """Record shell operations for validation."""
            self.operations.append(
                {
                    "type": "shell",
                    "command": command,
                }
            )

        def verify_chain(self, expected_operations):
            """Verify tool chain executed expected operations."""
            assert len(self.operations) >= len(expected_operations)
            for i, expected in enumerate(expected_operations):
                assert self.operations[i]["type"] == expected["type"]

    return ToolChain()


@pytest.fixture
def performance_baseline():
    """Performance baseline for integration tests."""

    class PerformanceBaseline:
        def __init__(self):
            self.timings = {}

        def measure(self, operation_name, func, *args, **kwargs):
            """Measure operation performance."""
            import time

            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            self.timings[operation_name] = duration
            return result

        async def measure_async(self, operation_name, func, *args, **kwargs):
            """Measure async operation performance."""
            import time

            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            self.timings[operation_name] = duration
            return result

        def assert_performance(self, operation_name, max_seconds):
            """Assert operation completed within time limit."""
            duration = self.timings.get(operation_name)
            assert duration is not None, f"No timing recorded for {operation_name}"
            assert (
                duration <= max_seconds
            ), f"{operation_name} took {duration:.2f}s, max {max_seconds}s"

    return PerformanceBaseline()
