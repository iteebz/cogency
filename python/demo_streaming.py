#!/usr/bin/env python3
"""
🚀 THE STREAMING REVOLUTION DEMO 🚀

This demonstrates the world's first truly transparent agent architecture:
- Stream IS the execution, not a view of it
- Real-time visibility into every thought process  
- No black boxes, no reconstruction - pure transparency

Architecture: Every node is an async generator that yields its thinking process
as it executes. The agent becomes a pass-through of the execution stream.
"""
import asyncio
from typing import AsyncIterator, Dict, List
from cogency.llm.base import BaseLLM
from cogency.tools.base import BaseTool
from cogency.nodes.plan import plan_streaming
from cogency.nodes.reason import reason_streaming  
from cogency.nodes.act import act_streaming
from cogency.nodes.respond import respond_streaming
from cogency.nodes.reflect import reflect_streaming
from cogency.context import Context
from cogency.types import AgentState

# Mock components for demonstration
class MockLLM(BaseLLM):
    """Mock LLM that simulates different node responses."""
    
    def __init__(self):
        super().__init__(api_key="mock", key_rotator=None)
    
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Simulate different responses based on context
        last_user = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        
        if any(word in last_user.lower() for word in ["multiply", "multiplied", "times", "*", "×", "calculate", "15", "24"]):
            return '{"action": "tool_needed", "reasoning": "Math calculation required", "strategy": "calculator"}'
        else:
            return '{"action": "direct_response", "reasoning": "Simple question", "answer": "The sky appears blue due to Rayleigh scattering of light."}'
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Simulate streaming responses based on node context."""
        # Detect which node is calling by examining system prompt
        system_content = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
        last_user = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        
        if "tool schemas" in system_content.lower():
            # This is the reason node - generate a tool call
            chunks = ['TOOL_CALL: ', 'calculator(', 'expression=', '"15 * 24"', ')']
        elif "final response" in system_content.lower():
            # This is the respond node - generate conversational response  
            chunks = ["The calculation ", "shows that ", "15 × 24 = ", "360. ", "Hope this helps!"]
        elif "evaluating task" in system_content.lower():
            # This is the reflect node - generate assessment
            chunks = ['{"status": ', '"complete", ', '"assessment": ', '"Successfully calculated the result"}']
        else:
            # This is the plan node - generate planning decision
            if any(word in last_user.lower() for word in ["multiply", "multiplied", "times", "*", "×", "calculate", "15", "24"]):
                chunks = ['{"action": ', '"tool_needed", ', '"reasoning": ', '"Math calculation required", ', '"strategy": ', '"calculator"}']
            else:
                chunks = ['{"action": ', '"direct_response", ', '"reasoning": ', '"Simple question", ', '"answer": ', '"The sky appears blue due to Rayleigh scattering."}']
        
        for chunk in chunks:
            await asyncio.sleep(0.15)  # Simulate realistic network delay
            yield chunk

class MockCalculator(BaseTool):
    """Mock calculator tool for demonstration."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs mathematical calculations"
        )
    
    async def run(self, expression: str) -> Dict:
        """Required abstract method implementation."""
        return await self.validate_and_run(expression)
    
    async def validate_and_run(self, expression: str) -> Dict:
        """Simulate calculator execution."""
        await asyncio.sleep(0.5)  # Simulate computation time
        try:
            # Simple eval for demo (never do this in production!)
            result = eval(expression.replace("×", "*").replace("÷", "/"))
            return {"result": result, "expression": expression}
        except:
            return {"error": f"Invalid expression: {expression}"}
    
    def get_schema(self) -> str:
        return "calculator(expression: str) -> {'result': number} | {'error': str}"
    
    def get_usage_examples(self) -> List[str]:
        return ["calculator(expression='2 + 2')", "calculator(expression='15 * 24')"]

async def stream_full_workflow(query: str, tools: List[BaseTool] = None) -> AsyncIterator[Dict[str, str]]:
    """
    Stream a complete agent workflow through all nodes.
    This demonstrates the full transparent execution.
    """
    print(f"🎯 Query: {query}")
    print("🌊 Streaming full agent workflow...\n")
    
    llm = MockLLM()
    tools = tools or []
    
    # Initialize state
    context = Context(current_input=query)
    state: AgentState = {"context": context, "execution_trace": None}
    
    # PLAN phase
    print("🧠 PLAN NODE")
    plan_decision = None
    async for chunk in plan_streaming(state, llm, tools, yield_interval=0.0):
        format_chunk(chunk)
        if chunk["type"] == "result":
            plan_decision = chunk["data"]["decision"]
        elif chunk["type"] == "state":
            state = chunk["state"]
    
    print("\n" + "="*50)
    
    # Route based on plan decision
    try:
        import json
        decision = json.loads(plan_decision)
        if decision.get("action") == "direct_response":
            # Direct to RESPOND
            print("🎯 RESPOND NODE (Direct)")
            async for chunk in respond_streaming(state, llm, yield_interval=0.0):
                format_chunk(chunk)
        else:
            # Go through REASON → ACT → REFLECT → RESPOND
            print("🤔 REASON NODE")
            async for chunk in reason_streaming(state, llm, tools, yield_interval=0.0):
                format_chunk(chunk)
                if chunk["type"] == "state":
                    state = chunk["state"]
            
            print("\n" + "="*50)
            print("⚡ ACT NODE")
            async for chunk in act_streaming(state, tools, yield_interval=0.0):
                format_chunk(chunk)
                if chunk["type"] == "state":
                    state = chunk["state"]
            
            print("\n" + "="*50)
            print("🔍 REFLECT NODE")
            async for chunk in reflect_streaming(state, llm, yield_interval=0.0):
                format_chunk(chunk)
                if chunk["type"] == "state":
                    state = chunk["state"]
            
            print("\n" + "="*50)
            print("🎯 RESPOND NODE (Final)")
            async for chunk in respond_streaming(state, llm, yield_interval=0.0):
                format_chunk(chunk)
    
    except json.JSONDecodeError:
        print("❌ Could not parse plan decision")

def format_chunk(chunk):
    """Format streaming chunks for beautiful display."""
    chunk_type = chunk.get("type", "unknown")
    node = chunk.get("node", "unknown").upper()
    content = chunk.get("content", "")
    
    if chunk_type == "thinking":
        print(f"💭 [{node}] {content}")
    elif chunk_type == "chunk":
        print(f"📦 [{node}] {content}", end="", flush=True)
    elif chunk_type == "result":
        data = chunk.get("data", {})
        print(f"\n✅ [{node}] Result: {data}")
    elif chunk_type == "tool_call":
        data = chunk.get("data", {})
        print(f"🔧 [{node}] Tool Call: {data}")
    elif chunk_type == "state":
        print(f"🔄 [{node}] State updated")

async def main():
    """Run the streaming revolution demo."""
    print("🚀" + "="*60 + "🚀")
    print("    THE STREAMING REVOLUTION: TRANSPARENT AGENTS")
    print("🚀" + "="*60 + "🚀\n")
    
    calculator = MockCalculator()
    
    # Demo 1: Direct response (no tools needed)
    print("📋 DEMO 1: Direct Response")
    await stream_full_workflow("Why is the sky blue?")
    
    print("\n\n📋 DEMO 2: Tool-based workflow")  
    await stream_full_workflow("What is 15 multiplied by 24?", [calculator])
    
    print("\n\n🎉 REVOLUTION COMPLETE!")
    print("This is what transparent AI looks like. No black boxes.")
    print("The stream IS the execution. Every thought, every step, real-time.")

if __name__ == "__main__":
    asyncio.run(main())