#!/usr/bin/env python3
"""CLI interface for cogency agent."""

import sys
import os
import json
from typing import List
from dotenv import load_dotenv, find_dotenv

from cogency.agent import Agent
from cogency.llm import GeminiLLM, KeyRotator
from cogency.tools.calculator import CalculatorTool


def load_api_keys() -> List[str]:
    """Load API keys from environment variables."""
    keys = []
    
    # Try numbered keys first (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for i in range(1, 10):
        key = os.environ.get(f"GEMINI_API_KEY_{i}")
        if key:
            keys.append(key)
    
    # If no numbered keys, try single key
    if not keys:
        single_key = os.environ.get("GEMINI_API_KEY")
        if single_key:
            keys.append(single_key)
    
    return keys


def create_llm() -> GeminiLLM:
    """Create LLM instance with intelligent key handling."""
    keys = load_api_keys()
    
    if len(keys) > 1:
        # Multiple keys - use rotation
        key_rotator = KeyRotator(keys)
        return GeminiLLM(key_rotator=key_rotator)
    elif len(keys) == 1:
        # Single key - use directly
        return GeminiLLM(api_key=keys[0])
    else:
        # No keys found - raise helpful error
        raise ValueError(
            "No API keys found. Please set either:\n"
            "- GEMINI_API_KEY for single key usage\n"
            "- GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc. for key rotation"
        )


def interactive_mode(agent: Agent, enable_trace: bool = False):
    """Run agent in interactive mode."""
    print("🤖 Cogency Agent - Interactive Mode")
    print("Type 'exit' or 'quit' to stop, 'trace' to toggle tracing")
    print("-" * 50)
    
    while True:
        try:
            message = input("\n> ").strip()
            
            if message.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if message.lower() == 'trace':
                enable_trace = not enable_trace
                print(f"Tracing {'enabled' if enable_trace else 'disabled'}")
                continue
            
            if not message:
                continue
                
            result = agent.run(message, enable_trace=enable_trace)
            print(f"🤖 {result['response']}")
            
            if enable_trace:
                print("\nConversation:", json.dumps(result["conversation"], indent=2))
                if "execution_trace" in result:
                    print("Execution trace:", json.dumps(result["execution_trace"], indent=2))
                    
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv(find_dotenv(usecwd=True))
    
    # Parse arguments
    enable_trace = "--trace" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv
    
    # Create agent
    try:
        llm = create_llm()
        calculator = CalculatorTool()
        agent = Agent(name="CogencyAgent", llm=llm, tools=[calculator])
    except Exception as e:
        print(f"Error initializing agent: {e}")
        sys.exit(1)
    
    # Interactive mode
    if interactive or len(sys.argv) < 2:
        interactive_mode(agent, enable_trace)
        return
    
    # Single query mode
    message = sys.argv[1]
    
    try:
        result = agent.run(message, enable_trace=enable_trace)
        print("Response:", result["response"])
        
        if enable_trace:
            print("Conversation:", json.dumps(result["conversation"], indent=2))
            if "execution_trace" in result:
                print("Execution trace:", json.dumps(result["execution_trace"], indent=2))
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()