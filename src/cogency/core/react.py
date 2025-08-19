"""ReAct Algorithm - Canonical XML Protocol Implementation."""

import time
from contextlib import suppress

from ..context.assembly import context
from ..context.persistence import persist


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
    """Canonical XML sectioned ReAct algorithm - Zero ceremony."""
    import os

    from ..context import working

    # Get user-scoped working memory
    tool_results = working.get(user_id)

    # Metrics tracking for A/B testing
    start_time = time.perf_counter()
    tool_sequence = []
    reasoning_type = (
        "emergent" if os.getenv("EMERGENT_REASONING", "true").lower() == "true" else "basic"
    )

    for iteration in range(max_iterations):
        # Iteration start with metrics
        yield {
            "type": "iteration",
            "number": iteration + 1,
            "reasoning_type": reasoning_type,
            "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
        }

        # Context assembly with system capabilities
        prompt = context.assemble(query, user_id, tool_results, tools, iteration)
        yield {"type": "context", "length": len(prompt)}

        # Stream XML sections with canonical boundary detection
        from ..lib.streaming import stream_xml_sections

        messages = [{"role": "user", "content": prompt}]
        stream_result = await stream_xml_sections(llm, messages)

        if stream_result.failure:
            yield {"type": "error", "source": "llm", "message": stream_result.error}
            return

        sections = stream_result.unwrap()

        # Yield thinking content as it was streamed
        if sections.get("thinking"):
            yield {"type": "thinking", "content": sections["thinking"]}

        # Parse and execute tools if present
        if sections.get("tools"):
            await _execute_tools_from_json(
                sections["tools"], tool_results, tools, user_id, tool_sequence, start_time
            )

        # Complete when response present and no tools
        if sections.get("response") and not sections.get("tools"):
            conversation_id = f"{user_id}_{int(time.time())}"
            final_answer = sections.get("response") or sections.get("thinking")

            with suppress(Exception):
                await persist(user_id, query, final_answer)

            yield {
                "type": "complete",
                "answer": final_answer,
                "conversation_id": conversation_id,
                "metrics": {
                    "iterations_used": iteration + 1,
                    "tools_executed": tool_sequence,
                    "reasoning_time_ms": int((time.perf_counter() - start_time) * 1000),
                    "reasoning_type": reasoning_type,
                    "logical_sequence": _validate_tool_sequence(tool_sequence),
                    "completion_reason": "explicit_completion",
                },
            }
            return

    # Max iterations reached - complete with reasoning
    conversation_id = f"{user_id}_{int(time.time())}"
    final_reasoning = sections.get("thinking", "Maximum iterations reached")

    with suppress(Exception):
        await persist(user_id, query, final_reasoning)

    yield {
        "type": "complete",
        "answer": final_reasoning,
        "conversation_id": conversation_id,
        "metrics": {
            "iterations_used": max_iterations,
            "tools_executed": tool_sequence,
            "reasoning_time_ms": int((time.perf_counter() - start_time) * 1000),
            "reasoning_type": reasoning_type,
            "logical_sequence": _validate_tool_sequence(tool_sequence),
            "completion_reason": "max_iterations",
        },
    }


async def _generate_response(llm, prompt: str):
    """Generate response using configured LLM."""
    messages = [{"role": "user", "content": prompt}]
    return await llm.generate(messages)


async def _execute_tools_from_json(
    tools_json: str,
    tool_results: list,
    tools: dict,
    user_id: str,
    tool_sequence: list,
    start_time: float,
) -> bool:
    """Execute tools from JSON string."""
    import json

    try:
        tools_list = json.loads(tools_json)
        if not isinstance(tools_list, list):
            tools_list = [tools_list]

        for tool_spec in tools_list:
            await _execute_json_tool(tool_spec, tool_results, tools, user_id)

            # Update tool sequence tracking
            if tool_results:
                last_result = tool_results[-1]
                tool_name = last_result["tool"]
                tool_sequence.append(
                    {
                        "name": tool_name,
                        "success": "result" in last_result,
                        "timestamp_ms": int((time.perf_counter() - start_time) * 1000),
                    }
                )

        return True

    except Exception as e:
        # Log error but don't fail the entire iteration
        error_entry = {"tool": "parse_error", "error": f"Failed to parse tools JSON: {str(e)}"}
        tool_results.append(error_entry)
        return False


async def _execute_json_tool(
    tool_spec: dict, tool_results: list, tools: dict, user_id: str
) -> bool:
    """Execute tool from JSON specification - zero ceremony."""
    tool_name = tool_spec.get("name")
    args = tool_spec.get("args", {})

    if not tool_name:
        result_entry = {"tool": "unknown", "args": {}, "error": "Missing tool name"}
        tool_results.append(result_entry)
        return True

    if tool_name not in tools:
        result_entry = {"tool": tool_name, "args": args, "error": f"Unknown tool: {tool_name}"}
        tool_results.append(result_entry)
        return True

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

    # Update user-scoped working memory
    from ..context import working

    working.update(user_id, tool_results)

    return True


def _validate_tool_sequence(tool_sequence: list) -> dict:
    """Validate logical tool sequence for workflow analysis."""
    if not tool_sequence:
        return {"valid": True, "reason": "no_tools_used", "efficiency_score": 1.0}

    # Common logical patterns
    logical_patterns = {
        "create_read": ["file_write", "file_read"],
        "search_scrape": ["search", "scrape"],
        "list_read": ["file_list", "file_read"],
    }

    tool_names = [t["name"] for t in tool_sequence]

    # Check for logical patterns
    for pattern_name, pattern in logical_patterns.items():
        if all(tool in tool_names for tool in pattern):
            return {"valid": True, "pattern": pattern_name, "efficiency_score": 0.9}

    # Check for tool repetition (inefficiency)
    if len(set(tool_names)) < len(tool_names):
        repeated_tools = [name for name in set(tool_names) if tool_names.count(name) > 1]
        return {
            "valid": True,
            "reason": "repeated_tools",
            "repeated": repeated_tools,
            "efficiency_score": 0.6,
        }

    # Valid sequence
    return {"valid": True, "reason": "valid_sequence", "efficiency_score": 0.8}
