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

from .. import context
from ..lib.metrics import Metrics
from .accumulator import Accumulator
from .config import Config
from .parser import parse_tokens


async def stream(
    query: str,
    user_id: str,
    conversation_id: str,
    *,
    config: Config,
    chunks: bool = False,
):
    """Stateless HTTP iterations with context rebuild per request."""
    llm = config.llm
    if llm is None:
        raise ValueError("LLM provider required")

    # Initialize metrics tracking
    model_name = getattr(llm, "http_model", "unknown")
    metrics = Metrics.init(model_name)
    time.time()

    try:
        # Assemble context from storage (exclude current cycle to prevent duplication)
        messages = await context.assemble(
            query,
            user_id,
            conversation_id,
            tools=config.tools,
            storage=config.storage,
            history_window=config.history_window,
            profile_enabled=config.profile,
        )

        complete = False

        for iteration in range(1, config.max_iterations + 1):  # [SEC-005] Prevent runaway agents
            # Exit early if previous iteration completed
            if complete:
                break

            # Add final iteration guidance
            if iteration == config.max_iterations:
                messages.append(
                    {
                        "role": "system",
                        "content": "Final iteration: Please conclude naturally with what you've accomplished.",
                    }
                )

            accumulator = Accumulator(
                user_id,
                conversation_id,
                execution=config.execution,
                chunks=chunks,
            )

            # Track this LLM call
            if metrics:
                metrics.start_step()
                metrics.add_input(messages)
            else:
                pass

            step_output_tokens = 0

            # Track output tokens for all LLM-generated content
            try:
                async for event in accumulator.process(parse_tokens(llm.stream(messages))):
                    # Track output tokens for all LLM-generated content
                    if (
                        event["type"] in ["think", "call", "respond"]
                        and metrics
                        and event.get("content")
                    ):
                        step_output_tokens += metrics.add_output(event["content"])

                    match event["type"]:
                        case "end":
                            # Agent finished - actual termination
                            complete = True
                            from ..lib.logger import logger

                            logger.debug(f"REPLAY: Set complete=True on iteration {iteration}")

                        case "execute":
                            # Emit metrics when LLM pauses for tool execution
                            if metrics:
                                yield metrics.event()
                                metrics.start_step()
                            yield event
                            break

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
                if metrics:
                    yield metrics.event()

            except Exception:
                raise

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
