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
import time

from .. import context
from ..lib.logger import logger
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

            step_output_tokens = 0

            request_timestamp = time.time()
            serialized_messages = json.dumps(messages)
            telemetry_events: list[dict] = []

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

                    if event:
                        telemetry_events.append(event)

                    match event["type"]:
                        case "end":
                            complete = True
                            logger.debug(f"REPLAY: Set complete=True on iteration {iteration}")
                            yield event

                        case "execute":
                            yield event
                            if metrics:
                                metrics_event = metrics.event()
                                telemetry_events.append(metrics_event)
                                yield metrics_event
                                metrics.start_step()

                        case "result":
                            yield event

                        case _:
                            yield event

                # Emit metrics after LLM call completes
                if metrics:
                    metrics_event = metrics.event()
                    telemetry_events.append(metrics_event)
                    yield metrics_event

            except Exception:
                raise
            finally:
                if hasattr(config.storage, "save_request"):
                    try:
                        await config.storage.save_request(
                            conversation_id,
                            user_id,
                            serialized_messages,
                            json.dumps(telemetry_events),
                            request_timestamp,
                        )
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.debug(f"Failed to persist request telemetry: {exc}")

            # Exit iteration loop if complete
            if complete:
                break

    except Exception as e:
        raise RuntimeError(f"HTTP error: {str(e)}") from e
