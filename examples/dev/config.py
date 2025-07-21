#!/usr/bin/env python3
"""Configuration Showcase - All Agent Configuration Options"""
import asyncio
from cogency import Agent
from cogency.tools import Calculator, Files, Search
from cogency.memory.backends.filesystem import FilesystemBackend

async def main():
    print("⚙️  Cogency Configuration Reference")
    print("=" * 45)
    
    # 1. Minimal Configuration
    print("\n=== 1. Minimal Agent ===")
    minimal = Agent("basic")
    print(f"Agent: {minimal.name}")
    print("Config: Default everything")
    
    # 2. Response Shaping Configuration
    print("\n=== 2. Response Shaping ===")
    shaped = Agent("personality_bot",
        personality="witty British comedian with dry humor",
        tone="sarcastic but helpful",
        style="concise with clever analogies",
        response_shaper={
            "constraints": ["keep responses under 100 words", "always end with a joke"]
        }
    )
    print(f"Agent: {shaped.name}")
    print("Config: Full personality customization")
    
    # 3. Tool Subsetting Examples
    print("\n=== 3. Tool Subsetting Examples ===")
    
    # No tools - pure conversation
    chat_only = Agent("chat_bot", tools=[])
    print(f"Chat Agent: No tools (pure conversation)")
    
    # Single tool focus
    math_bot = Agent("math_bot", tools=[Calculator()])
    print(f"Math Agent: Calculator only")
    
    # Focused subset
    research_bot = Agent("research_bot", 
        tools=[Search(), HTTP(), Files(), Calculator()])
    print(f"Research Agent: 4 focused tools")
    
    # All tools (default)
    full_agent = Agent("full_bot")  # Gets all registered tools
    print(f"Full Agent: All available tools")
    
    # 4. Memory Configuration
    print("\n=== 4. Custom Memory Backend ===")
    memory_agent = Agent("memory_bot",
        memory_backend=FilesystemBackend(".cogency/custom_memory"),
        memory=True
    )
    print(f"Agent: {memory_agent.name}")
    print("Config: Custom memory location")
    
    # 5. Memory Disabled
    print("\n=== 5. Memory Disabled ===")
    stateless = Agent("stateless_bot", memory=False)
    print(f"Agent: {stateless.name}")
    print("Config: No memory/recall capabilities")
    
    # 6. Development Configuration
    print("\n=== 6. Development Mode ===")
    dev_agent = Agent("dev_bot",
        trace=True,  # Enable tracing
        personality="debugging assistant"
    )
    print(f"Agent: {dev_agent.name}")
    print("Config: Tracing enabled for debugging")
    
    # 7. LLM Provider Configuration (if available)
    print("\n=== 7. LLM Provider Options ===")
    print("Config: Auto-detects from environment variables:")
    print("  • OPENAI_API_KEY → OpenAI GPT models")
    print("  • ANTHROPIC_API_KEY → Claude models") 
    print("  • GEMINI_API_KEY → Google Gemini")
    print("  • MISTRAL_API_KEY → Mistral models")
    
    # 8. Production Configuration Example
    print("\n=== 8. Production Setup Example ===")
    production_config = """
    production_agent = Agent("prod_assistant",
        personality="professional customer service representative",
        tone="polite and efficient",
        memory_backend=FilesystemBackend("/app/data/memory"),
        tools=[Search(), Files()],  # Only needed tools
        trace=False,  # Disable tracing in production
        response_shaper={
            "constraints": [
                "always be professional",
                "keep responses under 200 words",
                "ask for clarification if request is unclear"
            ]
        }
    )
    """
    print("Config: Production-ready setup")
    print(production_config)
    
    print("\n" + "=" * 50)
    print("💡 Configuration Tips:")
    print("   • Start minimal, add features as needed")
    print("   • Tool subsetting improves focus and performance")
    print("   • Memory can be disabled for stateless use cases")
    print("   • Response shaping is powerful for specialized agents")
    print("   • Tracing is essential for development/debugging")

if __name__ == "__main__":
    asyncio.run(main())