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

import time

from ..context import context
from ..lib.metrics import Tokens
from .accumulator import Accumulator
from .parser import parse_tokens


async def stream(config, query: str, user_id: str, conversation_id: str, chunks: bool = False):
    """WebSocket streaming with tool injection and session continuity."""
    if config.llm is None:
        raise ValueError("LLM provider required")

    # Duck typing - if it doesn't have WebSocket methods, fail fast
    if not hasattr(config.llm, "connect"):
        raise RuntimeError(
            f"Resume mode requires WebSocket support. Provider {type(config.llm).__name__} missing connect() method. "
            f"Use mode='auto' for fallback behavior or mode='replay' for HTTP-only."
        )

    # Initialize token tracking
    tokens = Tokens.init(config.llm)
    task_start_time = time.time()
    step_start_time = time.time()
    step_input_tokens = 0
    step_output_tokens = 0

    session = None
    try:
        # Assemble initial context
        messages = await context.assemble(query, user_id, conversation_id, config)
        
        # Track initial input tokens
        if tokens:
            step_input_tokens = tokens.add_input_messages(messages)

        # Establish persistent WebSocket session
        session = await config.llm.connect(messages)

        complete = False

        accumulator = Accumulator(
            config,
            user_id,
            conversation_id,
            chunks=chunks,
        )

        try:
            async for event in accumulator.process(parse_tokens(config.llm.receive(session))):
                # Track output tokens for content events
                if event["type"] in ["think", "respond"] and tokens and event.get("content"):
                    step_output_tokens += tokens.add_output(event["content"])
                
                match event["type"]:
                    case "end":
                        # Agent finished - actual termination
                        complete = True
                        
                        # Emit final metrics
                        if tokens:
                            step_duration = time.time() - step_start_time
                            total_duration = time.time() - task_start_time
                            metrics_event = tokens.to_step_metrics(
                                step_input_tokens, step_output_tokens, step_duration, total_duration
                            )
                            yield metrics_event

                    case "result":
                        # Tool result - inject into WebSocket session
                        success = await config.llm.send(session, event["content"])
                        if not success:
                            raise RuntimeError("Failed to inject tool result into WebSocket")
                        
                        # Emit metrics after tool result injection (end of LLM step)
                        if tokens:
                            step_duration = time.time() - step_start_time
                            total_duration = time.time() - task_start_time
                            metrics_event = tokens.to_step_metrics(
                                step_input_tokens, step_output_tokens, step_duration, total_duration
                            )
                            yield metrics_event
                            
                            # Reset for next step
                            step_start_time = time.time()
                            step_input_tokens = 0
                            step_output_tokens = 0

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
