#!/usr/bin/env python3
"""Integration test for the adaptive reasoning node."""

import asyncio
from unittest.mock import MagicMock, AsyncMock
from cogency.nodes.react_loop import react_loop_node, _complexity_score
from cogency.utils.adaptive_reasoning import StoppingCriteria
from cogency.context import Context
from cogency.types import ExecutionTrace


class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    
    async def invoke(self, messages):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "I don't have enough information to provide a response."


class MockTool:
    """Mock tool for testing."""
    
    def __init__(self, name, response="Mock response"):
        self.name = name
        self.description = f"Mock tool {name}"
        self.response = response
        
    async def validate_and_run(self, **kwargs):
        return self.response


async def test_adaptive_reasoning_integration():
    """Test the adaptive reasoning integration with the main reason node."""
    print("🔗 Testing adaptive reasoning integration...")
    
    # Test 1: Direct response scenario
    print("  Testing direct response scenario...")
    context = Context("What is 2+2?")
    trace = ExecutionTrace()
    
    llm = MockLLM(["DIRECT_RESPONSE: 2+2 equals 4."])
    
    state = {
        "context": context,
        "trace": trace,
        "selected_tools": []
    }
    
    result = await react_loop_node(state, llm)
    
    assert result["reasoning_decision"].should_respond == True
    assert result["reasoning_decision"].task_complete == True
    assert "2+2 equals 4" in result["reasoning_decision"].response_text
    print("  ✅ Direct response scenario works")
    
    # Test 2: Query complexity estimation
    print("  Testing query complexity estimation...")
    
    simple_complexity = _complexity_score("What is Python?", 5)
    complex_complexity = _complexity_score(
        "Analyze and compare the performance implications of different machine learning frameworks", 
        15
    )
    
    assert simple_complexity < complex_complexity
    assert 0.1 <= simple_complexity <= 1.0
    assert 0.1 <= complex_complexity <= 1.0
    print("  ✅ Query complexity estimation works")
    
    # Test 3: Tool execution scenario
    print("  Testing tool execution scenario...")
    context = Context("Search for Python information")
    trace = ExecutionTrace()
    
    mock_tool = MockTool("search", "Python is a programming language")
    
    llm = MockLLM([
        "TOOL_NEEDED: search(query='Python information')",
        "Based on the search results, Python is a programming language."
    ])
    
    state = {
        "context": context,
        "trace": trace,
        "selected_tools": [mock_tool]
    }
    
    result = await react_loop_node(state, llm)
    
    assert result["reasoning_decision"].should_respond == True
    assert result["reasoning_decision"].task_complete == True
    assert "programming language" in result["reasoning_decision"].response_text
    print("  ✅ Tool execution scenario works")
    
    # Test 4: Trace logging verification
    print("  Testing trace logging...")
    
    trace_entries = [entry for entry in trace.entries if entry["node"] == "react_loop"]
    assert len(trace_entries) > 0
    
    # Should have adaptive reasoning traces
    adaptive_traces = [entry for entry in trace_entries if "Adaptive reasoning" in entry["message"]]
    assert len(adaptive_traces) > 0
    print("  ✅ Trace logging works")
    
    print("🎉 All adaptive reasoning integration tests passed!")


if __name__ == "__main__":
    asyncio.run(test_adaptive_reasoning_integration())