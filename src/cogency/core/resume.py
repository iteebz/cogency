"""WebSocket mode with persistent session and tool injection.

WebSocket pattern:
1. Single session → continuous token stream
2. Parser detects §YIELD → pause session → execute tools
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
from ..lib.logger import logger
from .parser import parse_stream
from .protocols import Event


async def _handle_execute_yield(calls, config, user_id, session, conversation_id):
    """Execute tools and inject results into same WebSocket session."""
    from .execute import execute_tools_and_save

    individual_results, results_event = await execute_tools_and_save(
        calls, config, user_id, conversation_id
    )

    # Inject results into same WebSocket session
    results_text = json.dumps(individual_results)
    success = await config.llm.send(session, results_text)
    if not success:
        raise RuntimeError("Failed to send results to WebSocket")

    logger.debug("Tools executed, WebSocket continues")
    return results_event


async def stream(config, query: str, user_id: str, conversation_id: str):
    """WebSocket streaming with tool injection and session continuity."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    # Check resume capability - fallback to replay if not supported
    if not hasattr(config.llm, "resumable") or not config.llm.resumable:
        # Import here to avoid circular dependency
        from .replay import stream as replay_stream

        async for event in replay_stream(config, query, user_id, conversation_id):
            yield event
        return

    session = None
    try:
        # Assemble initial context
        messages = context.assemble(query, user_id, conversation_id, config.tools, config)

        # Establish persistent WebSocket session
        session = await config.llm.connect(messages)
        if not session:
            raise RuntimeError("Failed to establish WebSocket connection")

        calls = None
        complete = False

        # Parse streaming tokens with immediate persistence
        from ..lib.persist import create_event_persister

        persist_event = create_event_persister(conversation_id, user_id)

        # Continuous token stream from WebSocket
        async def continuous_token_stream():
            """Token stream from WebSocket to parser."""
            async for token in config.llm.receive(session):
                yield token

        async for event in parse_stream(continuous_token_stream(), on_complete=persist_event):
            match event["type"]:
                case Event.CALLS:
                    calls = event["calls"]

                case Event.RESPOND:
                    # Response event received
                    logger.debug("Response event received")

                case Event.YIELD:
                    # Context-aware yield handling
                    yield_context = event.get("content", "unknown")

                    if yield_context == "execute" and calls:
                        # Execute tools and continue same session
                        results_event = await _handle_execute_yield(
                            calls, config, user_id, session, conversation_id
                        )
                        yield results_event
                        calls = None

                    elif yield_context == "complete":
                        # Conversation complete
                        logger.debug("Conversation complete")
                        complete = True

                    else:
                        logger.debug(f"YIELD with context '{yield_context}' - continuing")

            yield event

            # Stop after completion
            if complete:
                logger.debug("Breaking WebSocket stream")
                break

        # Handle incomplete sessions
        if not complete:
            logger.debug("Incomplete, falling back to replay mode")
            if session:
                await config.llm.close(session)

            from .replay import stream as replay_stream

            async for event in replay_stream(config, query, user_id, conversation_id):
                yield event

    except Exception as e:
        logger.debug(f"Exception occurred: {str(e)}")
        raise RuntimeError(f"WebSocket error: {str(e)}") from e
    finally:
        # Session cleanup after successful completion
        if session and complete:
            logger.debug("Closing session after completion")
            await config.llm.close(session)
