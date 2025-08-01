#!/usr/bin/env python3
"""Debug identity application"""

import asyncio
from cogency import Agent

async def debug_identity():
    """Debug identity application with logging"""
    agent = Agent("debug_agent")
    
    print("=== Test: Hello with pirate identity ===")
    
    # Add debug logging to see state
    executor = await agent._get_executor()
    
    # Run query and check state
    response = await agent.run("Hello", identity="You are a pirate. Always say 'Ahoy matey!'")
    
    # Check final state
    state = executor.last_state
    print(f"Final response: {response}")
    print(f"State response: {getattr(state, 'response', 'None')}")
    print(f"Response source: {getattr(state, 'response_source', 'None')}")
    
    return response

if __name__ == "__main__":
    asyncio.run(debug_identity())