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

import time

from ..context import context
from ..lib.metrics import Tokens
from .accumulator import Accumulator
from .parser import parse_tokens


async def stream(config, query: str, user_id: str, conversation_id: str, chunks: bool = False):
    """Stateless HTTP iterations with context rebuild per request."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    # Initialize token tracking
    tokens = Tokens.init(config.llm)
    task_start_time = time.time()

    try:
        # Assemble context from storage (exclude current cycle to prevent duplication)
        messages = await context.assemble(query, user_id, conversation_id, config)

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

            # Track this LLM call
            step_start_time = time.time()
            if tokens:
                step_input_tokens = tokens.add_input_messages(messages)
            else:
                step_input_tokens = 0

            step_output_tokens = 0
            
            try:
                async for event in accumulator.process(parse_tokens(config.llm.stream(messages))):
                    # Track output tokens for content events
                    if event["type"] in ["think", "respond"] and tokens and event.get("content"):
                        step_output_tokens += tokens.add_output(event["content"])
                    
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
                            
                # Emit metrics after LLM call completes
                if tokens:
                    step_duration = time.time() - step_start_time
                    total_duration = time.time() - task_start_time
                    metrics_event = tokens.to_step_metrics(
                        step_input_tokens, step_output_tokens, step_duration, total_duration
                    )
                    yield metrics_event
                    
            except Exception:
                raise

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
