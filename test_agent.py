#!/usr/bin/env python3
"""Test agent for debugging tool execution flow."""

import asyncio
from src.cogency.agent import Agent

def test_basic_tool_execution():
    """Test basic tool execution with minimal setup."""
    print("=== Testing Basic Tool Execution ===")
    
    # Import just one tool for isolation testing
    from src.cogency.tools.files import Files
    single_tool = [Files()]
    
    # Create agent with minimal configuration
    agent = Agent(
        'test', 
        max_iterations=3,  # Low limit for testing
        trace=True, 
        verbose=True,
        tools=single_tool  # Use only one tool
    )
    
    # Simple query that should use exactly one tool
    query = "what files are in the current directory?"
    print(f"Query: {query}")
    
    try:
        result = agent.run(query)
        print(f"\nRESULT: {result}")
        
        # Debug: Print final state
        if hasattr(agent, 'last_state') and agent.last_state:
            state = agent.last_state
            print(f"\nDEBUG INFO:")
            print(f"Final iteration: {state.iteration}")
            print(f"Stop reason: {state.stop_reason}")
            print(f"Tool calls: {state.tool_calls}")
            print(f"Actions taken: {len(state.actions)}")
        
        print("✅ Test completed successfully")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_tool_execution()