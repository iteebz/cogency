"""Agent: Stateless ReAct loops with tool execution."""

from typing import Any

from ..providers.openai import generate
from ..tools import BASIC_TOOLS, Tool
from .parser import parse
from .prompts import prompt


class ReAct:
    """Stateless ReAct - Reason + Act with tools."""

    def __init__(self, tools: list[Tool] = None, user_id: str = "default", verbose: bool = False):
        self.tools = {tool.name: tool for tool in (tools or BASIC_TOOLS)}
        self.user_id = user_id
        self.verbose = verbose

    async def solve(self, task: str, max_iterations: int = 5) -> dict[str, Any]:
        """Solve task using stateless ReAct loops."""
        tool_results = []

        for iteration in range(max_iterations):
            if self.verbose:
                print(f"\n=== ITERATION {iteration + 1}/{max_iterations} ===")

            # Build prompt with context injection
            full_prompt = prompt(task, self.user_id, tool_results, self.tools)

            # Get LLM response
            try:
                response = await generate(full_prompt)
                parsed = parse(response)

                if self.verbose:
                    action = parsed.get("action", {})
                    print(f"Action: {action.get('type', 'unknown')} - {action.get('name', 'N/A')}")

                # Check for completion
                if "final_answer" in parsed:
                    return {
                        "final_answer": parsed["final_answer"],
                        "completed": True,
                        "iterations": iteration + 1,
                        "tool_calls": len(tool_results),
                    }

                # Execute tool if specified
                action = parsed.get("action", {})
                if action.get("type") == "tool_call":
                    result = await self._execute_tool(tool_results, action, iteration)

                    if self.verbose and result:
                        if "result" in result:
                            print(f"Tool result: {str(result['result'])[:100]}...")
                        else:
                            print(f"Tool error: {result.get('error', 'Unknown')}")

                elif action.get("type") == "continue":
                    # Continue reasoning without tool execution
                    if self.verbose:
                        print("Continuing reasoning...")
                    continue

            except Exception as e:
                # Emergency fallback - log error and continue
                tool_results.append(
                    {
                        "tool": "system",
                        "error": f"Response parsing failed: {str(e)}",
                        "iteration": iteration,
                    }
                )

        # Max iterations reached
        return {
            "final_answer": None,
            "completed": False,
            "iterations": max_iterations,
            "tool_calls": len(tool_results),
        }

    async def _execute_tool(
        self, tool_results: list[dict], action: dict[str, Any], iteration: int
    ) -> dict:
        """Execute tool and append result."""
        tool_name = action.get("name")
        tool_args = action.get("args", {})

        result_entry = {"tool": tool_name, "args": tool_args, "iteration": iteration}

        if tool_name in self.tools:
            try:
                result = await self.tools[tool_name].execute(**tool_args)
                result_entry["result"] = result
            except Exception as e:
                result_entry["error"] = str(e)
        else:
            result_entry["error"] = f"Unknown tool: {tool_name}"

        tool_results.append(result_entry)
        return result_entry
