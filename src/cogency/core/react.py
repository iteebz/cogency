"""ReAct Algorithm - Canonical XML Protocol Implementation."""

import time
import uuid

from ..context import conversation, working
from ..context.assembly import context
from ..context.memory import memory
from ..lib.streaming import stream_xml_sections
from .execute import execute_tools


async def react(
    llm,
    tools,
    query: str,
    user_id: str = None,
    max_iterations: int = 5,
    conversation_id: str = None,
    test_mode: bool = False,
):
    """ReAct algorithm - returns final result."""
    task_id = str(uuid.uuid4())

    result = None
    async for event in stream_react(
        llm, tools, query, user_id, max_iterations, conversation_id, task_id, test_mode
    ):
        if event["type"] in ["complete", "error"]:
            result = event
            break

    # Clear working memory after task completion (privacy + isolation)
    working.clear(task_id)
    return result


async def stream_react(
    llm,
    tools,
    query: str,
    user_id: str = None,
    max_iterations: int = 5,
    conversation_id: str = None,
    task_id: str = None,
    test_mode: bool = False,
):
    """Canonical XML sectioned ReAct algorithm - Zero ceremony."""

    # Handle optional parameters with canonical defaults
    if user_id is None:
        user_id = "default"
    if conversation_id is None:
        conversation_id = f"{user_id}_{int(time.time())}"  # Unique conversation per invocation
    if task_id is None:
        task_id = str(uuid.uuid4())

    for iteration in range(max_iterations):
        yield {"type": "iteration", "number": iteration + 1}

        # Context assembly with system capabilities
        messages = context.assemble(
            query, user_id, conversation_id, task_id, tools, iteration + 1, test_mode
        )
        yield {"type": "context", "length": len(str(messages))}

        # Stream XML sections with canonical boundary detection
        stream_result = await stream_xml_sections(llm, messages)

        if stream_result.failure:
            yield {"type": "error", "source": "llm", "message": stream_result.error}
            return

        sections = stream_result.unwrap()

        # Yield thinking content as it was streamed
        if sections.get("thinking"):
            yield {"type": "thinking", "content": sections["thinking"]}

        # Binary decision: Either execute tools OR complete with response
        tools_json = (sections.get("tools") or "[]").strip()

        # If tools requested, execute them and continue to next iteration
        if tools_json and tools_json != "[]":
            execution_result = await execute_tools(task_id, tools_json, tools, user_id)

            if execution_result.failure:
                yield {"type": "error", "source": "execution", "message": execution_result.error}
                return

            continue

        # No tools needed - complete with final response
        if sections.get("response"):
            response = sections["response"]

            conversation.add(conversation_id, "user", query)
            conversation.add(conversation_id, "assistant", response)

            # Learn from successful interaction (background, non-blocking)
            memory.learn(user_id, query, response)

            yield {
                "type": "complete",
                "answer": response,
                "conversation_id": conversation_id,
            }
            return

    # Max iterations reached - complete with reasoning
    response = sections.get("thinking", "Maximum iterations reached")

    conversation.add(conversation_id, "user", query)
    conversation.add(conversation_id, "assistant", response)

    yield {
        "type": "complete",
        "answer": response,
        "conversation_id": conversation_id,
    }
