"""Smoke test: Multi-step reasoning with Result pattern."""

import asyncio

import pytest
from resilient_result import Result


class MockMultiStepProvider:
    """Mock provider that simulates complex multi-step reasoning."""

    def __init__(self):
        self.step = 0

    async def run(self, messages, **kwargs):
        self.step += 1
        last_msg = messages[-1]["content"].lower()

        if self.step == 1:
            # Initial analysis
            return Result.ok(
                "I need to analyze the system first. Let me check the current directory structure: ls -la"
            )

        if self.step == 2 and "total" in last_msg:
            # Got directory listing, now check processes
            return Result.ok(
                "Good, I can see the directory structure. Now let me check running processes: ps aux | head -10"
            )

        if self.step == 3 and ("pid" in last_msg or "user" in last_msg):
            # Got process info, now check disk usage
            return Result.ok(
                "I can see the processes. Now let me check disk usage to complete the analysis: df -h"
            )

        if self.step >= 4 and (
            "filesystem" in last_msg or "available" in last_msg or "size" in last_msg
        ):
            # Final synthesis
            return Result.ok(
                """Based on my multi-step analysis:
1. Directory structure shows active development environment
2. Process list indicates normal system operation
3. Disk usage is within acceptable limits
Analysis complete - system is healthy."""
            )

        if self.step >= 4:
            # Force completion after 4 steps
            return Result.ok("Analysis complete based on available information.")

        # Fallback - continue analysis
        return Result.ok("Continuing analysis. Let me check the disk usage: df -h")


class MockBashTool:
    """Mock bash tool that returns realistic system info."""

    async def call(self, command):
        if command.startswith("ls"):
            return Result.ok(
                """total 48
drwxr-xr-x  12 user  staff   384 Jul 25 10:30 .
drwxr-xr-x   6 user  staff   192 Jul 24 15:20 ..
-rw-r--r--   1 user  staff  1234 Jul 25 09:15 README.md
-rw-r--r--   1 user  staff   567 Jul 25 10:30 pyproject.toml
drwxr-xr-x   8 user  staff   256 Jul 25 09:45 src"""
            )

        if command.startswith("ps"):
            return Result.ok(
                """USER       PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user      1234   2.1  1.5  4567890  12345   ??  S    10:30AM   0:00.45 python
user      5678   0.8  0.3  2345678   5432   ??  S    10:31AM   0:00.12 bash
user      9999   0.0  0.1   987654   1234   ??  S    10:32AM   0:00.01 ls"""
            )

        if command.startswith("df"):
            return Result.ok(
                """Filesystem      Size  Used Avail Use% Mounted on
/dev/disk1      500G  250G  245G  51% /
/dev/disk2      1.0T  600G  400G  60% /Users
tmpfs           8.0G  1.2G  6.8G  15% /tmp"""
            )

        return Result.fail(f"Unknown command: {command}")


# Mock agent that uses the real BaseAgent pattern but without fixture dependency
class TestAgent:
    """Test agent for integration tests - no fixture dependencies."""

    def __init__(self, llm=None, tools=None, max_iterations=10):
        self.llm = llm
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.messages = []

    async def run_async(self, prompt: str) -> Result:
        """Run agent with basic tool calling logic."""
        self.messages = [{"role": "user", "content": prompt}]

        for _iteration in range(self.max_iterations):
            result = await self.llm.run(self.messages)
            if not result.success:
                return Result.fail(f"Provider failed: {result.error}")

            response = result.data
            self.messages.append({"role": "assistant", "content": response})

            # Check if response wants to use tools
            if (
                any(
                    tool_name in response.lower() for tool_name in ["ls", "cat", "ps", "df", "echo"]
                )
                and self.tools
            ):
                command = self._extract_command(response)
                if command:
                    tool_result = await self.tools[0].call(command)
                    if tool_result.success:
                        self.messages.append(
                            {"role": "user", "content": f"Tool output: {tool_result.data}"}
                        )
                    else:
                        self.messages.append(
                            {
                                "role": "user",
                                "content": f"Tool error: {tool_result.error}. Please try a different approach.",
                            }
                        )
                    continue

            return Result.ok(response)

        return Result.fail("Max iterations reached")

    def _extract_command(self, response: str) -> str:
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if any(cmd in line for cmd in ["ls", "cat", "ps", "df", "echo"]):
                return line.split(":")[-1].strip() if ":" in line else line
        return ""


@pytest.mark.asyncio
async def test_multi_step():
    """Test agent can perform complex multi-step reasoning tasks."""

    # Setup mocks
    mock_provider = MockMultiStepProvider()
    mock_bash = MockBashTool()

    # Create agent
    agent = TestAgent(llm=mock_provider, tools=[mock_bash], max_iterations=8)

    # Run complex analysis task
    result = await agent.run_async(
        "Perform a comprehensive system analysis including directory structure, running processes, and disk usage"
    )

    # Verify multi-step execution succeeded
    assert result.success, f"Multi-step reasoning should succeed: {result.error}"
    assert mock_provider.step >= 4, "Should execute multiple reasoning steps"

    # Verify final result indicates completion
    final_response = result.data.lower()
    assert "analysis" in final_response and "complete" in final_response


@pytest.mark.asyncio
async def test_with_failures():
    """Test multi-step reasoning recovers from intermediate failures."""

    class SometimesFailingBash:
        def __init__(self):
            self.call_count = 0

        async def call(self, command):
            self.call_count += 1

            if self.call_count == 2:  # Second call fails
                return Result.fail("Permission denied")
            return Result.ok(f"Command output for: {command}")

    class RecoveryProvider:
        def __init__(self):
            self.step = 0

        async def run(self, messages, **kwargs):
            self.step += 1
            last_msg = messages[-1]["content"].lower()

            if "permission denied" in last_msg:
                return Result.ok(
                    "I see there was a permission error. Let me try a different approach: echo 'alternative method'"
                )
            if self.step == 1:
                return Result.ok("First, let me run: cat /etc/passwd")
            if self.step == 2:
                return Result.ok("Now let me try: sudo cat /root/secret")  # This will fail
            return Result.ok("Analysis complete using alternative methods.")

    agent = TestAgent(llm=RecoveryProvider(), tools=[SometimesFailingBash()], max_iterations=6)

    result = await agent.run_async("Analyze system configuration files")

    # Should recover and complete successfully
    assert result.success, f"Should recover from intermediate failures: {result.error}"


if __name__ == "__main__":
    asyncio.run(test_multi_step())
    print("✓ Multi-step reasoning smoke test passed")
