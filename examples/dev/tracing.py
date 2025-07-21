#!/usr/bin/env python3
"""Debug Tracing - Development Visibility"""
import asyncio
from cogency import Agent

async def main():
    print("🔍 Cogency Tracing Demo")
    print("=" * 35)
    
    # Create agent with tracing enabled - all tools for comprehensive demo
    agent = Agent("debug_assistant",
        personality="helpful coding assistant",
        trace=True  # Enable detailed tracing
        # Uses all tools to show comprehensive tracing
    )
    
    print("\n=== Simple Query with Tracing ===")
    await agent.query("What's 15% of 200, and what time is it in Tokyo?")
    
    print("\n" + "=" * 50)
    
    print("\n=== Complex Query with Tracing ===")
    await agent.query("""
    Search for information about Python FastAPI framework, 
    then create a simple 'hello.py' file with a basic FastAPI app,
    and show me the current directory contents.
    """)
    
    print("\n" + "=" * 50)
    print("🎯 Tracing shows:")
    print("   • Execution flow through nodes")
    print("   • Tool selection reasoning")
    print("   • Tool execution results")
    print("   • Decision points and routing")
    print("   • Performance timing")
    print("\n💡 Use tracing for:")
    print("   • Debugging agent behavior")
    print("   • Understanding tool selection")
    print("   • Performance optimization")
    print("   • Development and testing")

if __name__ == "__main__":
    asyncio.run(main())