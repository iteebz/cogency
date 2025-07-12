#!/usr/bin/env python3
"""
Mock test for streaming-first architecture.
Demonstrates the stream flow without requiring real API keys.
"""
import asyncio
from typing import AsyncIterator, Dict, List
from cogency.llm.base import BaseLLM
from cogency.nodes.plan import plan_streaming
from cogency.context import Context
from cogency.types import AgentState

class MockLLM(BaseLLM):
    """Mock LLM that simulates streaming responses."""
    
    def __init__(self):
        super().__init__(api_key="mock", key_rotator=None)
    
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return '{"action": "direct_response", "reasoning": "Simple math", "answer": "2 + 2 = 4"}'
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Simulate streaming JSON response chunk by chunk."""
        chunks = [
            '{"action":',
            ' "direct_response",',
            ' "reasoning":',
            ' "Simple math",',
            ' "answer":',
            ' "2 + 2 = 4"}'
        ]
        
        for chunk in chunks:
            await asyncio.sleep(0.1)  # Simulate network delay
            yield chunk

async def test_streaming_mock():
    print("🚀 Testing streaming-first architecture (Mock)...")
    print("=" * 50)
    
    # Setup mock components
    llm = MockLLM()
    context = Context(current_input="What is 2 + 2?")
    initial_state: AgentState = {
        "context": context,
        "execution_trace": None,
    }
    
    # Test the streaming plan node
    try:
        async for chunk in plan_streaming(initial_state, llm, []):
            chunk_type = chunk.get("type", "unknown")
            node = chunk.get("node", "unknown")
            content = chunk.get("content", "")
            
            if chunk_type == "thinking":
                print(f"💭 [{node.upper()}] {content}")
            elif chunk_type == "chunk":
                print(f"📦 [{node.upper()}] {content}", end="", flush=True)
            elif chunk_type == "result":
                print(f"\n✅ [{node.upper()}] Result: {chunk.get('data', {})}")
            elif chunk_type == "state":
                print(f"🔄 [{node.upper()}] State updated")
                
        print("\n🎉 Stream completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_mock())