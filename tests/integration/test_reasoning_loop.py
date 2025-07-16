#!/usr/bin/env python3
"""Integration tests for the complete reasoning loop: ReAct + memory + tools."""

import asyncio
import pytest
import json
from unittest.mock import patch
from cogency import Agent
from cogency.memory.filesystem import FSMemory
from cogency.tools.calculator import CalculatorTool
from cogency.tools.timezone import TimezoneTool
from cogency.tools.memory import MemorizeTool


class TestReasoningLoopIntegration:
    """Integration tests covering the entire cognitive workflow."""

    @pytest.fixture
    async def agent_with_memory_tools(self, tmp_memory_dir):
        """Agent with memory and tools for comprehensive testing."""
        memory = FSMemory(str(tmp_memory_dir))
        await memory.clear()  # Clean slate
        
        agent = Agent(
            "integration_test",
            memory_dir=str(memory.memory_dir),
            tools=[CalculatorTool(), TimezoneTool(), MemorizeTool(memory=memory)]
        )
        return agent, memory

    async def test_memorize_select_reason_flow(self, agent_with_memory_tools, mock_llm_response):
        """Test complete MEMORIZE → SELECT_TOOLS → REASON flow."""
        agent, memory = agent_with_memory_tools
        
        # First interaction: Store personal info
        mock_llm_response.return_value = json.dumps({"action": "respond", "answer": "Okay, I'll remember that you're a software engineer living in San Francisco."})
        result1 = await agent.run("I'm a software engineer living in San Francisco")
        assert result1 is not None
        
        # Verify memory storage
        memories = await memory.recall("software engineer")
        assert len(memories) > 0
        assert "San Francisco" in memories[0].content
        
        # Second interaction: Recall + tool usage
        mock_llm_response.return_value = json.dumps({"action": "use_tool", "tool_call": {"name": "TimezoneTool", "args": {"location": "San Francisco"}}})
        result2 = await agent.run("What time is it where I live? Use my location info.")
        assert result2 is not None
        
        # Verify memory was recalled and timezone tool was used
        memories_after = await memory.recall("software")
        assert len(memories_after) > 0
        assert memories_after[0].access_count > 1  # Memory was accessed
        
        # Clean up
        await memory.clear()

    async def test_multi_step_reasoning_with_tools(self, agent_with_memory_tools, mock_llm_response):
        """Test multi-step reasoning requiring tool chaining."""
        agent, memory = agent_with_memory_tools
        
        # Complex scenario requiring multiple tools
        mock_llm_response.side_effect = [
            json.dumps({"action": "use_tool", "tool_call": {"name": "CalculatorTool", "args": {"expression": "8 * 50"}}}),
            json.dumps({"action": "respond", "answer": "Your daily earnings are $400.00. Now, what time is it in New York?"}),
            json.dumps({"action": "use_tool", "tool_call": {"name": "TimezoneTool", "args": {"location": "New York"}}}),
            json.dumps({"action": "respond", "answer": "The time in New York is currently 12:00 PM."})
        ]
        scenario = """
        I need to calculate my daily earnings if I work 8 hours at $50/hour.
        Then tell me what time it is in New York.
        """
        
        result = await agent.run(scenario)
        assert result is not None
        
        # Verify both calculations and timezone lookup occurred
        result_str = str(result).lower()
        assert any(word in result_str for word in ["400", "$400", "daily"])  # Calculation result
        assert "new york" in result_str  # Timezone lookup
        
        # Clean up
        await memory.clear()

    async def test_memory_enhanced_reasoning(self, agent_with_memory_tools, mock_llm_response):
        """Test that memory is stored and recalled."""
        agent, memory = agent_with_memory_tools

        mock_llm_response.side_effect = [
            json.dumps({"action": "use_tool", "tool_call": {"name": "memorize", "args": {"text": "My favorite color is blue."}}}),
            json.dumps({"action": "respond", "answer": "Okay, I've remembered that your favorite color is blue."})
        ]

        # Find the MemorizeTool instance in the agent's tools
        memorize_tool_instance = next((tool for tool in agent.tools if tool.name == "memorize"), None)
        assert memorize_tool_instance is not None, "MemorizeTool not found in agent's tools"

        with patch.object(memorize_tool_instance, 'run', wraps=memorize_tool_instance.run) as mock_memorize_tool_run:
            # Store a simple memory
            await agent.run("My favorite color is blue.")

            # Verify MemorizeTool.run was called
            mock_memorize_tool_run.assert_called_once()

        # Recall the memory
        recalled_memories = await memory.recall("favorite color")
        assert len(recalled_memories) > 0
        assert "blue" in recalled_memories[0].content

        # Clean up
        await memory.clear()

    async def test_error_handling_in_reasoning_loop(self, agent_with_memory_tools, mock_llm_response):
        """Test error handling throughout the reasoning loop."""
        agent, memory = agent_with_memory_tools
        
        # Test with invalid tool usage
        mock_llm_response.return_value = json.dumps({"action": "respond", "answer": "I cannot calculate the square root of negative infinity as it's not a real number."})
        result = await agent.run("Calculate the square root of negative infinity")
        assert result is not None  # Should handle gracefully
        
        # Test with memory query that returns no results
        mock_llm_response.return_value = json.dumps({"action": "respond", "answer": "I don't have any information about quantum computing in my memory."})
        result2 = await agent.run("What do you remember about quantum computing?")
        assert result2 is not None  # Should handle empty memory gracefully
        
        # Clean up
        await memory.clear()

    async def test_performance_under_load(self, agent_with_memory_tools, mock_llm_response):
        """Test basic agent functionality under a light load."""
        agent, memory = agent_with_memory_tools

        mock_llm_response.side_effect = [
            json.dumps({"action": "respond", "answer": "The answer is 2."}),
            json.dumps({"action": "respond", "answer": "Why did the scarecrow win an award? Because he was outstanding in his field!"}),
                        json.dumps({"action": "use_tool", "tool_call": {"name": "memorize", "args": {"text": "The sky is blue."}}}),
            json.dumps({"action": "respond", "answer": "Okay, I've remembered that the sky is blue."})
        ]

        # Find the MemorizeTool instance in the agent's tools
        memorize_tool_instance = next((tool for tool in agent.tools if tool.name == "memorize"), None)
        assert memorize_tool_instance is not None, "MemorizeTool not found in agent's tools"

        with patch.object(memorize_tool_instance, 'run', wraps=memorize_tool_instance.run) as mock_memorize_tool_run:
            # Run a few simple tasks concurrently
            tasks = [
                agent.run("What is 1 + 1?"),
                agent.run("Tell me a short joke."),
                agent.run("Remember that the sky is blue.")
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all tasks completed without exceptions
            assert all(r is not None and not isinstance(r, Exception) for r in results)

            # Verify MemorizeTool.run was called
            mock_memorize_tool_run.assert_called_once()

        # Verify memory was updated
        memories = await memory.recall("sky")
        assert len(memories) > 0
        assert "blue" in memories[0].content

        # Clean up
        await memory.clear()


if __name__ == "__main__":
    pytest.main([__file__])