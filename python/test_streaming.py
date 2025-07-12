#!/usr/bin/env python3
"""
Test script for streaming-first architecture pilot.
Tests the new plan node streaming and Agent.stream() method.
"""
import asyncio
import os
from cogency.agent import Agent
from cogency.llm import OpenAILLM

async def test_streaming():
    # Setup agent with OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "test-key")
    
    try:
        llm = OpenAILLM(api_keys=api_key, model="gpt-4o-mini", temperature=0.7)
        agent = Agent(name="StreamTest", llm=llm)
        
        print("🚀 Testing streaming-first architecture...")
        print("=" * 50)
        
        async for chunk in agent.stream("What is 2 + 2?"):
            print(f"📦 {chunk}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())