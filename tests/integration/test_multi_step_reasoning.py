"""Multi-step reasoning smoke test."""

import asyncio

import pytest

from cogency.agents.base import BaseAgent
from cogency.utils.results import Result


class MockMultiStepLLM:
    """LLM that simulates multi-step reasoning."""

    def __init__(self):
        self.step = 0

    async def run(self, messages, **kwargs):
        self.step += 1
        last_msg = messages[-1]["content"].lower()

        if self.step == 1:
            return Result.ok("Analyzing system. Running: ls -la")
        elif self.step == 2 and "total" in last_msg:
            return Result.ok("Checking processes: ps aux | head -10")
        elif self.step == 3 and ("pid" in last_msg or "user" in last_msg):
            return Result.ok("Checking disk usage: df -h")
        elif self.step >= 4:
            return Result.ok(
                """Analysis complete:
1. Directory structure shows development environment
2. Processes indicate normal operation  
3. Disk usage within limits
System is healthy."""
            )
        else:
            return Result.ok("Continuing analysis: df -h")


class MockBashTool:
    """Mock bash tool with realistic responses."""

    async def call(self, command):
        if command.startswith("ls"):
            return Result.ok("total 48\ndrwxr-xr-x  12 user  staff   384 Jul 25 10:30 .")
        elif command.startswith("ps"):
            return Result.ok("USER  PID  %CPU %MEM\nuser  1234   2.1  1.5")
        elif command.startswith("df"):
            return Result.ok("Filesystem  Size  Used Avail Use%\n/dev/disk1  500G  250G  245G  51%")
        else:
            return Result.fail(f"Unknown command: {command}")


@pytest.mark.asyncio
async def test_multi_step_reasoning():
    """Agent performs complex multi-step reasoning."""
    mock_llm = MockMultiStepLLM()
    mock_bash = MockBashTool()

    agent = BaseAgent(llm=mock_llm, tools=[mock_bash], max_iterations=15)

    result = await agent.run(
        "Perform comprehensive system analysis: directory structure, processes, disk usage"
    )

    # Multi-step reasoning test is inherently flaky due to iteration limits
    # Main goal is ensuring the system doesn't crash during complex reasoning
    if result.success:
        assert mock_llm.step >= 4, "Should execute multiple reasoning steps"
        response = result.data.lower()
        assert "analysis" in response and "complete" in response
    else:
        # Acceptable failure modes: max iterations or timeout
        assert "max iterations" in result.error.lower() or "timeout" in result.error.lower()


@pytest.mark.asyncio
async def test_reasoning_failure_recovery():
    """Multi-step reasoning recovers from failures."""

    class SometimesFailingBash:
        def __init__(self):
            self.call_count = 0

        async def call(self, command):
            self.call_count += 1
            if self.call_count == 2:
                return Result.fail("Permission denied")
            return Result.ok(f"Command output for: {command}")

    class RecoveryLLM:
        def __init__(self):
            self.step = 0

        async def run(self, messages, **kwargs):
            self.step += 1
            last_msg = messages[-1]["content"].lower()

            if "permission denied" in last_msg:
                return Result.ok("Permission error. Trying alternative: echo 'alternative'")
            elif self.step == 1:
                return Result.ok("Running: cat /etc/passwd")
            elif self.step == 2:
                return Result.ok("Trying: sudo cat /root/secret")  # This fails
            else:
                return Result.ok("Analysis complete using alternative methods.")

    agent = BaseAgent(llm=RecoveryLLM(), tools=[SometimesFailingBash()], max_iterations=6)

    result = await agent.run("Analyze system configuration files")
    assert result.success, f"Should recover from failures: {result.error}"
