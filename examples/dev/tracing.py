#!/usr/bin/env python3
"""Debug Tracing - Development Visibility"""
import asyncio
from cogency import Agent
from cogency.utils.terminal import demo_header, stream_response, section, showcase, separator, tips

async def main():
    demo_header("🔍 Cogency Tracing Demo", 35)
    
    # Create agent with tracing enabled - all tools for comprehensive demo
    agent = Agent("debug_assistant",
        identity="helpful coding assistant",
        trace=True  # Enable detailed tracing
        # Uses all tools to show comprehensive tracing
    )
    
    section("Simple Query with Tracing")
    await stream_response(agent.stream("What's 15% of 200, and what time is it in Tokyo?"))
    
    separator()
    
    section("Complex Query with Tracing")
    await stream_response(agent.stream("""
    Search for information about Python FastAPI framework, 
    then create a simple 'hello.py' file with a basic FastAPI app,
    and show me the current directory contents.
    """))
    
    separator()
    showcase("🎯 Tracing shows:", [
        "Execution flow through nodes",
        "Tool selection reasoning",
        "Tool execution results",
        "Decision points and routing",
        "Performance timing"
    ])
    tips([
        "Debugging agent behavior",
        "Understanding tool selection", 
        "Performance optimization",
        "Development and testing"
    ])

if __name__ == "__main__":
    asyncio.run(main())