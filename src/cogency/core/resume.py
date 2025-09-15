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

from .. import context
from ..lib.metrics import Metrics
from .accumulator import Accumulator
from .parser import parse_tokens


async def stream(config, query: str, user_id: str, conversation_id: str, chunks: bool = False):
    """WebSocket streaming with tool injection and session continuity."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    # Verify WebSocket capability
    if not hasattr(config.llm, "connect"):
        raise RuntimeError(
            f"Resume mode requires WebSocket support. Provider {type(config.llm).__name__} missing connect() method. "
            f"Use mode='auto' for fallback behavior or mode='replay' for HTTP-only."
        )

    # Initialize metrics tracking
    metrics = Metrics.init(config.llm.llm_model)

    session = None
    try:
        messages = await context.assemble(query, user_id, conversation_id, config)

        if metrics:
            metrics.start_step()
            metrics.add_input(messages)

        session = await config.llm.connect(messages)

        complete = False

        accumulator = Accumulator(
            config,
            user_id,
            conversation_id,
            chunks=chunks,
        )

        try:
            async for event in accumulator.process(parse_tokens(session.send(query))):
                if (
                    event["type"] in ["think", "call", "respond"]
                    and metrics
                    and event.get("content")
                ):
                    metrics.add_output(event["content"])

                match event["type"]:
                    case "end":
                        complete = True
                        # Close session on task completion
                        await session.close()
                        if metrics:
                            yield metrics.event()

                    case "execute":
                        # Emit metrics when LLM pauses for tool execution
                        if metrics:
                            yield metrics.event()
                            metrics.start_step()

                    case "result":
                        # Send tool result to session to continue generation
                        try:
                            # Continue streaming after tool result injection
                            async for continuation_event in accumulator.process(
                                parse_tokens(session.send(event["content"]))
                            ):
                                yield continuation_event
                                if continuation_event.get("type") == "end":
                                    complete = True
                                    break
                        except Exception as e:
                            raise RuntimeError(f"WebSocket continuation failed: {e}") from e

                        if metrics:
                            yield metrics.event()
                            metrics.start_step()

                yield event

                if complete:
                    break
        except Exception:
            raise

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
