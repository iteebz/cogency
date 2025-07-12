#!/usr/bin/env python3
"""
Comprehensive streaming example for Cogency 0.3.0

Demonstrates the stream-first architecture where agents yield
execution steps in real-time for transparent reasoning.
"""
import asyncio
import os
from typing import Dict, Any

from cogency.agent import Agent
from cogency.llm import OpenAILLM, GeminiLLM, AnthropicLLM
from cogency.tools import CalculatorTool, WebSearchTool


def format_chunk(chunk: Dict[str, Any]) -> str:
    """Format streaming chunks with beautiful output."""
    if chunk["type"] == "thinking":
        return f"💭 {chunk['node'].upper()}: {chunk['content']}"
    elif chunk["type"] == "chunk":
        return f"🧠 {chunk['content']}"
    elif chunk["type"] == "result":
        return f"\n✅ {chunk['node'].upper()}: {chunk['data']}"
    elif chunk["type"] == "tool_call":
        return f"\n🔧 TOOL: {chunk['content']}"
    elif chunk["type"] == "error":
        return f"\n❌ ERROR: {chunk['content']}"
    elif chunk["type"] == "state":
        return f"\n📊 STATE: Updated"
    else:
        return f"\n🔍 {chunk['type'].upper()}: {chunk}"


async def basic_streaming_demo():
    """Basic streaming demonstration."""
    print("🚀 Basic Streaming Demo")
    print("=" * 50)
    
    # Initialize with OpenAI (fallback to Gemini if no key)
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"), model="gpt-4")
    except:
        try:
            llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
        except:
            print("❌ No valid API keys found. Please set OPENAI_API_KEY or GOOGLE_API_KEY")
            return
    
    agent = Agent(
        name="StreamingCalculator",
        llm=llm,
        tools=[CalculatorTool()]
    )
    
    # Stream a calculation task
    print("Query: 'What is 25 * 34 + 100?'\n")
    
    async for chunk in agent.stream("What is 25 * 34 + 100?"):
        print(format_chunk(chunk))
    
    print("\n" + "=" * 50)


async def advanced_streaming_demo():
    """Advanced streaming with multiple tools and complex reasoning."""
    print("\n🎯 Advanced Streaming Demo")
    print("=" * 50)
    
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"), model="gpt-4")
    except:
        try:
            llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
        except:
            print("❌ No valid API keys found")
            return
    
    agent = Agent(
        name="StreamingAgent",
        llm=llm,
        tools=[CalculatorTool(), WebSearchTool()]
    )
    
    # Complex multi-step task
    query = "Calculate 15 * 23 and then search for information about that number in mathematics"
    print(f"Query: '{query}'\n")
    
    async for chunk in agent.stream(query):
        print(format_chunk(chunk))
    
    print("\n" + "=" * 50)


async def rate_limited_streaming_demo():
    """Demonstrate yield_interval rate limiting."""
    print("\n⏱️  Rate Limited Streaming Demo")
    print("=" * 50)
    
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"), model="gpt-4")
    except:
        try:
            llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
        except:
            print("❌ No valid API keys found")
            return
    
    agent = Agent(
        name="RateLimitedAgent",
        llm=llm,
        tools=[CalculatorTool()]
    )
    
    print("Query: 'What is 100 / 25?' (with 0.5s yield interval)\n")
    
    import time
    start_time = time.time()
    
    async for chunk in agent.stream("What is 100 / 25?", yield_interval=0.5):
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] {format_chunk(chunk)}")
    
    print(f"\nTotal time: {time.time() - start_time:.1f}s")
    print("=" * 50)


async def streaming_vs_standard_demo():
    """Compare streaming vs standard execution."""
    print("\n⚡ Streaming vs Standard Demo")
    print("=" * 50)
    
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"), model="gpt-4")
    except:
        try:
            llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
        except:
            print("❌ No valid API keys found")
            return
    
    agent = Agent(
        name="ComparisonAgent",
        llm=llm,
        tools=[CalculatorTool()]
    )
    
    query = "Calculate 12 * 12"
    
    # Standard execution
    print("🔄 Standard Execution:")
    result = await agent.run(query)
    print(f"Result: {result['response']}\n")
    
    # Streaming execution
    print("🌊 Streaming Execution:")
    async for chunk in agent.stream(query):
        if chunk["type"] in ["thinking", "result"]:
            print(format_chunk(chunk))
    
    print("\n" + "=" * 50)


async def error_handling_demo():
    """Demonstrate error handling in streaming."""
    print("\n🚨 Error Handling Demo")
    print("=" * 50)
    
    try:
        llm = OpenAILLM(api_keys=os.getenv("OPENAI_API_KEY"), model="gpt-4")
    except:
        try:
            llm = GeminiLLM(api_keys=os.getenv("GOOGLE_API_KEY"))
        except:
            print("❌ No valid API keys found")
            return
    
    agent = Agent(
        name="ErrorAgent",
        llm=llm,
        tools=[CalculatorTool()]
    )
    
    # Query that will cause tool parsing errors
    print("Query: 'Calculate abc + def' (invalid math)\n")
    
    async for chunk in agent.stream("Calculate abc + def"):
        print(format_chunk(chunk))
    
    print("\n" + "=" * 50)


async def main():
    """Run all streaming demonstrations."""
    print("🎉 Cogency 0.3.0 Streaming Architecture Showcase")
    print("Stream-first design: agents defined by their execution streams")
    print("=" * 70)
    
    # Check for API keys
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        print("⚠️  Please set OPENAI_API_KEY or GOOGLE_API_KEY environment variable")
        print("   Example: export OPENAI_API_KEY='your-key-here'")
        return
    
    demos = [
        basic_streaming_demo,
        advanced_streaming_demo,
        rate_limited_streaming_demo,
        streaming_vs_standard_demo,
        error_handling_demo
    ]
    
    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        
        # Pause between demos
        await asyncio.sleep(1)
    
    print("\n🎯 Key Insights:")
    print("• Stream IS the execution, not a view of it")
    print("• Every node yields thinking steps in real-time")
    print("• Natural cancellation and unified interfaces")
    print("• Transparent agent reasoning without black boxes")
    print("• Configurable yield intervals for rate limiting")
    print("\n🚀 Stream-first agent architecture in action!")


if __name__ == "__main__":
    asyncio.run(main())