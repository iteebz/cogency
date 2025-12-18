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

from . import context
from .core.accumulator import Accumulator
from .core.config import Config
from .core.errors import LLMError
from .core.parser import parse_tokens
from .core.protocols import Event, event_content
from .lib import telemetry
from .lib.debug import log_response
from .lib.metrics import Metrics

logger = logging.getLogger(__name__)


async def stream(  # noqa: C901  # HTTP ReAct orchestrator with iteration control
    query: str,
    user_id: str | None,
    conversation_id: str,
    *,
    config: Config,
    stream: Literal["event", "token", None] = "event",
):
    llm = config.llm

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
                user_id or "",
                conversation_id,
                tools=config.tools,
                storage=config.storage,
                history_window=config.history_window,
                history_transform=config.history_transform,
                profile_enabled=config.profile,
                identity=config.identity,
                instructions=config.instructions,
            )

            # Inject pending notifications
            if config.notifications:
                try:
                    pending = await config.notifications()
                    for notification in pending:
                        messages.append({"role": "system", "content": notification})
                except Exception as e:
                    logger.warning(f"Notification source failed: {e}")

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
                user_id or "",
                conversation_id,
                execution=config.execution,
                stream="token" if token_streaming else "event",
            )

            # Track this LLM call
            if metrics:
                metrics.start_step()
                metrics.add_input(messages)

            telemetry_events: list[Event] = []
            llm_output_chunks: list[str] = []

            try:
                if stream is None:
                    completion = await llm.generate(messages)
                    token_source = completion
                else:
                    token_source = llm.stream(messages)

                async for event in accumulator.process(parse_tokens(token_source)):
                    content = event_content(event)
                    if event["type"] in ["think", "call", "respond"] and metrics and content:
                        metrics.add_output(content)
                        llm_output_chunks.append(content)

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

            finally:
                if config.debug:
                    log_response(conversation_id, model_name, "".join(llm_output_chunks))
                await telemetry.persist_events(conversation_id, telemetry_events, config.storage)

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise LLMError(f"HTTP error: {e!s}", cause=e) from e
