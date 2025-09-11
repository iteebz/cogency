"""Event accumulator: chunks flag controls semantic vs token streaming.

ZEALOT ARCHITECTURE: Accumulator does ONE job - batch or stream events based on chunks flag.

chunks=True:  Individual parser events → Consumer (raw streaming)
chunks=False: Accumulated semantic events → Consumer (progress streaming)

Persister ALWAYS gets accumulated semantic events regardless of chunks flag.
"""

import time
from collections.abc import AsyncGenerator
from typing import Any, Callable, Optional

from .protocols import Event


class Accumulator:
    """Event accumulator with chunks flag for granularity control."""
    
    def __init__(
        self, 
        chunks: bool = False,
        on_persist: Optional[Callable[[dict], None]] = None
    ):
        """Initialize accumulator.
        
        Args:
            chunks: If True, yield individual parser events immediately.
                   If False, accumulate into complete semantic events.
            on_persist: Callback for persisting complete semantic events.
        """
        self.chunks = chunks
        self.on_persist = on_persist
        
        # Accumulation state
        self.current_event_type = None
        self.accumulated_content = ""
        self.event_start_time = None
        
    async def process(
        self, 
        parser_events: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process parser events based on chunks flag.
        
        chunks=True: Stream individual events immediately
        chunks=False: Accumulate and emit complete semantic events
        """
        
        async for event in parser_events:
            event_type = Event(event["type"])
            content = event["content"]
            timestamp = event["timestamp"]
            
            # chunks=True: Always yield immediately
            if self.chunks:
                yield event
            
            # Handle state transitions and accumulation
            state_changed = event_type != self.current_event_type
            
            if state_changed:
                # State change - yield previous accumulated event (chunks=False only)
                if not self.chunks and self.current_event_type and self.accumulated_content.strip():
                    yield {
                        "type": self.current_event_type.value,
                        "content": self.accumulated_content,
                        "timestamp": self.event_start_time
                    }
                
                # Persist previous accumulated content
                if self.current_event_type and self.accumulated_content.strip():
                    await self._persist_accumulated_event()
                
                # Start new accumulation
                self.current_event_type = event_type
                self.accumulated_content = content
                self.event_start_time = timestamp
            else:
                # Same event type - accumulate content
                self.accumulated_content += content
                    
        # Final flush - persist any remaining content
        if self.current_event_type and self.accumulated_content.strip():
            await self._persist_accumulated_event()
            
            # Yield final event for non-chunks mode
            if not self.chunks:
                yield {
                    "type": self.current_event_type.value,
                    "content": self.accumulated_content,
                    "timestamp": self.event_start_time
                }
    
    async def _persist_accumulated_event(self):
        """Persist complete accumulated event to DB."""
        if not self.on_persist:
            return
            
        complete_event = {
            "type": self.current_event_type.value,
            "content": self.accumulated_content.strip(),
            "timestamp": self.event_start_time or time.time()
        }
        
        # Safe callback to persister
        self.on_persist(complete_event)
        
        # Reset accumulation
        self.accumulated_content = ""
        self.event_start_time = None