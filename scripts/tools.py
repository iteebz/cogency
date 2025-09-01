#!/usr/bin/env python3
"""TOOL FEEDBACK AUDIT - Direct testing to fix Gemini loops"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cogency.tools import TOOLS


async def test_tool_feedback():
    """Test all tools and show current feedback patterns."""
    print("🔧 TOOL FEEDBACK AUDIT")
    print("=" * 50)

    tools = {t.name: t for t in TOOLS}

    # Test write tool - the poison.txt scenario
    print("\n📝 WRITE TOOL:")
    print("Command: write(filename='poison.txt', content='POISON')")
    write_result = await tools["write"].execute(
        filename="poison.txt", content="POISON", sandbox=True
    )
    if write_result.success:
        print(f"✅ SUCCESS: {repr(write_result.unwrap())}")
    else:
        print(f"❌ ERROR: {repr(write_result.error)}")

    # Test read tool
    print("\n📖 READ TOOL:")
    print("Command: read(filename='poison.txt')")
    read_result = await tools["read"].execute(filename="poison.txt", sandbox=True)
    if read_result.success:
        content = read_result.unwrap()
        print(f"✅ SUCCESS: {repr(content[:100])}{'...' if len(content) > 100 else ''}")
    else:
        print(f"❌ ERROR: {repr(read_result.error)}")

    # Test list tool
    print("\n📋 LIST TOOL:")
    print("Command: list()")
    list_result = await tools["list"].execute(sandbox=True)
    if list_result.success:
        content = list_result.unwrap()
        print(f"✅ SUCCESS: {repr(content[:150])}{'...' if len(content) > 150 else ''}")
    else:
        print(f"❌ ERROR: {repr(list_result.error)}")

    # Test shell tool - success case
    print("\n🖥️  SHELL TOOL (SUCCESS):")
    print("Command: shell('echo hello')")
    shell_result = await tools["shell"].execute(command="echo hello", sandbox=True)
    if shell_result.success:
        print(f"✅ SUCCESS: {repr(shell_result.unwrap())}")
    else:
        print(f"❌ ERROR: {repr(shell_result.error)}")

    # Test shell tool - failure case
    print("\n🖥️  SHELL TOOL (FAILURE):")
    print("Command: shell('nonexistent-command')")
    shell_fail = await tools["shell"].execute(command="nonexistent-command", sandbox=True)
    if shell_fail.success:
        print(f"✅ SUCCESS: {repr(shell_fail.unwrap())}")
    else:
        print(f"❌ ERROR: {repr(shell_fail.error)}")

    # Test search tool
    print("\n🔍 SEARCH TOOL:")
    print("Command: search('python async')")
    try:
        search_result = await tools["search"].execute(query="python async")
        if search_result.success:
            content = search_result.unwrap()
            print(f"✅ SUCCESS: {repr(content[:200])}{'...' if len(content) > 200 else ''}")
        else:
            print(f"❌ ERROR: {repr(search_result.error)}")
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

    print("\n" + "=" * 50)
    print("🎯 ANALYSIS:")
    print("- Look for ambiguous language: 'Created', 'Updated', etc.")
    print("- Look for unclear success signals")
    print("- Conservative reasoning needs EXPLICIT SUCCESS/ERROR")
    print("- Current feedback causes Gemini uncertainty loops")


async def test_problematic_scenarios():
    """Test specific scenarios that cause Gemini loops."""
    print("\n🚨 PROBLEMATIC SCENARIO TESTING")
    print("=" * 50)

    tools = {t.name: t for t in TOOLS}

    # Scenario 1: Multiple writes to same file (the poison.txt issue)
    print("\n🧪 SCENARIO: Multiple writes to same file")

    # First write
    result1 = await tools["write"].execute(filename="loop-test.txt", content="first", sandbox=True)
    print(f"Write 1: {repr(result1.unwrap() if result1.success else result1.error)}")

    # Second write (overwrite)
    result2 = await tools["write"].execute(filename="loop-test.txt", content="second", sandbox=True)
    print(f"Write 2: {repr(result2.unwrap() if result2.success else result2.error)}")

    # Third write (overwrite again)
    result3 = await tools["write"].execute(filename="loop-test.txt", content="third", sandbox=True)
    print(f"Write 3: {repr(result3.unwrap() if result3.success else result3.error)}")

    print("\n🎯 GEMINI PROBLEM:")
    print("- Sees 'Updated' and thinks 'did it really succeed?'")
    print("- Conservative reasoning: 'better try again to be sure'")
    print("- Creates infinite §THINK → §CALLS → §THINK loop")
    print("- SOLUTION: Clear SUCCESS/ERROR binary signals")


if __name__ == "__main__":
    asyncio.run(test_tool_feedback())
    asyncio.run(test_problematic_scenarios())
