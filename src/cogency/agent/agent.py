"""Agent: Canonical single interface for LLM with tools."""

import json
from contextlib import suppress
from typing import NamedTuple, Optional

from ..context.assembly import context
from ..context.persistence import persist
from ..providers import generate
from ..tools import Tool


class ToolCall(NamedTuple):
    name: str
    args: dict


def parse_tool_call(response: str) -> Optional[ToolCall]:
    """Parse tool call from LLM response."""
    if not response.strip().startswith("{"):
        return None
    
    try:
        parsed = json.loads(response.strip())
        if "tool" in parsed:
            return ToolCall(parsed["tool"], parsed.get("args", {}))
    except json.JSONDecodeError:
        pass
    
    return None


class Agent:
    """Canonical agent interface - single way to execute queries."""
    
    def __init__(
        self, 
        model: str = "gpt-4o-mini",
        tools: list[Tool] = None,
        max_iterations: int = 5,
        verbose: bool = False
    ):
        self.model = model
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.verbose = verbose
    
    async def __call__(self, query: str, user_id: str = "default") -> str:
        """Execute query with intelligent tool usage."""
        
        # Build complete context with query
        messages = context(query, user_id, self.tools)
        
        tool_results = []
        
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n=== ITERATION {iteration + 1} ===")
                
            response = await generate(messages=messages, model=self.model)
            
            if self.verbose:
                print(f"Response: {response[:100]}...")
            
            # Parse and execute tool call
            if self.tools and (tool_call := parse_tool_call(response)):
                tool = next((t for t in self.tools if t.name == tool_call.name), None)
                if tool:
                    try:
                        result = await tool.execute(**tool_call.args)
                        tool_results.append({"tool": tool_call.name, "result": result})
                        
                        if self.verbose:
                            print(f"Tool {tool_call.name}: {str(result)[:100]}...")
                        
                        # Add tool result to conversation
                        messages.append({"role": "assistant", "content": response})
                        messages.append({"role": "user", "content": f"Tool result: {result}"})
                        continue
                        
                    except Exception as e:
                        if self.verbose:
                            print(f"Tool error: {e}")
                        messages.append({"role": "assistant", "content": response})
                        messages.append({"role": "user", "content": f"Tool error: {e}"})
                        continue
            
            # Regular response - we're done
            with suppress(Exception):
                await persist(user_id, query, response)
            return response
        
        # Max iterations reached
        return "Unable to complete task within iteration limit."

