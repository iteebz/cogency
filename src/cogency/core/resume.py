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

import json

from ..context import context
from ..lib.persist import persister
from .execute import execute
from .parser import parse_stream
from .protocols import Event


async def _execute_and_inject(calls, config, user_id, session, conversation_id):
    """
    Execute tools and inject results into same WebSocket session.

    After tool execution, combines results with a continuation prompt to ensure
    the LLM continues processing subsequent steps in multi-step tasks.
    """
    individual_results, results_event = await execute(calls, config, user_id, conversation_id)

    # Format results as JSON
    results_text = json.dumps(individual_results)

    # Combine with continuation instruction
    # This ensures the LLM continues to the next steps after processing tool results
    combined_message = f"{results_text}\n\nContinue with the next steps of the task."

    # Send combined message to WebSocket session
    # Note: This message is part of the WebSocket flow and isn't stored in the conversation DB
    success = await config.llm.send(session, combined_message)
    if not success:
        raise RuntimeError("Failed to send results to WebSocket")

    return results_event


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

        calls = None
        complete = False
        tool_results_sent = False  # Track when we've sent tool results

        # Parse streaming tokens with immediate persistence
        persist_event = persister(conversation_id, user_id)

        try:
            async for event in parse_stream(config.llm.receive(session), on_complete=persist_event):
                match event["type"]:
                    case Event.CALLS:
                        calls = event["calls"]

                    case Event.RESPOND:
                        # Response event - agent continues working
                        pass

                    case Event.END:
                        # Agent finished - actual termination
                        complete = True

                    case Event.EXECUTE:
                        # Execute tools and continue same session
                        if calls:
                            # Execute tools and continue same session
                            results_event = await _execute_and_inject(
                                calls, config, user_id, session, conversation_id
                            )
                            yield results_event
                            calls = None
                            tool_results_sent = True  # Mark that we sent tool results

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
