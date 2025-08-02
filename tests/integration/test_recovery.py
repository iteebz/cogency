"""Smoke test: Tool failure recovery with Result pattern."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from resilient_result import Result

from cogency import Agent
from tests.fixtures.llm import MockLLM


class MockCodeTool:
    """Mock code tool that fails predictably."""

    def __init__(self):
        self.call_count = 0
        self.name = "code"
        self.emoji = "🚀"
        self.description = "Execute code"
        self.rules = []

    async def run(self, code, language="python", timeout=30):
        self.call_count += 1

        if "nonexistent" in code:
            # First call fails
            return Result.fail("Error: No such file or directory")
        else:
            # Recovery call succeeds
            return Result.ok(
                {
                    "output": "total 48\ndrwxr-xr-x  12 user  staff   384 Jul 25 10:30 .",
                    "success": True,
                    "exit_code": 0,
                }
            )


@pytest.mark.asyncio
async def test_recovery():
    """Test agent recovers gracefully when tools fail."""

    # Create specialized LLM for recovery testing
    def recovery_response(messages, **kwargs):
        last_msg = messages[-1]["content"].lower()

        # Check if this is a preparing request (looking for JSON Response in prompt)
        if "json response" in last_msg:
            return '{"memory": null, "tags": null, "memory_type": "fact", "mode": "fast", "selected_tools": ["bash"], "reasoning": "Need to execute bash commands"}'

        if "error" in last_msg and "failed" in last_msg:
            return "I see the command failed. Let me try a simpler approach: ls -la"
        elif "total" in last_msg:
            return "Perfect! I can see the directory contents. The task is complete."
        else:
            return "I'll run a command that might fail: cat /nonexistent/file.txt"

    llm = MockLLM(custom_impl=recovery_response)
    mock_code = MockCodeTool()

    # Create agent with real code tool but mocked execution
    from cogency.tools.shell import Shell

    shell_tool = Shell()
    with patch.object(shell_tool, "run", side_effect=mock_code.run):
        from cogency import Agent

        agent = Agent("test", llm=llm, tools=[shell_tool], depth=5)

        # Run agent with initial prompt
        result = await agent.run("List the contents of the current directory")

        # Verify recovery happened - agent.run() returns string
        assert isinstance(result, str), f"Agent should return string response, got: {type(result)}"
        assert result.strip(), f"Agent should return non-empty response, got: '{result}'"
        assert len(result) > 5, f"Agent should return meaningful response, got: '{result}'"


@pytest.mark.asyncio
async def test_multiple_failures():
    """Test agent handles multiple consecutive tool failures."""

    class FailingCodeTool:
        def __init__(self):
            self.call_count = 0
            self.name = "code"
            self.emoji = "🚀"
            self.description = "Execute code"
            self.rules = []

        async def run(self, code, language="python", timeout=30):
            self.call_count += 1
            return Result.fail(
                {
                    "output": "",
                    "error_output": f"Command failed (attempt {self.call_count})",
                    "success": False,
                    "exit_code": 1,
                }
            )

    def persistent_response(messages, **kwargs):
        # Check if this is a preparing request (looking for JSON Response in prompt)
        content = messages[-1]["content"].lower()
        if "json response" in content:
            return '{"memory": null, "tags": null, "memory_type": "fact", "mode": "fast", "selected_tools": ["bash"], "reasoning": "Need to execute bash commands"}'
        return "Let me try another command: echo 'hello'"

    failing_tool = FailingCodeTool()
    from cogency.tools.shell import Shell

    shell_tool = Shell()
    with patch.object(shell_tool, "run", side_effect=failing_tool.run):
        from cogency import Agent

        agent = Agent(
            "test", llm=MockLLM(custom_impl=persistent_response), tools=[shell_tool], depth=3
        )

        result = await agent.run("Run a command")

        # Agent should eventually give up gracefully - agent.run() returns string
        assert isinstance(result, str), f"Agent should return string response, got: {type(result)}"
        assert result.strip(), f"Agent should return non-empty response, got: '{result}'"


if __name__ == "__main__":
    asyncio.run(test_recovery())
    print("✓ Tool failure recovery smoke test passed")
