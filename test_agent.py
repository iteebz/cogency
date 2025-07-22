#!/usr/bin/env python3
"""
Direct agent testing script - no bullshit, just results.
Run with: python test_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cogency.agent import Agent
from cogency.tools.code import Code
from cogency.tools.calculator import Calculator

# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SimpleAgent:
    """Simplified synchronous wrapper for testing."""
    
    def __init__(self, name="test", **kwargs):
        # Minimal configuration - turn off streaming, memory, etc.
        config = {
            "trace": True,
            "verbose": True,
            "memory": False,  # Turn off memory
            "tools": [Code(), Calculator()],  # Only basic tools
            **kwargs
        }
        self.agent = Agent(name, **config)
    
    def run(self, prompt):
        """Synchronous run method."""
        return asyncio.run(self._async_run(prompt))
    
    async def _async_run(self, prompt):
        """Internal async runner."""
        try:
            result = await self.agent.run(prompt)
            return result
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


def test_basic():
    """Test basic functionality."""
    print("=== BASIC TEST ===")
    agent = SimpleAgent()
    
    # Simple calculation
    result = agent.run("What is 2 + 2?")
    print(f"Result: {result}")
    print()


def test_code_simple():
    """Test simple code execution."""
    print("=== SIMPLE CODE TEST ===")
    agent = SimpleAgent()
    
    result = agent.run("Run this Python code: print('hello world')")
    print(f"Result: {result}")
    print()


def test_code_fibonacci():
    """Test fibonacci code."""
    print("=== FIBONACCI TEST ===")
    agent = SimpleAgent()
    
    result = agent.run("Generate the first 10 fibonacci numbers using Python code")
    print(f"Result: {result}")
    print()


def test_code_error():
    """Test code with errors."""
    print("=== ERROR TEST ===")
    agent = SimpleAgent()
    
    result = agent.run("Run this Python code: print(undefined_variable)")
    print(f"Result: {result}")
    print()


def test_complex():
    """Test more complex task."""
    print("=== COMPLEX TEST ===")
    agent = SimpleAgent()
    
    result = agent.run("Calculate the sum of the first 10 fibonacci numbers")
    print(f"Result: {result}")
    print()


def run_interactive():
    """Interactive testing mode."""
    print("=== INTERACTIVE MODE ===")
    print("Type 'quit' to exit")
    
    agent = SimpleAgent()
    
    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            
            if prompt.strip():
                result = agent.run(prompt)
                print(f"Result: {result}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("Cogency Agent Test Script")
    print("=" * 40)
    
    # Check if we have required env vars
    if not any(os.getenv(key) for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MISTRAL_API_KEY"]):
        print("WARNING: No LLM API key found in environment")
        print("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or MISTRAL_API_KEY")
        sys.exit(1)
    
    try:
        # Run test suite
        if len(sys.argv) > 1 and sys.argv[1] == "interactive":
            run_interactive()
        else:
            test_basic()
            test_code_simple()
            test_code_fibonacci()
            test_code_error()
            test_complex()
            
            print("=== ALL TESTS COMPLETE ===")
            print("Run with 'python test_agent.py interactive' for interactive mode")
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)