#!/usr/bin/env python3
"""Configuration Showcase - All Agent Configuration Options"""

import asyncio

from cogency import Agent
from cogency.memory.backends.filesystem import FilesystemBackend
from cogency.tools import Calculator, Files, Search
from cogency.utils import config_code, config_item, demo_header, trace_args, section, separator, tips


async def main():
    demo_header("⚙️ Cogency Configuration Reference")

    # 1. Minimal Configuration
    section("1. Minimal Agent")
    minimal = Agent("basic")
    config_item("Agent", minimal.name)
    config_item("Config", "Default everything")

    # 2. Identity Configuration
    section("2. Agent Identity")
    shaped = Agent("personality_bot", identity="witty British comedian with dry humor")
    config_item("Agent", shaped.name)
    config_item("Config", "Custom identity")

    # 3. Tool Subsetting Examples
    section("3. Tool Subsetting Examples")

    # No tools - pure conversation
    Agent("chat_bot", tools=[])
    config_item("Chat Agent", "No tools (pure conversation)")

    # Single tool focus
    Agent("math_bot", tools=[Calculator()])
    config_item("Math Agent", "Calculator only")

    # Focused subset
    Agent("research_bot", tools=[Search(), Files(), Calculator()])
    config_item("Research Agent", "3 focused tools")

    # All tools (default)
    Agent("full_bot")  # Gets all registered tools
    config_item("Full Agent", "All available tools")

    # 4. Memory Configuration
    section("4. Custom Memory Backend")
    memory_agent = Agent(
        "memory_bot", memory_backend=FilesystemBackend(".cogency/custom_memory"), memory=True
    )
    config_item("Agent", memory_agent.name)
    config_item("Config", "Custom memory location")

    # 5. Memory Disabled
    section("5. Memory Disabled")
    stateless = Agent("stateless_bot", memory=False)
    config_item("Agent", stateless.name)
    config_item("Config", "No memory/recall capabilities")

    # 6. Development Configuration
    section("6. Development Mode")
    dev_agent = Agent(
        "dev_bot",
        trace=trace_args(),  # Enable tracing via CLI
        identity="debugging assistant",
    )
    config_item("Agent", dev_agent.name)
    config_item("Config", "Tracing enabled for debugging")

    # 7. LLM Provider Configuration (if available)
    section("7. LLM Provider Options")
    config_item("Config", "Auto-detects from environment variables:")
    config_item("  • OPENAI_API_KEY", "OpenAI GPT models")
    config_item("  • ANTHROPIC_API_KEY", "Claude models")
    config_item("  • GEMINI_API_KEY", "Google Gemini")
    config_item("  • MISTRAL_API_KEY", "Mistral models")

    # 8. Production Configuration Example
    section("8. Production Setup Example")
    production_config = """
    production_agent = Agent("prod_assistant",
        identity="professional customer service representative",
        memory_backend=FilesystemBackend("/app/data/memory"),
        tools=[Search(), Files()],  # Only needed tools
        trace=False  # Disable tracing in production
    )
    """
    config_item("Config", "Production-ready setup")
    config_code(production_config)

    separator()
    tips(
        [
            "Start minimal, add features as needed",
            "Tool subsetting improves focus and performance",
            "Memory can be disabled for stateless use cases",
            "Identity provides agent personality and context",
            "Tracing is essential for development/debugging",
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
