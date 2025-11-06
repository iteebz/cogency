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

import logging
from typing import Literal

from .. import context
from ..lib import telemetry
from ..lib.metrics import Metrics
from .accumulator import Accumulator
from .config import Config
from .parser import parse_tokens

logger = logging.getLogger(__name__)


async def stream(
    query: str,
    user_id: str,
    conversation_id: str,
    *,
    config: Config,
    stream: Literal["event", "token", None] = "event",
):
    """Stateless HTTP iterations with context rebuild per request.

    Args:
        stream: Streaming strategy. "token" yields chunks as they arrive,
               "event" accumulates and yields complete semantic units,
               None uses LLM.generate() for non-streaming response.
    """

    llm = config.llm
    if llm is None:
        raise ValueError("LLM provider required")

    storage = config.storage

    # Initialize metrics tracking
    model_name = getattr(llm, "http_model", "unknown")
    metrics = Metrics.init(model_name)

    try:
        complete = False

        for iteration in range(1, config.max_iterations + 1):  # [SEC-005] Prevent runaway agents
            # Exit early if previous iteration completed
            if complete:
                break

            messages = await context.assemble(
                user_id,
                conversation_id,
                tools=config.tools,
                storage=config.storage,
                history_window=config.history_window,
                profile_enabled=config.profile,
                identity=config.identity,
                instructions=config.instructions,
            )

            # Add final iteration guidance
            if iteration == config.max_iterations:
                messages.append(
                    {
                        "role": "system",
                        "content": "Final iteration: Please conclude naturally with what you've accomplished.",
                    }
                )

            # stream=None uses .generate(), stream="token" yields token chunks, stream="event" batches semantically
            # Only "token" mode does token-level streaming; "event" and None both accumulate complete units
            token_streaming = stream == "token"
            accumulator = Accumulator(
                user_id,
                conversation_id,
                execution=config.execution,
                stream="token" if token_streaming else "event",
            )

            # Track this LLM call
            if metrics:
                metrics.start_step()
                metrics.add_input(messages)

            telemetry_events: list[dict] = []
            llm_output_chunks = []

            try:
                if stream is None:
                    completion = await llm.generate(messages)
                    token_source = completion
                else:
                    token_source = llm.stream(messages)

                async for event in accumulator.process(parse_tokens(token_source)):
                    if (
                        event["type"] in ["think", "call", "respond"]
                        and metrics
                        and event.get("content")
                    ):
                        metrics.add_output(event["content"])
                        llm_output_chunks.append(event["content"])

                    if event:
                        telemetry.add_event(telemetry_events, event)

                    match event["type"]:
                        case "end":
                            complete = True
                            logger.debug(f"REPLAY: Set complete=True on iteration {iteration}")
                            yield event

                        case "execute":
                            yield event
                            if metrics:
                                metrics_event = metrics.event()
                                telemetry.add_event(telemetry_events, metrics_event)
                                yield metrics_event
                                metrics.start_step()

                        case "result":
                            yield event

                        case _:
                            yield event

                # Emit metrics after LLM call completes
                if metrics:
                    metrics_event = metrics.event()
                    telemetry.add_event(telemetry_events, metrics_event)
                    yield metrics_event

            except Exception:
                raise
            finally:
                if config.debug:
                    from ..lib.debug import log_response

                    log_response(conversation_id, model_name, "".join(llm_output_chunks))
                await telemetry.persist_events(conversation_id, telemetry_events)

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
