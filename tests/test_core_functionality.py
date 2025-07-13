import pytest

from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools import CalculatorTool, FileManagerTool, WebSearchTool, list_available_tools


def test_tool_discovery():
    tools = list_available_tools()
    expected_tools = ["calculator", "web_search", "file_manager"]
    for tool in expected_tools:
        assert tool in tools, f"Missing tool: {tool}"


def test_tool_instantiation():
    CalculatorTool()
    WebSearchTool()
    FileManagerTool()


@pytest.mark.asyncio
async def test_calculator_tool():
    calc = CalculatorTool()
    result = await calc.run(operation="add", x1=5, x2=3)
    assert result.get("result") == 8, f"Calculator addition failed: {result}"

    result = await calc.run(operation="invalid")
    assert "error" in result, f"Calculator error handling failed: {result}"


@pytest.mark.asyncio
async def test_web_search_tool():
    web = WebSearchTool()
    result = await web.run(query="")
    assert "error" in result, f"Web search error handling failed: {result}"

    # Test basic search (without API key, should still validate input)
    result = await web.run(query="test query", max_results=3)
    assert "error" in result or "results" in result, (
        f"Web search basic functionality failed: {result}"
    )


def test_agent_without_llm():
    # This will fail on run() without API key, but should create successfully
    agent = Agent(
        name="TestAgent",
        llm=GeminiLLM(api_keys="fake-key"),
        tools=[CalculatorTool(), WebSearchTool()],
    )
    assert agent is not None, "Agent creation failed"
