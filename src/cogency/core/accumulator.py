"""Stream processing with clean persistence separation.

Accumulate events → Execute tools → Emit results.
Persistence delegated to specialized service.
"""

import time
from collections.abc import AsyncGenerator
from typing import Any

from .executor import execute
from .persister import EventPersister
from .protocols import ToolCall


class Accumulator:
    """Stream processor focused on event accumulation and tool execution."""

    def __init__(self, config, user_id: str, conversation_id: str, *, chunks: bool = False):
        self.config = config
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.chunks = chunks
        
        # Delegate persistence
        self.persister = EventPersister(conversation_id, user_id)
        
        # Simple accumulation state
        self.current_type = None
        self.content = ""
        self.start_time = None

    async def process(
        self, parser_events: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process events with clean tool execution."""

        async for event in parser_events:
            event_type = event["type"]
            content = event["content"]
            timestamp = time.time()

            if self.chunks:
                yield event

            # Handle control flow events
            if event_type == "execute":
                if self.current_type == "call" and self.content.strip():
                    # Persist the call first
                    await self.persister.persist_call(self.content, self.start_time)
                    
                    # Execute and persist result
                    try:
                        tool_call = ToolCall.from_json(self.content.strip())
                        result = await execute(tool_call, self.config, self.user_id, self.conversation_id)
                        
                        # Format and persist result
                        from .formatter import Formatter
                        result_content = Formatter.tool_result_human(result)
                        await self.persister.persist_result(result_content, timestamp)
                        
                        # Emit result
                        yield {
                            "type": "result",
                            "content": result_content,
                            "timestamp": timestamp,
                        }
                    except (ValueError, TypeError, KeyError) as e:
                        # LLM input error - send feedback event
                        error_content = f"Invalid tool call: {str(e)}"
                        await self.persister.persist_result(error_content, timestamp)
                            
                        yield {
                            "type": "result", 
                            "content": error_content,
                            "timestamp": timestamp,
                        }
                    # Let system errors (OSError, ConnectionError, etc) bubble up
                    
                    # Reset state
                    self.current_type = None
                    self.content = ""
                    self.start_time = None
                continue
                
            elif event_type == "end":
                # End processing
                yield {"type": "end", "content": "", "timestamp": timestamp}
                return

            # Handle state transitions
            if event_type != self.current_type:
                # Persist and emit previous accumulated content
                if self.current_type and self.content.strip():
                    # Persist think/respond events (calls handled in execute)
                    if self.current_type == "think":
                        await self.persister.persist_think(self.content, self.start_time)
                    elif self.current_type == "respond":
                        await self.persister.persist_respond(self.content, self.start_time)
                    
                    # Emit for streaming (non-chunks mode, skip calls - handled by execute)
                    if not self.chunks and self.current_type != "call":
                        yield {
                            "type": self.current_type,
                            "content": self.content,
                            "timestamp": self.start_time,
                        }

                # Start new accumulation
                self.current_type = event_type
                self.content = content
                self.start_time = timestamp
            else:
                # Same type - accumulate content
                if (
                    self.content
                    and content
                    and not self.content.endswith(" ")
                    and not content.startswith(" ")
                ):
                    self.content += " "
                self.content += content

        # Final flush
        if self.current_type and self.content.strip():
            # Persist final events
            if self.current_type == "think":
                await self.persister.persist_think(self.content, self.start_time)
            elif self.current_type == "respond":
                await self.persister.persist_respond(self.content, self.start_time)
            
            # Emit final event (non-chunks mode, skip calls)
            if not self.chunks and self.current_type != "call":
                yield {
                    "type": self.current_type,
                    "content": self.content,
                    "timestamp": self.start_time,
                }