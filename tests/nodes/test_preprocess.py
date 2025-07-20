#!/usr/bin/env python3
"""Test preprocess node functionality."""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from cogency.nodes.preprocess import preprocess_node
from cogency.types import AgentState
from cogency.tools.recall import Recall
from cogency.tools.calculator import Calculator


class MockLLM:
    async def invoke(self, messages):
        # Mock response based on the query
        query = messages[0]["content"]
        
        if "Python" in query and "OpenAI" in query:
            return '{"memory": "User likes Python and works at OpenAI", "tags": ["programming", "work"], "memory_type": "fact", "respond_directly": false, "selected_tools": ["recall"], "reasoning": "User shared personal info, need recall for future context"}'
        elif "what is my favorite" in query.lower():
            return '{"memory": null, "tags": null, "memory_type": "fact", "respond_directly": false, "selected_tools": ["recall"], "reasoning": "Personal question needs memory lookup"}'
        elif "2 + 2" in query:
            return '{"memory": null, "tags": null, "memory_type": "fact", "respond_directly": false, "selected_tools": ["calculator"], "reasoning": "Simple math needs calculator"}'
        else:
            return '{"memory": null, "tags": null, "memory_type": "fact", "respond_directly": true, "selected_tools": [], "reasoning": "General knowledge"}'


class MockMemory:
    async def create(self, *args, **kwargs):
        return Mock()


class MockContext:
    user_id = "test_user"


@pytest.mark.asyncio
async def test_memory_extraction():
    """Test that memory is extracted for personal info."""
    state = AgentState({
        "query": "My favorite programming language is Python and I work at OpenAI",
        "context": MockContext()
    })
    
    mock_tools = [
        Recall(MockMemory()),
        Calculator()
    ]
    
    result = await preprocess_node(
        state,
        llm=MockLLM(),
        tools=mock_tools,
        memory=MockMemory()
    )
    
    assert result['next_node'] == 'reason'
    assert any(t.name == 'recall' for t in result['selected_tools'])


@pytest.mark.asyncio
async def test_recall_usage():
    """Test that recall is selected for personal questions."""
    state = AgentState({
        "query": "What is my favorite programming language?",
        "context": MockContext()
    })
    
    mock_tools = [
        Recall(MockMemory()),
        Calculator()
    ]
    
    result = await preprocess_node(
        state,
        llm=MockLLM(),
        tools=mock_tools,
        memory=MockMemory()
    )
    
    # Should use ReAct workflow and include recall
    assert result['next_node'] == 'reason'
    assert any(t.name == 'recall' for t in result['selected_tools'])


@pytest.mark.asyncio
async def test_calculator_selection():
    """Test that calculator is selected for math."""
    state = AgentState({
        "query": "What is 2 + 2?",
        "context": MockContext()
    })
    
    mock_tools = [
        Recall(MockMemory()),
        Calculator()
    ]
    
    result = await preprocess_node(
        state,
        llm=MockLLM(),
        tools=mock_tools,
        memory=MockMemory()
    )
    
    # Should use ReAct workflow with calculator
    assert result['next_node'] == 'reason'
    assert any(t.name == 'calculator' for t in result['selected_tools'])


@pytest.mark.asyncio
async def test_direct_response():
    """Test direct response for general knowledge."""
    state = AgentState({
        "query": "What is the capital of France?",
        "context": MockContext()
    })
    
    mock_tools = [
        Recall(MockMemory()),
        Calculator()
    ]
    
    result = await preprocess_node(
        state,
        llm=MockLLM(),
        tools=mock_tools,
        memory=MockMemory()
    )
    
    # Should respond directly for general knowledge
    assert result['next_node'] == 'respond'
    assert result['max_iterations'] == 5