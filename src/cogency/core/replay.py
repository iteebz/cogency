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

from ..context import context
from .accumulator import Accumulator
from .parser import parse_tokens


async def stream(config, query: str, user_id: str, conversation_id: str, chunks: bool = False):
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

            complete = False

            accumulator = Accumulator(
                config,
                user_id,
                conversation_id,
                chunks=chunks,
            )

            try:
                async for event in accumulator.process(parse_tokens(config.llm.stream(messages))):
                    match event["type"]:
                        case "end":
                            # Agent finished - actual termination
                            complete = True

                        case "result":
                            # Tool result - add to context for next HTTP iteration
                            messages.append(
                                {
                                    "role": "system",
                                    "content": f"COMPLETED ACTION: {event['content']}",
                                }
                            )
                            # Yield result to user before breaking
                            yield event
                            # Break to start new iteration cycle
                            break
                        case _:
                            yield event
            except Exception:
                raise

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
