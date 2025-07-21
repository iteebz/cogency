#!/usr/bin/env python3
"""Code Execution - Killer Feature Demo"""
import asyncio
from cogency import Agent
from cogency.tools import Shell, Files, Code
from cogency.utils.terminal import demo_header, stream_response, section, showcase, separator

async def main():
    demo_header("🚀 Cogency Coding Demo", 30)
    
    # Create specialized coding agent with focused tool subset
    coding_agent = Agent("coding_assistant",
        identity="expert Python developer and code reviewer",
        tools=[Code(), Files(), Shell()]  # Focused coding environment
    )
    
    section("Complete Coding Workflow")
    query = """Create a complete Bitcoin price tracker:
    
    1. Write a Python script that fetches the current Bitcoin price from the CoinDesk API
    2. The script should display the price in USD with proper formatting
    3. Add error handling for network issues
    4. Save the script as 'btc_tracker.py'
    5. Execute the script to verify it works correctly
    6. Show me the contents of the created file
    
    Make the code clean, well-commented, and production-ready.
    """
    
    await stream_response(coding_agent.stream(query))
    
    separator()
    showcase("🎯 This demo showcases:", [
        "Code generation",
        "File I/O operations",
        "Code execution",
        "Error handling", 
        "Tool subsetting",
        "Complete development workflow"
    ])

if __name__ == "__main__":
    asyncio.run(main())