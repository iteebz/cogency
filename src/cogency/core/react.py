"""ReAct algorithm implementation - pure functions."""

import time
from contextlib import suppress

from ..context import context, persist
from ..lib.parsing import parse_with_signature


async def react(llm, tools, query: str, user_id: str, max_iterations: int = 5):
    """ReAct algorithm - returns final result."""
    from ..context import working

    result = None
    async for event in stream_react(llm, tools, query, user_id, max_iterations):
        if event["type"] in ["complete", "error"]:
            result = event
            break

    # Clear working memory after task completion (privacy + isolation)
    working.clear(user_id)
    return result


async def stream_react(llm, tools, query: str, user_id: str, max_iterations: int = 5):
    """ReAct algorithm - streaming interface."""
    from ..context import working

    # Get user-scoped working memory
    tool_results = working.get(user_id)

    for iteration in range(max_iterations):
        # Iteration start
        yield {"type": "iteration", "number": iteration + 1}

        # Context assembly
        ctx = context.assemble(query, user_id, tool_results)
        yield {"type": "context", "length": len(ctx)}

        # LLM generation with security-aware reasoning on first iteration
        prompt = _build_prompt(query, ctx, tool_results, tools, iteration)
        llm_result = await _generate_response(llm, prompt)

        if llm_result.failure:
            yield {"type": "error", "source": "llm", "message": llm_result.error}
            return

        response = llm_result.unwrap()
        yield {"type": "reasoning", "content": response}

        # Check for completion
        if "final answer" in response.lower():
            final = _extract_final_answer(response)
            conversation_id = f"{user_id}_{int(time.time())}"

            # Persist before yielding final answer
            with suppress(Exception):
                await persist(user_id, query, final)

            # Final event with conversation context
            yield {"type": "complete", "answer": final, "conversation_id": conversation_id}
            return

        # Tool execution
        tool_used = await _execute_tool(response, tool_results, tools, user_id)
        if tool_used and tool_results:
            last_result = tool_results[-1]
            yield {
                "type": "tool",
                "name": last_result["tool"],
                "success": "result" in last_result,
                "data": last_result.get("result", last_result.get("error")),
            }
        elif not tool_used:
            # No tool, complete with response
            conversation_id = f"{user_id}_{int(time.time())}"

            # Persist before yielding complete
            with suppress(Exception):
                await persist(user_id, query, response)

            yield {"type": "complete", "answer": response, "conversation_id": conversation_id}
            return

    # Max iterations - complete with last response
    conversation_id = f"{user_id}_{int(time.time())}"

    # Persist before yielding max iterations complete
    with suppress(Exception):
        await persist(user_id, query, response)

    yield {"type": "complete", "answer": response, "conversation_id": conversation_id}


async def _generate_response(llm, prompt: str):
    """Generate response using configured LLM."""
    messages = [{"role": "user", "content": prompt}]
    return await llm.generate(messages)


def _build_prompt(query: str, ctx: str, tool_results: list, tools: dict, iteration: int = 0) -> str:
    """Build ReAct prompt with context and tools."""
    parts = []
    if ctx.strip():
        parts.append(ctx)

    # Security assessment on first iteration only
    if iteration == 0:
        from ..lib.security import SECURITY_ASSESSMENT

        parts.append(SECURITY_ASSESSMENT)

    parts.append(f"TASK: {query}")

    if tools:
        tools_text = "\n".join(f"- {t.name}: {t.description}" for t in tools.values())
        parts.append(f"TOOLS:\n{tools_text}")

    if tool_results:
        results_text = "PREVIOUS TOOLS:\n"
        for r in tool_results[-3:]:
            name = r["tool"]
            if "result" in r:
                results_text += f"✅ {name}: {str(r['result'])[:200]}...\n"
            else:
                results_text += f"❌ {name}: {str(r.get('error', 'Unknown error'))}\n"
        parts.append(results_text)

    prompt = "\n\n".join(parts)

    if iteration == 0:
        return f"""{prompt}

First assess if this request is safe using the security evaluation above. If unsafe, politely refuse and explain why. If safe, proceed with normal reasoning.

Think step by step. Use tools when needed by writing:
USE: tool_name(arg1="value1", arg2="value2")

When complete, write your final answer."""
    return f"""{prompt}

Think step by step. Use tools when needed by writing:
USE: tool_name(arg1="value1", arg2="value2")

When complete, write your final answer."""


async def _execute_tool(response: str, tool_results: list, tools: dict, user_id: str) -> bool:
    """Execute tool from response. Returns True if tool was used."""
    import re

    match = re.search(r"USE:\s*(\w+)\(", response, re.IGNORECASE)
    if not match:
        return False

    tool_name = match.group(1)
    if tool_name not in tools:
        result_entry = {"tool": tool_name, "args": {}, "error": f"Unknown tool: {tool_name}"}
        tool_results.append(result_entry)
        return True

    # Use signature-based parsing with the actual tool instance
    parse_result = parse_with_signature(response, tools[tool_name])
    if parse_result.failure:
        return False

    call_data = parse_result.unwrap()
    args = call_data["args"]

    result_entry = {"tool": tool_name, "args": args}

    try:
        result = await tools[tool_name].execute(**args)
        if result.success:
            result_entry["result"] = result.unwrap()
        else:
            result_entry["error"] = result.error
    except Exception as e:
        result_entry["error"] = str(e)

    tool_results.append(result_entry)

    # Update user-scoped working memory after tool execution
    from ..context import working

    working.update(user_id, tool_results)

    return True


def _extract_final_answer(response: str) -> str:
    """Extract final answer from response."""
    lower_response = response.lower()
    if "final answer:" in lower_response:
        # Find the position of "final answer:" (case insensitive)
        pos = lower_response.find("final answer:")
        return response[pos + len("final answer:") :].strip()
    return response
