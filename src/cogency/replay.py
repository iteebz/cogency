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

from .core.config import Config
from .core.errors import LLMError
from .core.parser import parse_tokens
from .core.protocols import event_content
from .core.session import setup
from .lib import telemetry
from .lib.debug import log_response

logger = logging.getLogger(__name__)


async def stream(  # noqa: C901
    query: str,
    user_id: str | None,
    conversation_id: str,
    *,
    config: Config,
    stream: Literal["event", "token", None] = "event",
):
    llm = config.llm
    model_name = getattr(llm, "http_model", "unknown")

    try:
        complete = False

        for iteration in range(1, config.max_iterations + 1):  # [SEC-005] Prevent runaway agents
            sess = await setup(query, user_id, conversation_id, config=config, stream=stream)

            if iteration == config.max_iterations:
                sess.messages.append(
                    {
                        "role": "system",
                        "content": "Final iteration: Please conclude naturally with what you've accomplished.",
                    }
                )

            telemetry_events = []
            llm_output_chunks: list[str] = []

            try:
                if stream is None:
                    completion = await llm.generate(sess.messages)
                    token_source = completion
                else:
                    token_source = llm.stream(sess.messages)

                async for event in sess.accumulator.process(parse_tokens(token_source)):
                    content = event_content(event)
                    if event["type"] in ["think", "call", "respond"] and sess.metrics and content:
                        sess.metrics.add_output(content)
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
                            if sess.metrics:
                                metrics_event = sess.metrics.event()
                                telemetry.add_event(telemetry_events, metrics_event)
                                yield metrics_event
                                sess.metrics.start_step()

                        case "result":
                            yield event

                        case _:
                            yield event

                if sess.metrics:
                    metrics_event = sess.metrics.event()
                    telemetry.add_event(telemetry_events, metrics_event)
                    yield metrics_event

            finally:
                if config.debug:
                    log_response(conversation_id, model_name, "".join(llm_output_chunks))
                await telemetry.persist_events(conversation_id, telemetry_events, config.storage)

            if complete:
                break

    except Exception as e:
        raise LLMError(f"HTTP error: {e!s}", cause=e) from e
