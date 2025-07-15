#!/usr/bin/env python3
"""Web search tool isolation test."""
import asyncio
from cogency import Agent, WebSearchTool

async def main():
    print("🔍 Testing WebSearchTool...")
    agent = Agent("search", tools=[WebSearchTool()])
    result = await agent.run("Search for Python programming tutorials")
    result_str = str(result).lower()
    has_search = any(word in result_str for word in ["python", "tutorial", "programming", "results"])
    assert has_search, f"No search results: {result}"

if __name__ == "__main__":
    asyncio.run(main())