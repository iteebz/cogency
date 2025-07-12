#!/usr/bin/env python3
"""
Simple streaming example for Cogency 0.3.0

Shows the minimal code needed to use streaming.
"""
import asyncio
import os

from cogency.agent import Agent
from cogency.llm import OpenAILLM, GeminiLLM
from cogency.tools import CalculatorTool


async def main():
    """Simple streaming example."""
    # Setup LLM (try OpenAI first, fallback to Gemini)
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"))
    except:
        llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
    
    # Create agent
    agent = Agent(
        name="SimpleAgent",
        llm=llm,
        tools=[CalculatorTool()]
    )
    
    # Stream execution with beautiful output
    print("🤔 Question: What is 15 * 23?\n")
    
    async for chunk in agent.stream("What is 15 * 23?"):
        if chunk["type"] == "thinking":
            print(f"💭 {chunk['content']}")
        elif chunk["type"] == "chunk":
            print(f"🧠 {chunk['content']}", end="")
        elif chunk["type"] == "result":
            print(f"\n✅ {chunk['node']}: {chunk['data']}")


if __name__ == "__main__":
    asyncio.run(main())