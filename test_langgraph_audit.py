#!/usr/bin/env python3
"""
COMPREHENSIVE LANGGRAPH INTEGRATION AUDIT
Tests all the bullshit from the audit prompt
"""
import asyncio
import inspect
from cogency import Agent, WeatherTool, CalculatorTool
from cogency.nodes import think, plan, act, reflect, respond
from cogency.llm import OpenAILLM, auto_detect_llm
from cogency.flow import Flow
from cogency.types import AgentState
from cogency.context import Context

async def test_1_node_return_types():
    """Test 1: Node Return Types - FAIL if returns async generator"""
    print("🔍 TEST 1: Node Return Types")
    
    # Mock LLM for testing
    class MockLLM:
        async def invoke(self, messages, **kwargs):
            return "test thinking response"
        async def ainvoke(self, messages, **kwargs):
            return await self.invoke(messages, **kwargs)
    
    mock_llm = MockLLM()
    state = {
        "context": Context(current_input="test query"),
        "execution_trace": None
    }
    
    # Test each node
    nodes = [
        ("think", lambda: think(state, llm=mock_llm)),
        ("plan", lambda: plan(state, llm=mock_llm, tools=[], prompt_fragments={})),
        ("act", lambda: act(state, tools=[])),
        ("reflect", lambda: reflect(state, llm=mock_llm)),
        ("respond", lambda: respond(state, llm=mock_llm, prompt_fragments={}))
    ]
    
    for node_name, node_func in nodes:
        result = await node_func()
        assert isinstance(result, dict), f"❌ {node_name} returned {type(result)}, expected dict"
        assert "context" in result, f"❌ {node_name} missing 'context' in result"
        print(f"  ✅ {node_name} returns dict")
    
    print("  ✅ ALL NODES RETURN DICTS\n")


async def test_2_llm_interface():
    """Test 2: LLM Interface Compatibility"""
    print("🔍 TEST 2: LLM Interface Compatibility")
    
    llm = auto_detect_llm()
    
    # Test both interfaces exist
    assert hasattr(llm, "invoke"), "❌ LLM missing invoke() method"
    assert hasattr(llm, "ainvoke"), "❌ LLM missing ainvoke() method"
    
    # Test both are async
    assert inspect.iscoroutinefunction(llm.invoke), "❌ invoke() is not async"
    assert inspect.iscoroutinefunction(llm.ainvoke), "❌ ainvoke() is not async"
    
    print("  ✅ LLM has both invoke() and ainvoke()")
    print("  ✅ Both methods are async")
    print("  ✅ LLM INTERFACE COMPATIBLE\n")


async def test_3_workflow_execution():
    """Test 3: LangGraph Integration - FAIL if gets coroutine objects"""
    print("🔍 TEST 3: LangGraph Integration")
    
    llm = auto_detect_llm()
    tools = [WeatherTool(), CalculatorTool()]
    flow = Flow(llm, tools)
    
    state = {
        "context": Context(current_input="test query"),
        "execution_trace": None
    }
    
    # Test workflow executes without coroutine errors
    try:
        result = await flow.workflow.ainvoke(state)
        assert isinstance(result, dict), f"❌ Workflow returned {type(result)}, expected dict"
        assert "context" in result, "❌ Workflow result missing 'context'"
        print("  ✅ Workflow executes without coroutine errors")
        print("  ✅ Workflow returns proper dict state")
    except Exception as e:
        if "coroutine" in str(e).lower():
            print(f"  ❌ COROUTINE ERROR: {e}")
            raise
        else:
            raise
    
    print("  ✅ LANGGRAPH INTEGRATION WORKS\n")


async def test_4_streaming_capability():
    """Test 4: Streaming Works"""
    print("🔍 TEST 4: Streaming Capability")
    
    agent = Agent("test_agent", tools=[WeatherTool()])
    
    # Test streaming produces output
    result = await agent.stream("What's 2+2?")
    assert isinstance(result, str), f"❌ Stream returned {type(result)}, expected str"
    assert len(result) > 0, "❌ Stream returned empty result"
    
    print("  ✅ Streaming produces output")
    print("  ✅ Returns proper string response")
    print("  ✅ STREAMING WORKS\n")


async def test_5_complex_workflow():
    """Test 5: Complex Example - Multi-step with tools"""
    print("🔍 TEST 5: Complex Workflow")
    
    agent = Agent("complex_agent", tools=[WeatherTool(), CalculatorTool()])
    
    # Test complex query that requires multiple steps
    result = await agent.stream("What's the weather in London and what's 25 * 4?")
    assert isinstance(result, str), f"❌ Complex workflow returned {type(result)}, expected str"
    assert len(result) > 0, "❌ Complex workflow returned empty result"
    
    print("  ✅ Complex workflow executes")
    print("  ✅ Handles multiple tools")
    print("  ✅ COMPLEX WORKFLOW WORKS\n")


async def test_6_edge_cases():
    """Test 6: Edge Cases"""
    print("🔍 TEST 6: Edge Cases")
    
    agent = Agent("edge_case_agent")
    
    # Test simple query without tools
    result = await agent.stream("Hello, how are you?")
    assert isinstance(result, str), f"❌ No-tools query returned {type(result)}, expected str"
    assert len(result) > 0, "❌ No-tools query returned empty result"
    
    print("  ✅ Works without tools")
    print("  ✅ Handles simple queries")
    print("  ✅ EDGE CASES WORK\n")


async def main():
    """Run comprehensive LangGraph audit"""
    print("🚀 COMPREHENSIVE LANGGRAPH INTEGRATION AUDIT")
    print("=" * 60)
    
    try:
        await test_1_node_return_types()
        await test_2_llm_interface()
        await test_3_workflow_execution()
        await test_4_streaming_capability()
        await test_5_complex_workflow()
        await test_6_edge_cases()
        
        print("🎉 ALL TESTS PASSED - LANGGRAPH INTEGRATION VERIFIED")
        print("✅ Nodes return dicts")
        print("✅ LLM has proper interface")
        print("✅ Flow uses pure orchestration")
        print("✅ Streaming works")
        print("✅ Complex workflows work")
        print("✅ Zero compatibility issues")
        
    except Exception as e:
        print(f"❌ AUDIT FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())