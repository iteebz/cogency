#!/usr/bin/env python3
"""Test the clean Agent API with trace and verbose flags."""
import asyncio
from cogency import Agent
from cogency.llm.mock import MockLLM

async def test_clean_api():
    """Test the beautiful new API."""
    print("🧪 Testing Clean Agent API")
    
    # Use mock LLM for testing
    mock_llm = MockLLM()
    
    # Test 1: Basic agent with verbose output
    print("\n1. Basic agent (verbose=True, trace=False)")
    agent = Agent("test", verbose=True, trace=False, llm=mock_llm)
    
    # Test 2: Agent with tracing enabled
    print("\n2. Agent with tracing (verbose=True, trace=True)")
    trace_agent = Agent("trace_test", verbose=True, trace=True, llm=mock_llm)
    
    # Test 3: Silent agent
    print("\n3. Silent agent (verbose=False, trace=False)")
    silent_agent = Agent("silent", verbose=False, trace=False, llm=mock_llm)
    
    print("\n✅ All agents created successfully!")
    print(f"Agent 1: trace={agent.trace}, verbose={agent.verbose}")
    print(f"Agent 2: trace={trace_agent.trace}, verbose={trace_agent.verbose}")
    print(f"Agent 3: trace={silent_agent.trace}, verbose={silent_agent.verbose}")
    
    # Test the OutputManager integration
    print("\n4. Testing OutputManager integration")
    from cogency.output import OutputManager
    
    output = OutputManager(trace=True, verbose=True)
    print(f"OutputManager created: trace_enabled={output.trace_enabled}, verbose_enabled={output.verbose_enabled}")
    
    # Test trace collection
    await output.trace("Test trace message", node="test")
    traces = output.get_traces()
    print(f"Collected {len(traces)} trace entries")
    
    print("\n🎉 Clean API test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_clean_api())