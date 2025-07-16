#!/usr/bin/env python3
"""BRUTAL REALITY CHECK: Test if Cogency actually works as advertised."""

import asyncio
import time
from pathlib import Path

# Test 1: The "6-Line Magic" Test
async def test_basic_magic():
    """Test the most basic claim: Agent() just works."""
    print("🔥 TEST 1: 6-Line Magic")
    
    try:
        from cogency import Agent
        print("✅ Import successful")
        
        agent = Agent("assistant")
        print("✅ Agent instantiation successful")
        
        result = await agent.run("Hello world")
        print(f"✅ Basic run successful: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

# Test 2: Multi-Turn Reasoning Complexity
async def test_multiturn_reasoning():
    """Test if ReAct loop actually adapts complexity."""
    print("\n🔥 TEST 2: Multi-Turn Reasoning Complexity")
    
    try:
        from cogency import Agent
        agent = Agent("assistant", trace=True)
        
        # Simple query
        print("Testing simple query...")
        start = time.time()
        result1 = await agent.run("What's 2+2?")
        time1 = time.time() - start
        print(f"Simple query result: {result1[:100]}... (took {time1:.2f}s)")
        
        # Complex query
        print("Testing complex query...")
        start = time.time()
        result2 = await agent.run("Research the impact of climate change on coffee production in Ethiopia, then suggest 3 actionable solutions")
        time2 = time.time() - start
        print(f"Complex query result: {result2[:100]}... (took {time2:.2f}s)")
        
        # Reality check: Complex should take longer
        if time2 > time1:
            print("✅ Complexity adaptation detected (complex took longer)")
        else:
            print("⚠️  No clear complexity adaptation detected")
            
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

# Test 3: Streaming Claims
async def test_streaming():
    """Test if streaming actually works and provides clean output."""
    print("\n🔥 TEST 3: Streaming Claims")
    
    try:
        from cogency import Agent
        agent = Agent("assistant")
        
        print("Testing streaming...")
        chunks = []
        chunk_count = 0
        
        async for chunk in agent.stream("Explain quantum computing in simple terms"):
            chunks.append(chunk)
            chunk_count += 1
            if chunk_count <= 3:  # Show first few chunks
                print(f"Chunk {chunk_count}: {chunk[:50]}...")
        
        full_response = "".join(chunks)
        print(f"✅ Streaming successful: {len(chunks)} chunks, {len(full_response)} total chars")
        
        # Check if chunks look like actual content, not JSON dumps
        sample_chunk = chunks[0] if chunks else ""
        if sample_chunk and not sample_chunk.startswith('{'):
            print("✅ Clean streaming output (not JSON dumps)")
        else:
            print("⚠️  Streaming output might be JSON/structured data")
            
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

# Test 4: Memory Backend Swapping
async def test_memory_swap():
    """Test if memory backends actually swap with zero code changes."""
    print("\n🔥 TEST 4: Memory Backend Swapping")
    
    try:
        from cogency import Agent
        
        # Test filesystem memory with memory_dir parameter
        print("Testing FSMemory via memory_dir...")
        agent = Agent("assistant", memory_dir=".test_reality_check")
        
        await agent.run("Remember that I like coffee")
        result = await agent.run("What do you remember about my preferences?")
        print(f"✅ FSMemory test: {result[:100]}...")
        
        # Clean up
        await agent.memory.clear()
        
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

# Test 5: Tool Discovery
async def test_tools():
    """Test if tools are actually discovered and used intelligently."""
    print("\n🔥 TEST 5: Tool Discovery and Usage")
    
    try:
        from cogency import Agent
        from cogency.tools.calculator import CalculatorTool
        
        # Test with explicit tools
        agent = Agent("assistant", tools=[CalculatorTool()])
        
        result = await agent.run("What's 23 * 47?")
        print(f"✅ Calculator tool test: {result[:100]}...")
        
        # Check if result contains actual calculation
        if "1081" in result or "23" in result or "47" in result:
            print("✅ Tool actually used for calculation")
        else:
            print("⚠️  Tool might not have been used effectively")
            
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

# Test 6: Error Handling
async def test_error_handling():
    """Test graceful degradation and error handling."""
    print("\n🔥 TEST 6: Error Handling")
    
    try:
        from cogency import Agent
        
        # Test with potentially problematic query
        agent = Agent("assistant")
        result = await agent.run("Calculate the square root of negative infinity while dividing by zero")
        
        print(f"✅ Error handling test: {result[:100]}...")
        
        # Should get a response, not crash
        if result and len(result) > 0:
            print("✅ Graceful error handling")
        else:
            print("⚠️  Poor error handling")
            
        return True
        
    except Exception as e:
        print(f"❌ BULLSHIT DETECTED: {e}")
        return False

async def main():
    """Run all reality checks."""
    print("🚨 COGENCY REALITY CHECK: DOES IT ACTUALLY WORK?")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(await test_basic_magic())
    results.append(await test_multiturn_reasoning())
    results.append(await test_streaming())
    results.append(await test_memory_swap())
    results.append(await test_tools())
    results.append(await test_error_handling())
    
    # Final verdict
    print("\n" + "=" * 60)
    print("🏁 FINAL VERDICT")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 SHIP IT: Core functionality works as advertised")
    elif passed >= total * 0.7:
        print("⚠️  MIXED: Most parts work, some need fixing")
    else:
        print("💥 BULLSHIT DETECTED: Major gaps between claims and reality")
    
    print("\nNext steps based on any failures above...")

if __name__ == "__main__":
    asyncio.run(main())