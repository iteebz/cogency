"""Agent mock fixtures for testing."""

import pytest
from resilient_result import Result


class BaseAgent:
    """Minimal agent for smoke test validation."""

    def __init__(self, llm=None, embed=None, tools=None, max_iterations=10):
        self.llm = llm
        self.embed = embed
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.messages = []

    async def run_old_api(self, prompt: str) -> Result:
        """Run agent with basic tool calling logic."""
        self.messages = [{"role": "user", "content": prompt}]
        for _iteration in range(self.max_iterations):
            result = await self.llm.run(self.messages)
            if not result.success:
                return Result.fail(f"Provider failed: {result.error}")
            response = result.unwrap()
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
                            {"role": "user", "content": f"Tool output: {tool_result.unwrap()}"}
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

    async def run(self, prompt: str) -> tuple[str, str]:
        """New agent API - returns (response, conversation_id)."""
        result = await self.run_old_api(prompt)
        if result.success:
            return result.unwrap(), "test_conversation_id"
        return f"Error: {result.error}", "test_conversation_id"

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
