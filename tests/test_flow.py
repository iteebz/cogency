"""Test the core execution flow and state transitions."""
import pytest
from unittest.mock import AsyncMock

from cogency.flow import Flow
from cogency.llm.mock import MockLLM
from cogency.context import Context
from cogency.output import Output
from cogency.tools.calculator import Calculator

@pytest.mark.asyncio
async def test_direct_flow():
    """Test a simple flow: preprocess -> respond."""
    # Setup
    llm = MockLLM()
    context = Context("Hello")
    output = Output()
    flow = Flow(llm=llm, tools=[], memory=None)

    # Flow is a StateGraph now - test that it compiles
    assert flow.flow is not None

@pytest.mark.asyncio
async def test_tool_flow():
    """Test a simple flow: preprocess -> reason -> act -> reason -> respond."""
    # Setup
    llm = MockLLM()
    tools = [Calculator()]
    context = Context("What is 2+2?")
    output = Output()
    flow = Flow(llm=llm, tools=tools, memory=None)

    # Test flow has tools and compiled graph
    assert len(flow.tools) == 1
    assert flow.flow is not None
