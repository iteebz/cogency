#!/usr/bin/env python3
"""Beautiful Cogency demo - zero ceremony."""
import asyncio
from cogency import Agent

async def main():
    pirate_identity = {
        "personality": "a swashbuckling pirate captain",
        "tone": "boisterous",
        "constraints": ["use-nautical-terms", "end-with-ahoy"]
    }
    agent = Agent("pirate_assistant", response_shaper=pirate_identity)
    await agent.query("What is 2 + 2?")

if __name__ == "__main__":
    asyncio.run(main())