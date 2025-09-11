"""WebSocket mode with persistent session and tool injection.

WebSocket pattern:
1. Single session → continuous token stream
2. Parser detects §EXECUTE → pause session → execute tools
3. Inject results → resume same stream
4. Repeat within same session

Features:
- Persistent WebSocket connection
- Stream pauses/resumes without context loss
- LLM maintains conversation state
- Requires WebSocket support (GPT-4o Realtime, Gemini Live)
- Maximum token efficiency
"""

from ..context import context
from ..lib.persist import persister
from .accumulator import Accumulator
from .parser import parse_tokens


async def stream(config, query: str, user_id: str, conversation_id: str):
    """WebSocket streaming with tool injection and session continuity."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    # Check resume capability - strict mode, no fallback
    has_resumable = hasattr(config.llm, "resumable")
    resumable_value = getattr(config.llm, "resumable", None) if has_resumable else None

    if not has_resumable or not resumable_value:
        raise RuntimeError(
            f"Resume mode requires WebSocket support. Provider {type(config.llm).__name__} does not support resumable sessions. "
            f"Use mode='auto' for fallback behavior or mode='replay' for HTTP-only."
        )

    session = None
    try:
        # Assemble initial context
        messages = context.assemble(query, user_id, conversation_id, config)

        # Establish persistent WebSocket session
        session_result = await config.llm.connect(messages)

        if not session_result:
            raise RuntimeError("Failed to establish WebSocket connection")

        # Unwrap Result if needed
        if hasattr(session_result, "success") and hasattr(session_result, "unwrap"):
            if session_result.success:
                session = session_result.unwrap()
            else:
                raise RuntimeError("Failed to establish WebSocket connection")
        else:
            session = session_result

        complete = False

        persist_event = persister(conversation_id, user_id)
        accumulator = Accumulator(
            config,
            user_id,
            conversation_id,
            chunks=True,
            on_persist=persist_event,
        )

        try:
            async for event in accumulator.process(parse_tokens(config.llm.receive(session))):
                match event["type"]:
                    case "end":
                        # Agent finished - actual termination
                        complete = True

                    case "result":
                        # Tool result - inject into WebSocket session
                        success = await config.llm.send(session, event["content"])
                        if not success:
                            raise RuntimeError("Failed to inject tool result into WebSocket")

                yield event

                # Stop after completion
                if complete:
                    break
        except Exception:
            raise

        # Handle incomplete sessions
        if not complete:
            # Stream ended without §END - this is natural completion for resume mode
            # WebSocket streams end when provider decides, not when agent decides
            complete = True

    except Exception as e:
        raise RuntimeError(f"WebSocket failed: {str(e)}") from e
    finally:
        # Always cleanup session - success or failure
        if session:
            await config.llm.close(session)
