#!/usr/bin/env python3
"""Basic cross-provider smoke test for beta validation."""

import asyncio
import os
from typing import Dict, List

from cogency import Agent
from cogency.services.llm import AnthropicLLM, OpenAILLM, GeminiLLM, MistralLLM


async def test_provider(provider_name: str, llm_instance) -> Dict:
    """Test basic functionality with a provider."""
    print(f"Testing {provider_name}...")
    
    try:
        agent = Agent("test", llm=llm_instance, notify=False)
        result = await agent.run("What is 2+2? Just give the number.")
        
        return {
            "provider": provider_name,
            "status": "✅ PASS",
            "result": result[:50] + "..." if len(result) > 50 else result,
            "error": None
        }
    except Exception as e:
        return {
            "provider": provider_name,
            "status": "❌ FAIL", 
            "result": None,
            "error": str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        }


async def main():
    """Run cross-provider smoke tests."""
    print("🧪 Cogency Cross-Provider Smoke Test")
    print("=" * 40)
    
    # Test configurations
    providers = []
    
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("OpenAI", OpenAILLM()))
    
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("Anthropic", AnthropicLLM()))
    
    if os.getenv("GEMINI_API_KEY"):
        providers.append(("Gemini", GeminiLLM()))
        
    if os.getenv("MISTRAL_API_KEY"):
        providers.append(("Mistral", MistralLLM()))
    
    if not providers:
        print("❌ No API keys found. Set at least one:")
        print("   OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY")
        return
    
    # Run tests
    results = []
    for name, llm in providers:
        result = await test_provider(name, llm)
        results.append(result)
        print(f"   {result['status']} {result['provider']}")
        if result['error']:
            print(f"      Error: {result['error']}")
    
    # Summary
    print("\n📊 Summary:")
    passed = sum(1 for r in results if "PASS" in r['status'])
    total = len(results)
    print(f"   {passed}/{total} providers working")
    
    if passed < total:
        print("\n⚠️  Some providers failed. This is expected in beta.")
        print("   Report issues: https://github.com/iteebz/cogency/issues")


if __name__ == "__main__":
    asyncio.run(main())