"""WebSocket streaming with tool injection and session persistence.

Algorithm:
1. Establish WebSocket session with initial context
2. Stream tokens continuously from LLM
3. When parser detects §execute → pause stream → execute tool
4. Inject tool result back into same session → resume streaming
5. Repeat until §end or natural completion

Enables maximum token efficiency by maintaining conversation state
in LLM memory rather than resending full context each turn.
"""

from typing import Literal

from .. import context
from ..lib import telemetry
from ..lib.debug import log_response
from ..lib.metrics import Metrics
from .accumulator import Accumulator
from .config import Config
from .parser import parse_tokens
from .protocols import event_content, event_type


async def stream(
    query: str,
    user_id: str,
    conversation_id: str,
    *,
    config: Config,
    stream: Literal["event", "token", None] = "event",
):
    """WebSocket streaming with tool injection and session continuity.

    Args:
        stream: Streaming strategy. "token" yields chunks as they arrive,
               "event" accumulates and yields complete semantic units,
               None uses LLM.generate() for non-streaming response.
    """

    llm = config.llm
    if llm is None:
        raise ValueError("LLM provider required")

    # Verify WebSocket capability
    if not hasattr(llm, "connect"):
        raise RuntimeError(
            f"Resume mode requires WebSocket support. Provider {type(llm).__name__} missing connect() method. "
            f"Use mode='auto' for fallback behavior or mode='replay' for HTTP-only."
        )

    # Initialize metrics tracking
    model_name = getattr(llm, "http_model", "unknown")
    metrics = Metrics.init(model_name)

    session = None
    turn = 0
    try:
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

        if metrics:
            metrics.start_step()
            metrics.add_input(messages)

        telemetry_events: list[dict] = []
        session = await llm.connect(messages)

        complete = False

        # stream=None uses .generate(), stream="token" yields token chunks, stream="event" batches semantically
        # Only "token" mode does token-level streaming; "event" and None both accumulate complete units
        token_streaming = stream == "token"
        accumulator = Accumulator(
            user_id,
            conversation_id,
            execution=config.execution,
            stream="token" if token_streaming else "event",
        )

        payload = None
        count_payload_tokens = False

        try:
            while True:
                turn += 1
                if turn > config.max_iterations:
                    raise RuntimeError(
                        f"Max iterations ({config.max_iterations}) exceeded in resume mode."
                    )

                if count_payload_tokens and metrics and payload:
                    metrics.add_input(payload)

                turn_output: list[str] = []
                next_payload: str | None = None

                try:
                    # Send query on first turn, payload on subsequent turns
                    send_content = query if payload is None else payload
                    async for event in accumulator.process(
                        parse_tokens(session.send(send_content))
                    ):
                        ev_type = event_type(event)
                        content = event_content(event)

                        if ev_type in {"think", "call", "respond"} and metrics and content:
                            metrics.add_output(content)
                            turn_output.append(content)

                        if event:
                            telemetry.add_event(telemetry_events, event)

                        match ev_type:
                            case "end":
                                complete = True
                                if metrics:
                                    metric = metrics.event()
                                    telemetry.add_event(telemetry_events, metric)
                                    yield metric
                                yield event
                                break

                            case "execute":
                                if metrics:
                                    metric = metrics.event()
                                    telemetry.add_event(telemetry_events, metric)
                                    yield metric
                                    metrics.start_step()
                                yield event

                            case "result":
                                yield event
                                next_payload = f"<results>\n{content}\n</results>"
                                break

                            case _:
                                yield event

                        if complete:
                            break
                except Exception as e:
                    raise RuntimeError(f"WebSocket continuation failed: {e}") from e
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
            await telemetry.persist_events(conversation_id, telemetry_events)
        # Handle natural WebSocket completion
        if not complete:
            # Stream ended without §end - provider-driven completion
            complete = True

    except Exception as e:
        raise RuntimeError(f"WebSocket failed: {str(e)}") from e
    finally:
        # Always cleanup WebSocket session
        if session:
            await session.close()
