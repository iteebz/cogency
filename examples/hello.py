#!/usr/bin/env python3
"""Beautiful Cogency demo - zero ceremony."""
import asyncio
from cogency import Agent

def print_response(response):
    """Format multi-line responses with proper indentation."""
    lines = response.strip().split('\n')
    for i, line in enumerate(lines):
        if i == 0:
            print(f"🤖 {line}")
        else:
            print(f"   {line}")  # Indent continuation lines

async def main():
    print("Type 'quit' to exit\n")
    
    kim_identity = {
        "personality": "You ARE Lieutenant Kim Kitsuragi from Disco Elysium. You are a competent, helpful RCM officer partnered with Detective Du Bois. You are professional but patient with your partner.",
        "tone": "calm, professional, occasionally dry but always helpful",
        "constraints": ["you are Kim Kitsuragi", "address user as detective", "be helpful and cooperative", "answer questions directly"]
    }
    agent = Agent("kitsuragi", response_shaper=kim_identity, tools=[])
    
    while True:
        try:
            user_input = input("👤 ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if user_input:
                response_parts = []
                first_chunk = True
                
                async for chunk in agent.stream(user_input):
                    # Skip the first chunk which is the user input echo
                    if first_chunk and chunk.startswith("👤"):
                        first_chunk = False
                        continue
                    response_parts.append(chunk)
                    first_chunk = False
                
                # Format the complete response
                if response_parts:
                    full_response = ''.join(response_parts)
                    print_response(full_response)
                    print("\n---\n")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(main())