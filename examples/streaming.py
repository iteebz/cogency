"""
Streaming Integration Test - demonstrates all streaming modes.
"""
import asyncio
from cogency import Agent


async def main():
    """Test streaming modes for cognitive workflow."""
    agent = Agent("streaming_test")
    
    print("🚀 STREAMING INTEGRATION TEST")
    print("=" * 50)
    
    # Single hybrid streaming test
    await agent.stream("Tell me about quantum computing", mode="both")
    
    print("\n✅ STREAMING TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())