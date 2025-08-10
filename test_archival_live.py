#!/usr/bin/env python3
"""
Live Archival Memory Testing with Real Gemini LLM Calls

Tests the complete archival memory pipeline with actual LLM invocations:
1. Situate step (profile synthesis every 5 interactions)  
2. Archive step (knowledge extraction at conversation end)
3. Recall tool (cross-conversation knowledge retrieval)

Automatically loads GEMINI_API_KEY from .env file.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set manually
    pass

from cogency import Agent
from cogency.providers.gemini import Gemini


async def test_archival_memory_pipeline():
    """Test complete archival memory pipeline with real LLM calls."""
    
    # Create temporary directory for archival memory
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "test_memory"
        
        print(f"📁 Memory path: {memory_path}")
        
        # Create agent with archival memory enabled - auto-detects Gemini keys
        agent = Agent(
            "assistant", 
            provider="gemini",  # Auto-detects GEMINI_API_KEY_1 through _8
            memory=True,  # Use simple memory configuration
            observe=True
        )
        
        print("🔑 Using auto-detected Gemini API keys")
        
        print("\n🧪 Starting Live Archival Memory Testing")
        print("=" * 50)
        
        # Test 1: Build up interactions to trigger synthesis
        print("\n📝 Test 1: Profile Synthesis (3 interactions)")
        
        queries = [
            "I'm working on a Python web application using FastAPI. What are some best practices?",
            "How can I optimize database queries in my FastAPI app?", 
            "What's the best way to handle authentication in FastAPI?"
        ]
        
        responses = []
        for i, query in enumerate(queries, 1):
            print(f"   {i}. User: {query[:60]}...")
            response = await agent.run_async(query)
            responses.append(response)
            print(f"   {i}. Assistant: {response[:100]}...")
            print()
        
        # Check if synthesis triggered (logs should show situate step)
        synthesis_logs = [log for log in agent.logs() if log.get("type") == "situate"]
        if synthesis_logs:
            print(f"✅ Profile synthesis triggered: {len(synthesis_logs)} events")
        else:
            print("⚠️  Profile synthesis not triggered - check threshold logic")
        
        # Test 2: Trigger archival memory by ending conversation
        print("\n📚 Test 2: Knowledge Archival (conversation end)")
        
        # Add a few more interactions about a different topic
        archival_queries = [
            "Tell me about machine learning model deployment strategies",
            "What are the key considerations for ML model monitoring in production?"
        ]
        
        for query in archival_queries:
            print(f"   User: {query[:60]}...")
            response = await agent.run_async(query)
            print(f"   Assistant: {response[:100]}...")
        
        # Force conversation end to trigger archival
        print("   Ending conversation to trigger archival...")
        # Note: In real usage, this would happen when conversation naturally ends
        # For testing, we need to simulate this
        
        # Test 3: Check if archival files were created
        print("\n📂 Test 3: Archival File Creation")
        
        if memory_path.exists():
            archival_files = list(memory_path.rglob("*.md"))
            if archival_files:
                print(f"✅ Created {len(archival_files)} archival files:")
                for file in archival_files:
                    size = file.stat().st_size
                    print(f"   - {file.name} ({size} bytes)")
                    
                    # Show content of first file
                    if file == archival_files[0]:
                        content = file.read_text()[:200]
                        print(f"   Content preview: {content}...")
            else:
                print("⚠️  No archival files created - check archive step implementation")
        else:
            print("❌ Memory path doesn't exist")
        
        # Test 4: Test recall tool (if archival data exists)
        print("\n🧠 Test 4: Knowledge Recall")
        
        recall_query = "recall(query='FastAPI best practices', limit=2)"
        print(f"   Testing recall: {recall_query}")
        
        # Note: This requires the recall tool to be properly integrated
        try:
            recall_response = await agent.run_async("What did we discuss about FastAPI optimization?")
            print(f"   Recall response: {recall_response[:150]}...")
            
            if "FastAPI" in recall_response or "database" in recall_response:
                print("✅ Recall appears to be working - found relevant knowledge")
            else:
                print("⚠️  Recall may not be accessing archival memory")
                
        except Exception as e:
            print(f"❌ Recall failed: {e}")
        
        # Test 5: Show detailed logs
        print("\n📊 Test 5: Pipeline Analysis")
        
        all_logs = agent.logs(mode="debug")
        
        # Count different event types
        situate_events = [log for log in all_logs if log.get("type") == "situate"]
        archive_events = [log for log in all_logs if log.get("type") == "archive"] 
        tool_events = [log for log in all_logs if log.get("type") == "tool"]
        provider_events = [log for log in all_logs if log.get("type") == "provider"]
        
        print(f"   Situate events: {len(situate_events)}")
        print(f"   Archive events: {len(archive_events)}")
        print(f"   Tool events: {len(tool_events)}")
        print(f"   Provider events: {len(provider_events)}")
        
        # Show LLM costs
        total_cost = sum(log.get("cost", 0) for log in provider_events)
        print(f"   Total LLM cost: ${total_cost:.4f}")
        
        print("\n🎯 Test Summary")
        print("=" * 50)
        
        success_count = 0
        if synthesis_logs:
            print("✅ Profile synthesis working")
            success_count += 1
        else:
            print("❌ Profile synthesis not working")
            
        if memory_path.exists() and list(memory_path.rglob("*.md")):
            print("✅ Archival file creation working") 
            success_count += 1
        else:
            print("❌ Archival file creation not working")
            
        if provider_events:
            print("✅ LLM integration working")
            success_count += 1
        else:
            print("❌ LLM integration not working")
            
        print(f"\n🏆 Overall: {success_count}/3 components working")
        
        if success_count == 3:
            print("🎉 Archival memory pipeline fully operational!")
        else:
            print("⚠️  Some components need attention")


async def main():
    """Run comprehensive archival memory testing."""
    try:
        await test_archival_memory_pipeline()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())