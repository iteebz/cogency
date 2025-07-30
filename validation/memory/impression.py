"""E2E validation for LLM-native memory system."""

import asyncio
from cogency import Agent


async def main():
    """Validate memory.remember()/recall() API works."""
    agent = Agent("test", memory=True)
    
    # Learn preference
    await agent.run("I prefer TypeScript")
    
    # Test recall  
    response = await agent.run("What language should I use?")
    
    if "typescript" in response.lower():
        print("✅ Memory validation passed")
        return True
    else:
        print("❌ Memory validation failed")  
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)