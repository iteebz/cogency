"""Agent mock fixtures for testing."""

import pytest
from resilient_result import Result


class BaseAgent:
    """Minimal agent for smoke test validation."""

    def __init__(self, llm=None, tools=None, depth=10):
        self.llm = llm
        self.tools = tools or []
        self.depth = depth
        self.messages = []

    async def run(self, prompt: str) -> Result:
        """Run agent with basic tool calling logic."""
        self.messages = [{"role": "user", "content": prompt}]
        for _iteration in range(self.depth):
            llm_result = await self.llm.run(self.messages)
            if not llm_result.success:
                return Result.fail(f"LLM failed: {llm_result.error}")
            response = llm_result.data
            self.messages.append({"role": "assistant", "content": response})
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


@pytest.fixture
def base_agent():
    """Minimal BaseAgent for smoke tests (fixture)."""
    return BaseAgent
