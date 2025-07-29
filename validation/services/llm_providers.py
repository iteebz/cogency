"""LLM provider validation - test different backends."""

import asyncio
import os

from cogency import Agent
from cogency.services.llm import AnthropicLLM, GeminiLLM, MistralLLM, OpenAILLM, XaiLLM


async def test_provider_availability():
    """Test which LLM providers are available."""
    print("🔍 Testing LLM provider availability...")

    providers = [
        ("OpenAI", OpenAILLM, "OPENAI_API_KEY"),
        ("Anthropic", AnthropicLLM, "ANTHROPIC_API_KEY"),
        ("Gemini", GeminiLLM, "GEMINI_API_KEY"),
        ("Mistral", MistralLLM, "MISTRAL_API_KEY"),
        ("XAI", XaiLLM, "XAI_API_KEY"),
    ]

    available_providers = []

    for name, provider_class, env_key in providers:
        if os.environ.get(env_key):
            try:
                llm = provider_class()
                agent = Agent(f"provider-{name.lower()}", llm=llm, debug=False)
                result = await agent.run("Say 'test successful'")

                if result and "test successful" in result.lower():
                    print(f"✅ {name} provider available and working")
                    available_providers.append(name)
                else:
                    print(f"⚠️  {name} provider configured but not responding correctly")

            except Exception as e:
                print(f"❌ {name} provider failed: {e}")
        else:
            print(f"⚪ {name} provider not configured (missing {env_key})")

    return len(available_providers) > 0


async def test_provider_consistency():
    """Test that different providers give reasonable responses."""
    print("🎯 Testing provider response consistency...")

    # Use available providers
    test_providers = []

    if os.environ.get("OPENAI_API_KEY"):
        test_providers.append(("OpenAI", OpenAILLM))

    if os.environ.get("ANTHROPIC_API_KEY"):
        test_providers.append(("Anthropic", AnthropicLLM))

    if len(test_providers) == 0:
        print("⚠️  No providers configured for consistency testing")
        return True  # Don't fail if no providers available

    query = "What is the capital of Japan?"
    results = []

    for name, provider_class in test_providers:
        try:
            llm = provider_class()
            agent = Agent(f"consistency-{name.lower()}", llm=llm, debug=False)
            result = await agent.run(query)

            if result and "tokyo" in result.lower():
                print(f"✅ {name} gave correct answer")
                results.append(True)
            else:
                print(f"❌ {name} gave incorrect answer: {result[:100]}...")
                results.append(False)

        except Exception as e:
            print(f"❌ {name} consistency test failed: {e}")
            results.append(False)

    return all(results) if results else True


async def test_provider_error_handling():
    """Test provider error handling with invalid requests."""
    print("🛡️  Testing provider error handling...")

    # Test with first available provider
    test_llm = None
    provider_name = "Unknown"

    if os.environ.get("OPENAI_API_KEY"):
        test_llm = OpenAILLM()
        provider_name = "OpenAI"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        test_llm = AnthropicLLM()
        provider_name = "Anthropic"

    if not test_llm:
        print("⚠️  No providers available for error handling test")
        return True

    agent = Agent(f"error-{provider_name.lower()}", llm=test_llm, debug=True)

    # This should either handle gracefully or provide a reasonable error
    result = await agent.run("")  # Empty query

    if result and ("ERROR:" in result or len(result) > 10):
        print(f"✅ {provider_name} error handling working")
        return True
    else:
        print(f"❌ {provider_name} error handling failed")
        return False


async def test_provider_streaming():
    """Test provider streaming capabilities."""
    print("🌊 Testing provider streaming...")

    # Test with first available provider
    test_llm = None
    provider_name = "Unknown"

    if os.environ.get("OPENAI_API_KEY"):
        test_llm = OpenAILLM()
        provider_name = "OpenAI"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        test_llm = AnthropicLLM()
        provider_name = "Anthropic"

    if not test_llm:
        print("⚠️  No providers available for streaming test")
        return True

    agent = Agent(f"stream-{provider_name.lower()}", llm=test_llm, debug=False)

    chunks = []
    async for chunk in agent.stream("Count from 1 to 5"):
        chunks.append(chunk)

    full_response = "".join(chunks)

    if len(chunks) > 1 and "1" in full_response and "5" in full_response:
        print(f"✅ {provider_name} streaming working")
        return True
    else:
        print(f"❌ {provider_name} streaming failed")
        return False


async def main():
    """Run all LLM provider validation tests."""
    print("🚀 Starting LLM provider validation...\n")

    tests = [
        test_provider_availability,
        test_provider_consistency,
        test_provider_error_handling,
        test_provider_streaming,
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append(success)
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print(f"📊 LLM provider validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 LLM providers are production ready!")
    else:
        print("⚠️  LLM providers need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
