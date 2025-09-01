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
from ..lib.logger import logger
from .parser import parse_stream
from .protocols import Event


async def _handle_execute_yield_replay(calls, config, user_id, conversation_id, messages):
    """Execute tools and add results to message context for next HTTP iteration."""
    from .execute import execute_tools_and_save

    individual_results, results_event = await execute_tools_and_save(
        calls, config, user_id, conversation_id
    )

    # Add results to message context for next iteration
    messages.append(
        {
            "role": "system",
            "content": json.dumps(individual_results),
        }
    )

    return individual_results, results_event


async def stream(config, query: str, user_id: str, conversation_id: str):
    """Stateless HTTP iterations with context rebuild per request."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    try:
        # Assemble context from storage
        messages = context.assemble(query, user_id, conversation_id, config.tools, config)

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
            from ..lib.persist import create_event_persister

            persist_event = create_event_persister(conversation_id, user_id)

            async for event in parse_stream(config.llm.stream(messages), on_complete=persist_event):
                logger.debug(f"Event: {event['type']} - {event.get('content', '')[:100]}...")

                match event["type"]:
                    case Event.CALLS:
                        calls = event.get("calls")
                        if not calls:
                            logger.debug("CALLS parsing failed - skipping")
                            continue

                    case Event.RESPOND:
                        # Response complete
                        logger.debug("Response complete")
                        complete = True

                    case Event.YIELD:
                        # Context-aware yield handling
                        yield_context = event.get("content", "unknown")

                        if yield_context == "execute" and calls:
                            # Execute tools, add to context for next request
                            individual_results, results_event = await _handle_execute_yield_replay(
                                calls, config, user_id, conversation_id, messages
                            )
                            yield results_event

                            # Start new iteration cycle
                            break

                        elif yield_context == "complete":
                            # Complete
                            complete = True

                yield event

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
