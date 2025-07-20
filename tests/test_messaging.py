"""Tests for messaging system - core business logic only."""
import pytest
from unittest.mock import AsyncMock

from cogency.messaging import (
    format_tool_params,
    contextualize_result,
    should_show_reasoning,
    AgentMessenger
)


def test_parameter_formatting():
    """Test key parameter formatting cases."""
    # Weather
    assert format_tool_params("weather", {"city": "Tokyo"}) == "(Tokyo)"
    
    # Calculator
    assert format_tool_params("calculator", {"operation": "multiply", "x1": 120, "x2": 3}) == "(120 × 3)"
    
    # Search truncation
    long_query = "this is a very long search query that should be truncated"
    result = format_tool_params("search", {"query": long_query})
    assert "..." in result and len(result) < 50
    
    # Empty params
    assert format_tool_params("any_tool", {}) == ""


def test_result_contextualization():
    """Test key result formatting cases."""
    # Weather
    assert contextualize_result("weather", {"temperature": "25°C", "condition": "sunny"}) == "25°C sunny"
    
    # Calculator
    assert contextualize_result("calculator", {"result": 360}) == "360"
    
    # Search
    assert contextualize_result("search", {"results_count": 12}) == "12 results"
    assert contextualize_result("search", {"results_count": 1}) == "1 result"
    
    # HTTP status
    assert contextualize_result("http", {"status_code": 200}) == "✓ 200"
    assert contextualize_result("http", {"status_code": 404}) == "✗ 404"
    
    # Fallbacks
    assert contextualize_result("any_tool", None) == "completed"


def test_reasoning_intelligence():
    """Test reasoning filtering logic."""
    # Should skip obvious patterns
    assert should_show_reasoning("I need to use the weather tool") is False
    assert should_show_reasoning("User wants information") is False
    
    # Should show valuable reasoning
    assert should_show_reasoning("Rain first 2 days means indoor activities") is True
    assert should_show_reasoning("Need to filter by salary - most listings don't show pay") is True
    
    # Edge cases
    assert should_show_reasoning("") is False
    assert should_show_reasoning("short") is False


@pytest.mark.asyncio
async def test_tool_execution_messaging():
    """Test core tool execution flow."""
    callback = AsyncMock()
    
    # Success case
    await AgentMessenger.tool_execution(
        callback, "weather", {"city": "Tokyo"}, 
        {"temperature": "25°C", "condition": "sunny"}, success=True
    )
    
    call_args = callback.call_args[0][0]
    assert "Tokyo" in call_args and "25°C sunny" in call_args and "→" in call_args
    
    callback.reset_mock()
    
    # Failure case
    await AgentMessenger.tool_execution(
        callback, "weather", {"city": "Atlantis"}, 
        "City not found", success=False
    )
    
    call_args = callback.call_args[0][0]
    assert "❌" in call_args and "City not found" in call_args