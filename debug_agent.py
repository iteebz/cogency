#!/usr/bin/env python3
"""Debug agent notifications."""

import asyncio
from src.cogency import Agent

async def test_agent():
    print("=== Testing Agent Notifications ===")
    
    # Test 1: Simple math (might skip full workflow)
    print("\n1. Simple math with notify=True:")
    agent = Agent("test", notify=True)
    response = await agent.run_async("What is 2+2?")
    print(f"Response: {response}")
    
    # Test 2: Complex query that should trigger full workflow
    print("\n2. Complex query with tools:")
    agent2 = Agent("test2", notify=True, tools=["files", "shell"])
    response2 = await agent2.run_async("Help me analyze my current directory structure and tell me what programming languages are used in this project.")
    print(f"Response: {response2}")
    
    # Test 3: Agent with debug=True for complex task
    print("\n3. Debug mode with complex task:")
    agent3 = Agent("test3", notify=True, debug=True, tools=["files"])
    response3 = await agent3.run_async("Find all Python files in the src directory and tell me what the main classes are.")
    print(f"Response: {response3}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(test_agent())