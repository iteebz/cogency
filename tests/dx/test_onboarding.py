#!/usr/bin/env python3
"""Developer experience tests for onboarding, error clarity, and setup."""

import asyncio
import os
import tempfile
from pathlib import Path
from cogency import Agent
from cogency.memory.filesystem import FSMemory
from cogency.tools.calculator import CalculatorTool


class TestDeveloperExperience:
    """Tests focused on developer experience and onboarding."""

    async def test_minimal_agent_creation(self):
        """Test the simplest possible agent creation (3-line DX)."""
        try:
            # This should work with minimal setup
            agent = Agent("test_assistant")
            assert agent is not None
            print("✅ Minimal agent creation works")
        except Exception as e:
            print(f"❌ Minimal agent creation failed: {e}")
            raise

    async def test_agent_with_tools(self):
        """Test agent creation with tools."""
        try:
            agent = Agent("calculator_assistant", tools=[CalculatorTool()])
            assert agent is not None
            assert len(agent.tools) == 1
            print("✅ Agent with tools creation works")
        except Exception as e:
            print(f"❌ Agent with tools creation failed: {e}")
            raise

    async def test_agent_with_memory(self):
        """Test agent creation with memory."""
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                memory = FSMemory(tmp_dir)
                agent = Agent("memory_assistant", memory=memory)
                assert agent is not None
                assert agent.memory is not None
                print("✅ Agent with memory creation works")
        except Exception as e:
            print(f"❌ Agent with memory creation failed: {e}")
            raise

    async def test_output_modes(self):
        """Test all output modes work correctly."""
        agent = Agent("mode_test")
        query = "What is 2 + 2?"
        
        modes = ["summary", "trace", "raw"]
        for mode in modes:
            try:
                result = await agent.run(query, mode=mode)
                assert result is not None
                print(f"✅ Output mode '{mode}' works")
            except Exception as e:
                print(f"❌ Output mode '{mode}' failed: {e}")
                raise

    async def test_error_handling_missing_env(self):
        """Test error handling when environment is not properly configured."""
        # Save original env vars
        original_api_key = os.environ.get("ANTHROPIC_API_KEY")
        original_openai_key = os.environ.get("OPENAI_API_KEY")
        
        try:
            # Remove API keys to test error handling
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            
            # This should fail gracefully with clear error message
            try:
                agent = Agent("test_no_env")
                result = await agent.run("Test query")
                # If we get here, fallback worked
                print("✅ Graceful fallback when no API keys")
            except Exception as e:
                # Should get clear error message
                error_msg = str(e).lower()
                if any(word in error_msg for word in ["api", "key", "credential", "auth"]):
                    print("✅ Clear error message for missing credentials")
                else:
                    print(f"❌ Unclear error message: {e}")
                    raise
                
        finally:
            # Restore original env vars
            if original_api_key:
                os.environ["ANTHROPIC_API_KEY"] = original_api_key
            if original_openai_key:
                os.environ["OPENAI_API_KEY"] = original_openai_key

    async def test_memory_auto_creation(self):
        """Test that memory directories are created automatically."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_path = Path(tmp_dir) / "test_memory"
            
            # Memory directory shouldn't exist initially
            assert not memory_path.exists()
            
            # Creating FSMemory should auto-create directory
            memory = FSMemory(str(memory_path))
            assert memory_path.exists()
            
            print("✅ Memory directory auto-creation works")

    async def test_tool_error_handling(self):
        """Test error handling in tool execution."""
        agent = Agent("error_test", tools=[CalculatorTool()])
        
        # Test invalid calculation
        try:
            result = await agent.run("Calculate 1 divided by 0")
            # Should handle gracefully
            assert result is not None
            print("✅ Tool error handling works")
        except Exception as e:
            print(f"❌ Tool error not handled gracefully: {e}")
            raise

    async def test_setup_validation(self):
        """Test that setup can be validated easily."""
        try:
            # Test basic agent functionality
            agent = Agent("setup_test")
            result = await agent.run("Say hello")
            assert result is not None
            assert len(str(result)) > 0
            print("✅ Basic setup validation works")
        except Exception as e:
            print(f"❌ Setup validation failed: {e}")
            raise

    async def test_concurrent_agent_usage(self):
        """Test that multiple agents can be used concurrently."""
        agent1 = Agent("concurrent_1")
        agent2 = Agent("concurrent_2")
        
        # Run concurrent tasks
        tasks = [
            agent1.run("Count to 3"),
            agent2.run("Count to 5")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Both should complete successfully
        assert len(results) == 2
        assert all(r is not None and not isinstance(r, Exception) for r in results)
        print("✅ Concurrent agent usage works")


async def run_dx_tests():
    """Run all developer experience tests."""
    test_suite = TestDeveloperExperience()
    
    print("👨‍💻 Testing developer experience...")
    
    # Run tests
    await test_suite.test_minimal_agent_creation()
    await test_suite.test_agent_with_tools()
    await test_suite.test_agent_with_memory()
    await test_suite.test_output_modes()
    await test_suite.test_error_handling_missing_env()
    await test_suite.test_memory_auto_creation()
    await test_suite.test_tool_error_handling()
    await test_suite.test_setup_validation()
    await test_suite.test_concurrent_agent_usage()
    
    print("\n🎉 All developer experience tests passed!")


if __name__ == "__main__":
    asyncio.run(run_dx_tests())