#!/usr/bin/env python3
"""File manager tool isolation test."""
import asyncio
from cogency import Agent, FileManagerTool

async def main():
    print("📁 Testing FileManagerTool...")
    agent = Agent("files", tools=[FileManagerTool(base_dir="sandbox")])
    result = await agent.run("Create a test file called hello.txt with content 'Hello World'")
    result_str = str(result).lower()
    has_file = any(word in result_str for word in ["created", "file", "hello", "world"])
    assert has_file, f"No file operation: {result}"

if __name__ == "__main__":
    asyncio.run(main())