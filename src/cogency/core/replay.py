"""Stateless HTTP mode with context rebuilding per iteration.

ReAct pattern:
1. HTTP Request → LLM Response → Parse → Execute Tools
2. Repeat until complete

Features:
- Fresh HTTP request per iteration
- Context rebuilt from storage each time
- Universal LLM compatibility
- No WebSocket dependencies
"""

import json

from ..context import context
from ..lib.persist import persister
from .execute import execute
from .parser import parse_stream
from .protocols import Event


async def _execute_and_continue(calls, config, user_id, conversation_id, messages):
    """Execute tools and add results to message context for next HTTP iteration."""
    individual_results, results_event = await execute(calls, config, user_id, conversation_id)

    # Add results to message context for next iteration
    messages.append(
        {
            "role": "system",
            "content": f"COMPLETED ACTIONS: {json.dumps(individual_results)}",
        }
    )

    return individual_results, results_event


async def stream(config, query: str, user_id: str, conversation_id: str):
    """Stateless HTTP iterations with context rebuild per request."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    try:
        # Assemble context from storage (exclude current cycle to prevent duplication)
        messages = context.assemble(query, user_id, conversation_id, config)

        for iteration in range(1, config.max_iterations + 1):
            # Add final iteration guidance
            if iteration == config.max_iterations:
                messages.append(
                    {
                        "role": "system",
                        "content": "Final iteration: Please conclude naturally with what you've accomplished.",
                    }
                )

            calls = None
            complete = False

            # Parse LLM stream with immediate persistence
            persist_event = persister(conversation_id, user_id)

            # HTTP STREAMING: Direct stream call, pure tokens
            try:
                async for event in parse_stream(
                    config.llm.stream(messages), on_complete=persist_event
                ):
                    match event["type"]:
                        case Event.CALLS:
                            calls = event.get("calls")
                            if not calls:
                                continue

                        case Event.RESPOND:
                            # Response event - agent continues working
                            pass

                        case Event.END:
                            # Agent finished - actual termination
                            complete = True

                        case Event.EXECUTE:
                            # Execute tools and start new iteration cycle
                            if calls:
                                # Execute tools, add to context for next request
                                individual_results, results_event = await _execute_and_continue(
                                    calls, config, user_id, conversation_id, messages
                                )
                                yield results_event

                                # Start new iteration cycle
                                break

                    yield event
            except Exception:
                raise

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
