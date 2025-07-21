#!/usr/bin/env python3
"""Test adaptive routing behavior - fast_react vs deep_react."""

import asyncio
from cogency.llm.mock import MockLLM
from cogency.nodes.preprocess import preprocess_node
from cogency.types import AgentState, Context
from cogency.tools.base import BaseTool


class MockSearchTool(BaseTool):
    """Mock search tool for testing."""
    
    def __init__(self):
        super().__init__("search", "Search for information", "🔍")
    
    def get_schema(self):
        return "search(query: str) -> str"
    
    def get_usage_examples(self):
        return ["search('weather today')", "search('python tutorials')"]
    
    async def run(self, query: str) -> str:
        return f"Search results for: {query}"


async def test_routing():
    """Test that simple queries get fast_react, complex queries get deep_react."""
    
    # Setup
    llm = MockLLM()
    tools = [MockSearchTool()]
    
    # Test cases
    test_cases = [
        {
            "query": "What is the weather today?",
            "expected_mode": "fast",
            "description": "Simple lookup query"
        },
        {
            "query": "Analyze the economic implications of AI development and compare different regulatory approaches across multiple countries, synthesizing policy recommendations.",
            "expected_mode": "deep", 
            "description": "Complex analysis query"
        },
        {
            "query": "Search for Python tutorials",
            "expected_mode": "fast",
            "description": "Direct search request"
        },
        {
            "query": "Compare and contrast the philosophical implications of different AI consciousness theories, synthesize insights from neuroscience and cognitive psychology, then provide recommendations for ethical frameworks.",
            "expected_mode": "deep",
            "description": "Multi-step synthesis task"
        }
    ]
    
    print("🧪 Testing Adaptive Routing\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"Test {i}: {case['description']}")
        print(f"Query: {case['query'][:60]}...")
        
        # Mock LLM response - simulate the classification 
        if case["expected_mode"] == "fast":
            llm.response = '{"respond_directly": false, "react_mode": "fast", "selected_tools": ["search"], "reasoning": "Simple query"}'
        else:
            llm.response = '{"respond_directly": false, "react_mode": "deep", "selected_tools": ["search"], "reasoning": "Complex analysis needed"}'
        
        # Create test state
        context = Context()
        context.current_input = case["query"]
        state = AgentState(
            query=case["query"],
            context=context
        )
        
        # Run preprocessing
        result = await preprocess_node(state, llm=llm, tools=tools)
        
        # Validate routing
        actual_mode = result.get("react_mode", "not_set")
        expected_mode = case["expected_mode"]
        
        if actual_mode == expected_mode:
            print(f"✅ PASS: {actual_mode} mode")
        else:
            print(f"❌ FAIL: Expected {expected_mode}, got {actual_mode}")
        
        print(f"Next node: {result.get('next_node', 'not_set')}")
        print()


async def test_cognitive_state():
    """Test cognitive state initialization with different react_modes."""
    from cogency.nodes.reasoning.cognitive_state import initialize_cognitive_state
    
    print("🧠 Testing Cognitive State Adaptation\n")
    
    # Test fast_react
    fast_state = {}
    fast_cognitive = initialize_cognitive_state(fast_state, react_mode="fast")
    
    print("Fast React Cognitive State:")
    print(f"  Max history: {fast_cognitive['max_history']}")
    print(f"  Max failures: {fast_cognitive['max_failures']}")
    print(f"  React mode: {fast_cognitive['react_mode']}")
    
    # Test deep_react  
    deep_state = {}
    deep_cognitive = initialize_cognitive_state(deep_state, react_mode="deep")
    
    print("\nDeep React Cognitive State:")
    print(f"  Max history: {deep_cognitive['max_history']}")
    print(f"  Max failures: {deep_cognitive['max_failures']}")
    print(f"  React mode: {deep_cognitive['react_mode']}")
    
    # Validate differences
    if fast_cognitive['max_history'] < deep_cognitive['max_history']:
        print("\n✅ PASS: Fast react uses less memory than deep react")
    else:
        print("\n❌ FAIL: Memory limits not properly differentiated")


async def main():
    """Run all tests."""
    await test_routing()
    await test_cognitive_state()
    
    print("🎉 Adaptive Reasoning Tests Complete!")
    print("\nArchitecture Summary:")
    print("  • 3-way routing: Direct → Fast React → Deep React")
    print("  • LLM classifies complexity in preprocess node")
    print("  • Reason node adapts behavior based on react_mode")
    print("  • Memory limits scale with cognitive complexity")


if __name__ == "__main__":
    asyncio.run(main())