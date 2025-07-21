#!/usr/bin/env python3
"""Persistent Memory - Core Architectural Differentiator"""
import asyncio
from cogency import Agent

async def main():
    print("🧠 Cogency Memory Demo")
    print("=" * 30)
    
    # Create agent with memory enabled and only recall tool
    from cogency.tools import Recall
    agent = Agent("memory_assistant", 
        personality="helpful assistant with excellent memory",
        memory_dir=".cogency/demo_memory",  # Custom memory location for demo
        tools=[Recall]  # Only recall tool - memory is the star
    )
    
    print("\n=== Teaching the Agent ===")
    await agent.query("""Please remember these important details about me:
    - My name is Alex and I'm a software engineer
    - I work primarily with Python and JavaScript  
    - My favorite framework is FastAPI for backends
    - I'm currently building a personal finance app
    - I prefer concise, practical advice over long explanations
    """)
    
    print("\n=== Testing Memory Recall ===")
    await agent.query("What do you know about my work and preferences?")
    
    print("\n=== Context + Memory Working Together ===")
    await agent.query("Based on what you know about me, what would be a good database choice for my current project?")
    
    print("\n=== Memory Across Sessions ===")
    print("💡 Restart this script - the agent will remember everything!")
    print("💡 Try: python memory.py")

if __name__ == "__main__":
    asyncio.run(main())