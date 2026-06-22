"""WebSocket streaming with tool injection and session persistence.

Algorithm:
1. Establish WebSocket session with initial context
2. Stream tokens continuously from LLM
3. When parser detects execute event → pause stream → execute tool
4. Inject tool result back into same session → resume streaming
5. Repeat until end event or natural completion

Enables maximum token efficiency by maintaining conversation state
in LLM memory rather than resending full context each turn.
"""

import logging
from typing import Literal

from .core.config import Config
from .core.errors import LLMError
from .core.parser import parse_tokens
from .core.protocols import event_content, event_type
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

    if not hasattr(llm, "connect"):
        raise LLMError(
            f"Resume mode requires WebSocket support. Provider {type(llm).__name__} missing connect() method. "
            f"Use mode='auto' for fallback behavior or mode='replay' for HTTP-only."
        )

    model_name = getattr(llm, "http_model", "unknown")

    sess = await setup(query, user_id, conversation_id, config=config, stream=stream)

    session = None
    turn = 0
    try:
        session = await llm.connect(sess.messages)

        complete = False
        payload = None
        count_payload_tokens = False
        telemetry_events = []

        try:
            while True:
                turn += 1
                if turn > config.max_iterations:
                    raise LLMError(
                        f"Max iterations ({config.max_iterations}) exceeded in resume mode."
                    )

                if count_payload_tokens and sess.metrics and payload:
                    sess.metrics.add_input(payload)

                turn_output: list[str] = []
                next_payload: str | None = None

                try:
                    send_content = query if payload is None else payload
                    async for event in sess.accumulator.process(
                        parse_tokens(session.send(send_content))
                    ):
                        ev_type = event_type(event)
                        content = event_content(event)

                        if ev_type in {"think", "call", "respond"} and sess.metrics and content:
                            sess.metrics.add_output(content)
                            turn_output.append(content)

                        if event:
                            telemetry.add_event(telemetry_events, event)

                        match ev_type:
                            case "end":
                                complete = True
                                if sess.metrics:
                                    metric = sess.metrics.event()
                                    telemetry.add_event(telemetry_events, metric)
                                    yield metric
                                yield event
                                break

                            case "execute":
                                if sess.metrics:
                                    metric = sess.metrics.event()
                                    telemetry.add_event(telemetry_events, metric)
                                    yield metric
                                    sess.metrics.start_step()
                                yield event

                            case "result":
                                yield event
                                next_payload = f"<results>\n{content}\n</results>"
                                break

                            case _:
                                yield event
                except Exception as e:
                    raise LLMError(f"WebSocket continuation failed: {e}", cause=e) from e
                finally:
                    if config.debug:
                        log_response(
                            conversation_id,
                            model_name,
                            "".join(turn_output),
                        )

                if complete or next_payload is None:
                    break

                payload = next_payload or ""
                count_payload_tokens = True
        finally:
            await telemetry.persist_events(conversation_id, telemetry_events, config.storage)

    except Exception as e:
        raise LLMError(f"WebSocket failed: {e!s}", cause=e) from e
    finally:
        if session:
            await session.close()
