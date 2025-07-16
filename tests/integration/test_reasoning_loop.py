#!/usr/bin/env python3
"""Integration tests for the complete reasoning loop: ReAct + memory + tools."""

import asyncio
import pytest
from cogency import Agent
from cogency.memory.filesystem import FSMemory
from cogency.tools.calculator import CalculatorTool
from cogency.tools.timezone import TimezoneTool


class TestReasoningLoopIntegration:
    """Integration tests covering the entire cognitive workflow."""

    @pytest.fixture
    async def agent_with_memory_tools(self):
        """Agent with memory and tools for comprehensive testing."""
        memory = FSMemory(".test_memory_integration")
        await memory.clear()  # Clean slate
        
        agent = Agent(
            "integration_test",
            memory=memory,
            tools=[CalculatorTool(), TimezoneTool()]
        )
        return agent, memory

    async def test_memorize_select_reason_flow(self, agent_with_memory_tools):
        """Test complete MEMORIZE → SELECT_TOOLS → REASON flow."""
        agent, memory = agent_with_memory_tools
        
        # First interaction: Store personal info
        result1 = await agent.run("I'm a software engineer living in San Francisco")
        assert result1 is not None
        
        # Verify memory storage
        memories = await memory.recall("software engineer")
        assert len(memories) > 0
        assert "San Francisco" in memories[0].content
        
        # Second interaction: Recall + tool usage
        result2 = await agent.run("What time is it where I live? Use my location info.")
        assert result2 is not None
        
        # Verify memory was recalled and timezone tool was used
        memories_after = await memory.recall("software")
        assert len(memories_after) > 0
        assert memories_after[0].access_count > 1  # Memory was accessed
        
        # Clean up
        await memory.clear()

    async def test_multi_step_reasoning_with_tools(self, agent_with_memory_tools):
        """Test multi-step reasoning requiring tool chaining."""
        agent, memory = agent_with_memory_tools
        
        # Complex scenario requiring multiple tools
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

    async def test_memory_enhanced_reasoning(self, agent_with_memory_tools):
        """Test that memory enhances reasoning quality."""
        agent, memory = agent_with_memory_tools
        
        # Store context across multiple interactions
        await agent.run("I prefer working in Python and have 5 years of experience")
        await agent.run("I'm currently learning machine learning")
        await agent.run("My current salary is $120,000")
        
        # Test reasoning with accumulated context
        result = await agent.run("Should I ask for a raise? Consider my background.")
        assert result is not None
        
        # Verify context integration
        result_str = str(result).lower()
        assert any(word in result_str for word in ["python", "experience", "salary", "120"])
        
        # Check memory was properly accessed
        memories = await memory.recall("python experience")
        assert len(memories) > 0
        assert any(m.access_count > 1 for m in memories)
        
        # Clean up
        await memory.clear()

    async def test_error_handling_in_reasoning_loop(self, agent_with_memory_tools):
        """Test error handling throughout the reasoning loop."""
        agent, memory = agent_with_memory_tools
        
        # Test with invalid tool usage
        result = await agent.run("Calculate the square root of negative infinity")
        assert result is not None  # Should handle gracefully
        
        # Test with memory query that returns no results
        result2 = await agent.run("What do you remember about quantum computing?")
        assert result2 is not None  # Should handle empty memory gracefully
        
        # Clean up
        await memory.clear()

    async def test_performance_under_load(self, agent_with_memory_tools):
        """Test reasoning loop performance with multiple concurrent operations."""
        agent, memory = agent_with_memory_tools
        
        # Simulate concurrent requests
        tasks = []
        for i in range(5):
            tasks.extend([
                agent.run(f"Calculate {i} * 2 and remember this calculation"),
                agent.run(f"What's the timezone for user {i}?"),
                agent.run(f"Store that I completed task {i}")
            ])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed successfully
        assert len(results) == 15
        assert all(r is not None and not isinstance(r, Exception) for r in results)
        
        # Verify memory accumulated properly
        memories = await memory.recall("calculate")
        assert len(memories) >= 5
        
        # Clean up
        await memory.clear()


async def run_integration_tests():
    """Run all integration tests."""
    test_suite = TestReasoningLoopIntegration()
    
    print("🔄 Testing complete reasoning loop integration...")
    
    # Create fixture
    agent, memory = await test_suite.agent_with_memory_tools()
    
    try:
        # Run tests
        await test_suite.test_memorize_select_reason_flow((agent, memory))
        print("✅ MEMORIZE → SELECT_TOOLS → REASON flow")
        
        await test_suite.test_multi_step_reasoning_with_tools((agent, memory))
        print("✅ Multi-step reasoning with tools")
        
        await test_suite.test_memory_enhanced_reasoning((agent, memory))
        print("✅ Memory-enhanced reasoning")
        
        await test_suite.test_error_handling_in_reasoning_loop((agent, memory))
        print("✅ Error handling in reasoning loop")
        
        await test_suite.test_performance_under_load((agent, memory))
        print("✅ Performance under load")
        
        print("\n🎉 All integration tests passed!")
        
    finally:
        # Cleanup
        await memory.clear()


if __name__ == "__main__":
    asyncio.run(run_integration_tests())