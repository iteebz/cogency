#!/usr/bin/env python3
"""Hello World - Conversation + Response Shaping"""
import asyncio
from cogency import Agent

async def main():
    print("🔥 Cogency Hello World Demo")
    print("=" * 40)
    
    # 1. Vanilla Agent
    print("\n=== Vanilla Agent ===")
    vanilla_agent = Agent("assistant", tools=[])  # No tools - pure conversation
    await vanilla_agent.query("Tell me a fun fact about the Roman Empire.")
    
    # 2. Response Shaping Demo
    print("\n=== Response Shaping Demo ===")
    mentor_agent = Agent("coding_mentor",
        personality="experienced coding mentor who loves teaching",
        tone="encouraging and practical", 
        style="step-by-step guidance with examples",
        tools=[]  # No tools - focus on personality/response shaping
    )
    await mentor_agent.query("How should I start learning Python?")
    
    # 3. Interactive Chat Loop
    print("\n=== Interactive Chat (type 'quit' to exit) ===")
    while True:
        try:
            user_input = input("\n👤 ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input:
                await mentor_agent.query(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())