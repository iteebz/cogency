"""Streamer: Event streaming, accumulation, state management, and consumer formatting.

ZEALOT ARCHITECTURE: Streamer is the smart layer between Parser and Consumers.

Responsibilities:
- Stream events immediately for real-time UX (think/respond)
- Accumulate events based on type (streaming vs batching)
- Detect state transitions and manage conversation state
- Persist events to database on state changes
- Coordinate with tool execution layer

Parser gives us raw semantic events, we give consumers clean formatted streams.
"""

import json
import time
from collections.abc import AsyncGenerator
from typing import Any, Callable, Optional

from ..lib.resilience import safe_callback
from .executor import execute_calls
from .parser import parse_tokens
from .protocols import Event, ToolResult


class Streamer:
    """Real-time event streamer with smart accumulation and state management."""
    
    def __init__(
        self, 
        conversation_id: str, 
        user_id: str,
        config,
        on_persist: Optional[Callable[[dict], None]] = None
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.config = config
        self.on_persist = on_persist
        
        # State tracking
        self.current_state = Event.RESPOND
        self.accumulated_content = ""
        self.accumulated_calls = []
        self.last_state_change = time.time()
    
    async def process_events(
        self, 
        token_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process token stream into consumer-ready events.
        
        Handles three event processing strategies:
        1. THINK/RESPOND: Stream tokens immediately with state hints
        2. CALL: Accumulate until EXECUTE, then coordinate with tools
        3. EXECUTE/END: State transition events
        """
        
        async for raw_event in parse_tokens(token_stream):
            event_type = Event(raw_event["type"])
            content = raw_event["content"]
            timestamp = raw_event["timestamp"]
            
            # Detect CONVERSATION state transitions (only THINK/RESPOND are states)
            conversation_states = {Event.THINK, Event.RESPOND}
            is_conversation_event = event_type in conversation_states
            current_is_conversation = self.current_state in conversation_states
            
            state_change = False
            if is_conversation_event and current_is_conversation:
                # Both are conversation states - check for actual transition
                state_change = event_type != self.current_state
            elif is_conversation_event and not current_is_conversation:
                # Entering conversation state from action/initial
                state_change = True
            # Else: action events (CALL/EXECUTE/END) never trigger state_change=True
            
            if state_change:
                # Persist accumulated content before transition
                await self._persist_accumulated_state()
                self.last_state_change = timestamp
            
            # Update current state for conversation events only
            if is_conversation_event:
                self.current_state = event_type
            
            # Process based on event type
            match event_type:
                case Event.THINK:
                    # Streaming think event: emit immediately
                    if content:
                        yield {
                            "type": "think",
                            "content": content,
                            "timestamp": timestamp,
                            "state_change": state_change
                        }
                    
                    # Accumulate for persistence
                    self.accumulated_content += content
                
                case Event.RESPOND:
                    # Streaming respond event: emit immediately  
                    if content:
                        yield {
                            "type": "respond",
                            "content": content,
                            "timestamp": timestamp,
                            "state_change": state_change
                        }
                    
                    # Accumulate for persistence
                    self.accumulated_content += content
                
                case Event.CALL:
                    # Accumulation event: collect single tool call
                    self.accumulated_content += content
                    
                    # Try to parse as JSON object (single call)
                    try:
                        call_data = json.loads(content)
                        if isinstance(call_data, dict):
                            self.accumulated_calls = [call_data]  # Convert to list for executor
                    except json.JSONDecodeError:
                        # Invalid JSON - continue accumulating
                        pass
                
                case Event.EXECUTE:
                    # Execute accumulated tool calls
                    if self.accumulated_calls:
                        try:
                            tool_results = await execute_calls(
                                self.accumulated_calls, 
                                self.config, 
                                self.user_id, 
                                self.conversation_id
                            )
                            
                            # Emit tool events for each result
                            for result in tool_results:
                                yield {
                                    "type": "tool",
                                    "content": result.outcome,  # Simple outcome text
                                    "timestamp": time.time(),
                                    "status": "success"         # Tools return results or throw
                                }
                                
                                # Persist tool execution
                                await self._persist_tool_result(result)
                                
                        except Exception as e:
                            # Tool execution failed
                            yield {
                                "type": "tool",
                                "content": f"execution failed: {str(e)}",
                                "timestamp": time.time(),
                                "status": "error"
                            }
                    
                    # Reset accumulated calls
                    self.accumulated_calls = []
                
                case Event.END:
                    # Final persistence and termination
                    await self._persist_accumulated_state()
                    
                    yield {
                        "type": "end",
                        "content": "",
                        "timestamp": timestamp
                    }
                    return
    
    async def _persist_accumulated_state(self):
        """Persist accumulated content to database on state transitions."""
        if not self.accumulated_content.strip() or not self.on_persist:
            return
            
        # Create persistence event
        persist_event = {
            "type": self.current_state.value,
            "content": self.accumulated_content.strip(),
            "timestamp": self.last_state_change,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id
        }
        
        # Safe callback to persistence layer
        safe_callback(self.on_persist, persist_event)
        
        # Reset accumulation
        self.accumulated_content = ""
    
    async def _persist_tool_result(self, result):
        """Persist individual tool execution results."""
        if not self.on_persist:
            return
            
        # Store simple outcome and content
        persist_event = {
            "type": "tool_result", 
            "content": result.for_agent(),  # outcome + content for full context
            "timestamp": time.time(),
            "conversation_id": self.conversation_id,
            "user_id": self.user_id
        }
        
        safe_callback(self.on_persist, persist_event)