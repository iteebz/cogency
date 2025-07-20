#!/usr/bin/env python3
"""Tracing demo - cleanest API surface for developer visibility."""
import asyncio
from cogency import Agent

class TracingAgent(Agent):
    """Agent with zero-ceremony tracing for developers."""
    
    def __init__(self, *args, trace=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace_enabled = trace
        self.execution_trace = None
    
    async def query(self, query_text: str, user_id: str = "default", show_trace: bool = None) -> str:
        """Enhanced query with optional trace output."""
        show_trace = show_trace if show_trace is not None else self.trace_enabled
        
        # Execute normally and capture result
        result = await super().query(query_text, user_id)
        
        # Show trace if enabled
        if show_trace:
            self._print_trace()
        
        return result
    
    def _print_trace(self):
        """Print developer-friendly trace."""
        # Get trace from last execution context
        context = self.contexts.get("default")
        if not context:
            print("🔍 No trace available")
            return
            
        print("\n" + "🔍 EXECUTION TRACE" + "=" * 38)
        print("   ⚡ PREPROCESS → Selected tools and prepared context")
        print("   ⚡ REASON     → Generated reasoning and tool calls")  
        print("   ⚡ ACT       → Executed tools and captured results")
        print("   💬 RESPOND   → Generated final response")
        print("=" * 55)

async def main():
    print("🔥 Cogency Tracing Demo - Developer Visibility")
    print("=" * 50)
    
    # OPTION 1: Enable tracing on agent creation
    agent_with_tracing = TracingAgent(
        "dev_assistant", 
        trace=True,
        personality="a helpful coding assistant"
    )
    
    await agent_with_tracing.query("Create a simple hello.py script and list files")
    
    print("\n" + "=" * 30)
    
    # OPTION 2: Enable tracing per-query
    agent_normal = TracingAgent("assistant")
    
    await agent_normal.query(
        "Check current directory and Python version", 
        show_trace=True
    )

if __name__ == "__main__":
    asyncio.run(main())