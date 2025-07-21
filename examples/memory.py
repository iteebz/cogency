#!/usr/bin/env python3
"""Persistent Memory - Core Architectural Differentiator"""
import asyncio
from cogency import Agent
from cogency.utils import demo_header, stream_response, section, info, parse_trace_args

async def main():
    demo_header("🧠 Cogency Memory Demo", 30)
    
    # Create agent with memory enabled and only recall tool
    from cogency.tools import Recall
    agent = Agent("memory_assistant", 
        identity="helpful assistant with excellent memory",
        memory_dir=".cogency/demo_memory",  # Custom memory location for demo
        tools=[Recall],  # Only recall tool - memory is the star
        trace=parse_trace_args()
    )
    
    section("Teaching the Agent")
    await stream_response(agent.stream("""Please remember these important details about me:
    - My name is Alex and I'm a software engineer
    - I work primarily with Python and JavaScript  
    - My favorite framework is FastAPI for backends
    - I'm currently building a personal finance app
    - I prefer concise, practical advice over long explanations
    """))
    
    section("Testing Memory Recall")
    await stream_response(agent.stream("What do you know about my work and preferences?"))
    
    section("Context + Memory Working Together")
    await stream_response(agent.stream("Based on what you know about me, what would be a good database choice for my current project?"))
    
    section("Memory Across Sessions")
    info("Restart this script - the agent will remember everything!")
    info("Try: python memory.py")

if __name__ == "__main__":
    asyncio.run(main())