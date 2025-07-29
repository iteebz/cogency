"""Agent personality validation - identity and output schema."""

import asyncio

from cogency import Agent


async def test_identity_basic():
    """Test basic identity configuration."""
    print("🎭 Testing basic identity configuration...")

    identity = "You are a helpful math tutor who explains concepts step by step."

    agent = Agent("identity-basic", identity=identity, debug=True)

    result = await agent.run("How do you solve 2x + 5 = 15?")

    if (
        result
        and "ERROR:" not in result
        and ("step" in result.lower() or "first" in result.lower())
        and "x = 5" in result
    ):
        print("✅ Basic identity configuration succeeded")
        return True
    else:
        print("❌ Basic identity configuration failed")
        return False


async def test_identity_consistency():
    """Test identity consistency across interactions."""
    print("🎨 Testing identity consistency...")

    identity = "You are a pirate captain who speaks in nautical terms and always mentions treasure."

    agent = Agent("identity-consistency", identity=identity, debug=True)

    result1 = await agent.run("What's the weather like?")
    result2 = await agent.run("Tell me about mathematics.")

    pirate_terms = ["matey", "ahoy", "ship", "sail", "treasure", "ye", "arr"]

    has_pirate_speech1 = any(term in result1.lower() for term in pirate_terms)
    has_pirate_speech2 = any(term in result2.lower() for term in pirate_terms)

    if (
        result1
        and result2
        and "ERROR:" not in result1
        and "ERROR:" not in result2
        and has_pirate_speech1
        and has_pirate_speech2
    ):
        print("✅ Identity consistency succeeded")
        return True
    else:
        print("❌ Identity consistency failed")
        return False


async def test_output_schema_basic():
    """Test basic output schema enforcement."""
    print("📋 Testing basic output schema...")

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reasoning": {"type": "string"},
        },
        "required": ["answer", "confidence"],
    }

    agent = Agent("schema-basic", output_schema=schema, debug=True)

    result = await agent.run("What is the capital of Italy?")

    # Check if response follows JSON-like structure
    if (
        result
        and "ERROR:" not in result
        and ("answer" in result.lower() or "confidence" in result.lower())
        and "rome" in result.lower()
    ):
        print("✅ Basic output schema succeeded")
        return True
    else:
        print("❌ Basic output schema failed")
        return False


async def test_identity_with_schema():
    """Test identity combined with output schema."""
    print("🎯 Testing identity with output schema...")

    identity = "You are a scientific researcher who provides precise, evidence-based answers."
    schema = {
        "type": "object",
        "properties": {
            "hypothesis": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "conclusion": {"type": "string"},
        },
    }

    agent = Agent("identity-schema", identity=identity, output_schema=schema, debug=True)

    result = await agent.run("Why do leaves change color in fall?")

    scientific_terms = ["chlorophyll", "pigment", "temperature", "light", "chemical"]
    has_scientific_content = any(term in result.lower() for term in scientific_terms)

    has_structure = any(
        field in result.lower() for field in ["hypothesis", "evidence", "conclusion"]
    )

    if result and "ERROR:" not in result and has_scientific_content and has_structure:
        print("✅ Identity with schema succeeded")
        return True
    else:
        print("❌ Identity with schema failed")
        return False


async def main():
    """Run all personality validation tests."""
    print("🚀 Starting personality validation...\n")

    tests = [
        test_identity_basic,
        test_identity_consistency,
        test_output_schema_basic,
        test_identity_with_schema,
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

    print(f"📊 Personality validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Personality features are production ready!")
    else:
        print("⚠️  Personality features need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
