#!/usr/bin/env python3
"""Code Execution - Killer Feature Demo"""
import asyncio
from cogency import Agent
from cogency.tools import Shell, Files, Code

async def main():
    print("🚀 Cogency Coding Demo")
    print("=" * 30)
    
    # Create specialized coding agent with focused tool subset
    coding_agent = Agent("coding_assistant",
        personality="expert Python developer and code reviewer",
        tone="precise and helpful",
        tools=[Code(), Files(), Shell()]  # Focused coding environment
    )
    
    print("\n=== Complete Coding Workflow ===")
    query = """Create a complete Bitcoin price tracker:
    
    1. Write a Python script that fetches the current Bitcoin price from the CoinDesk API
    2. The script should display the price in USD with proper formatting
    3. Add error handling for network issues
    4. Save the script as 'btc_tracker.py'
    5. Execute the script to verify it works correctly
    6. Show me the contents of the created file
    
    Make the code clean, well-commented, and production-ready.
    """
    
    await coding_agent.query(query)
    
    print("\n" + "=" * 50)
    print("🎯 This demo showcases:")
    print("   • Code generation")
    print("   • File I/O operations") 
    print("   • Code execution")
    print("   • Error handling")
    print("   • Tool subsetting")
    print("   • Complete development workflow")

if __name__ == "__main__":
    asyncio.run(main())