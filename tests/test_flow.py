"""Test the core execution flow and state transitions."""
import pytest
from unittest.mock import AsyncMock

from cogency.flow import Flow
from cogency.llm.mock import MockLLM
from cogency.context import Context
from cogency.output import Output
from cogency.tools.calculator import Calculator

@pytest.mark.asyncio
async def test_direct_response_flow():
    """Test a simple flow: preprocess -> respond."""
    # Setup
    llm = MockLLM()
    context = Context("Hello")
    output = Output()
    flow = Flow(llm=llm, tools=[], memory=None, output=output)

    # Mock LLM responses for each node
    # 1. Preprocess -> respond directly
    # 2. Respond -> generate final answer
    llm.add_response('{"respond_directly": true, "reasoning": "Simple greeting"}')
    llm.add_response("Hello there! How can I help you?")

    # Execute
    final_result = await flow.execute("Hello")

    # Verify
    assert final_result == "Hello there! How can I help you?"
    assert llm.call_count == 2

@pytest.mark.asyncio
async def test_tool_use_flow():
    """Test a simple flow: preprocess -> reason -> act -> reason -> respond."""
    # Setup
    llm = MockLLM()
    tools = [Calculator()]
    context = Context("What is 2+2?")
    output = Output()
    flow = Flow(llm=llm, tools=tools, memory=None)

    # Mock LLM responses for each node
    # 1. Preprocess -> needs to reason
    llm.add_response('{"respond_directly": false, "react_mode": "fast", "selected_tools": ["calculator"]}')
    # 2. Reason -> needs to use calculator
    llm.add_response('{"reasoning": "I need to calculate 2+2", "tool_calls": [{"name": "calculator", "args": {"expression": "2+2"}}]}')
    # 3. Reason (after act) -> got tool result, can now answer
    llm.add_response('{"reasoning": "The calculation is complete, I can answer now."}')
    # 4. Respond -> generate final answer
    llm.add_response("The answer is 4.")

    # Execute
    final_result = await flow.execute("What is 2+2?")

    # Verify
    assert final_result == "The answer is 4."
    assert llm.call_count == 4
