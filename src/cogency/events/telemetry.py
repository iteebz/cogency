"""CLI Telemetry Bridge - unified event surfacing via existing infrastructure."""

import asyncio
import time
from collections import deque
from typing import AsyncIterator, Dict, Any, Optional, List

from .bus import MessageBus
from .handlers import EventBuffer


class TelemetryBridge:
    """Bridge events to CLI telemetry with zero ceremony."""
    
    def __init__(self, bus: MessageBus = None):
        self.bus = bus
        self.buffer = EventBuffer(max_size=500) 
        self._live_stream = None
        self._filters = {}
        
        if bus:
            bus.subscribe(self.buffer)
    
    def stream_live(self, filters: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream live events with optional filtering."""
        return self._stream_events(live=True, filters=filters)
    
    def get_recent(self, count: int = 20, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get recent events with filtering."""
        events = list(self.buffer.events)
        
        # Apply filters
        if filters:
            events = self._apply_filters(events, filters)
        
        return events[-count:] if count else events
    
    def get_summary(self) -> Dict[str, Any]:
        """Get telemetry summary for current session."""
        events = list(self.buffer.events)
        
        if not events:
            return {"total_events": 0, "session_start": None}
        
        # Calculate metrics
        event_types = {}
        tools_used = set()
        iterations = 0
        errors = 0
        start_time = None
        end_time = None
        
        for event in events:
            event_type = event.get("type")
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Track timing
            timestamp = event.get("timestamp")
            if timestamp:
                if start_time is None or timestamp < start_time:
                    start_time = timestamp
                if end_time is None or timestamp > end_time:
                    end_time = timestamp
            
            # Extract metrics from event data
            data = event.get("data", {})
            
            if event_type == "tool" and data.get("status") == "complete":
                tools_used.add(data.get("name", "unknown"))
            elif event_type == "agent" and data.get("state") == "iteration":
                iterations += 1
            elif event.get("level") == "error" or data.get("status") == "error":
                errors += 1
        
        duration = (end_time - start_time) if (start_time and end_time) else 0
        
        return {
            "total_events": len(events),
            "event_types": event_types,
            "tools_used": list(tools_used),
            "iterations": iterations,
            "errors": errors,
            "duration": duration,
            "session_start": start_time,
        }
    
    def format_event(self, event: Dict[str, Any], style: str = "compact") -> str:
        """Format event for beautiful CLI display."""
        if style == "compact":
            return self._format_compact(event)
        elif style == "detailed":
            return self._format_detailed(event)
        elif style == "json":
            import json
            return json.dumps(event, default=str, indent=2)
        else:
            return str(event)
    
    def _format_compact(self, event: Dict[str, Any]) -> str:
        """Compact single-line event format."""
        timestamp = event.get("timestamp", time.time())
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        event_type = event.get("type", "unknown")
        level = event.get("level", "info")
        data = event.get("data", {})
        
        # Choose emoji based on event type and level
        emoji = self._get_event_emoji(event_type, level, data)
        
        # Format content based on event type
        content = self._get_event_content(event_type, data)
        
        # Level indicator
        level_color = self._get_level_color(level)
        
        return f"{time_str} {emoji} [{event_type}] {content} {level_color}"
    
    def _format_detailed(self, event: Dict[str, Any]) -> str:
        """Detailed multi-line event format."""
        lines = []
        timestamp = event.get("timestamp", time.time())
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        
        # Header
        event_type = event.get("type", "unknown")
        level = event.get("level", "info")
        emoji = self._get_event_emoji(event_type, level, event.get("data", {}))
        
        lines.append(f"{emoji} {event_type.upper()} ({level}) - {time_str}")
        
        # Data details
        data = event.get("data", {})
        if data:
            for key, value in data.items():
                if key == "error" and value:
                    lines.append(f"  ❌ Error: {value}")
                elif key == "status":
                    status_emoji = "✅" if value == "complete" else "⏳" if value == "start" else "❌"
                    lines.append(f"  {status_emoji} Status: {value}")
                elif key in ["name", "operation", "tool"]:
                    lines.append(f"  🔧 Tool: {value}")
                elif key == "iteration":
                    lines.append(f"  🔄 Iteration: {value}")
                elif key == "response_length":
                    lines.append(f"  📏 Response: {value} chars")
                else:
                    lines.append(f"  • {key}: {value}")
        
        return "\\n".join(lines)
    
    def _get_event_emoji(self, event_type: str, level: str, data: Dict[str, Any]) -> str:
        """Get appropriate emoji for event type and context."""
        if level == "error":
            return "❌"
        
        emoji_map = {
            "agent": "🧠",
            "tool": "🔧", 
            "reason": "💭",
            "respond": "💬",
            "memory": "💾",
            "security": "🔒",
            "config_load": "⚙️",
            "log": "📝",
        }
        
        emoji = emoji_map.get(event_type, "📊")
        
        # Context-specific overrides
        if event_type == "tool":
            status = data.get("status")
            if status == "complete":
                emoji = "✅"
            elif status == "error":
                emoji = "❌"
        elif event_type == "agent":
            state = data.get("state")
            if state == "complete":
                emoji = "🎯"
            elif state == "error":
                emoji = "❌"
        
        return emoji
    
    def _get_event_content(self, event_type: str, data: Dict[str, Any]) -> str:
        """Extract meaningful content from event data."""
        if event_type == "tool":
            name = data.get("name", "unknown")
            operation = data.get("operation")
            status = data.get("status")
            if operation and operation != name:
                return f"{name}.{operation} → {status}"
            return f"{name} → {status}"
        
        elif event_type == "agent":
            state = data.get("state", "unknown")
            iteration = data.get("iteration")
            if state == "iteration" and iteration is not None:
                return f"iteration {iteration}"
            return state
        
        elif event_type == "reason":
            state = data.get("state", "unknown")
            return f"reasoning → {state}"
        
        elif event_type == "memory":
            operation = data.get("operation", "unknown")
            return f"memory.{operation}"
        
        elif event_type == "security":
            operation = data.get("operation", "assess")
            return f"security.{operation}"
        
        else:
            # Generic content extraction
            important_keys = ["name", "operation", "state", "status", "message"]
            content_parts = []
            for key in important_keys:
                if key in data:
                    content_parts.append(str(data[key]))
            return " ".join(content_parts) if content_parts else "event"
    
    def _get_level_color(self, level: str) -> str:
        """Get color indicator for log level (simplified for CLI)."""
        color_map = {
            "debug": "🔍",
            "info": "",
            "warning": "⚠️", 
            "error": "🚨",
        }
        return color_map.get(level, "")
    
    def _apply_filters(self, events: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to event list."""
        filtered = events
        
        if "type" in filters:
            event_type = filters["type"]
            filtered = [e for e in filtered if e.get("type") == event_type]
        
        if "level" in filters:
            level = filters["level"]
            filtered = [e for e in filtered if e.get("level") == level]
        
        if "errors_only" in filters and filters["errors_only"]:
            filtered = [e for e in filtered if e.get("level") == "error" or 
                       e.get("data", {}).get("status") == "error"]
        
        if "since" in filters:
            since = filters["since"]
            filtered = [e for e in filtered if e.get("timestamp", 0) >= since]
        
        if "tool" in filters:
            tool_name = filters["tool"]
            filtered = [e for e in filtered if e.get("type") == "tool" and 
                       e.get("data", {}).get("name") == tool_name]
        
        return filtered
    
    async def _stream_events(self, live: bool = True, filters: Dict[str, Any] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream events with optional live mode."""
        if not live:
            # Return existing events
            events = self.get_recent(filters=filters)
            for event in events:
                yield event
            return
        
        # Live streaming (placeholder - would need real-time event queue)
        # For now, poll the buffer for new events
        last_seen = len(self.buffer.events)
        
        while True:
            current_size = len(self.buffer.events)
            if current_size > last_seen:
                # New events arrived
                new_events = list(self.buffer.events)[last_seen:]
                for event in new_events:
                    if not filters or event in self._apply_filters([event], filters):
                        yield event
                last_seen = current_size
            
            await asyncio.sleep(0.1)  # Poll every 100ms


# Export canonical functions for CLI integration
def create_telemetry_bridge(bus: MessageBus = None) -> TelemetryBridge:
    """Create telemetry bridge with existing bus."""
    return TelemetryBridge(bus)


def format_telemetry_summary(bridge: TelemetryBridge) -> str:
    """Format beautiful telemetry summary for CLI display."""
    summary = bridge.get_summary()
    
    if summary["total_events"] == 0:
        return "📊 No telemetry data available"
    
    lines = ["📊 Telemetry Summary", "=" * 50]
    
    # Basic metrics
    lines.append(f"Total events: {summary['total_events']}")
    
    if summary["duration"]:
        lines.append(f"Session duration: {summary['duration']:.1f}s")
    
    if summary["iterations"]:
        lines.append(f"Reasoning iterations: {summary['iterations']}")
    
    if summary["errors"]:
        lines.append(f"Errors: {summary['errors']} ❌")
    
    # Tools used
    if summary["tools_used"]:
        tools_str = ", ".join(summary["tools_used"])
        lines.append(f"Tools used: {tools_str}")
    
    # Event breakdown
    if summary["event_types"]:
        lines.append("\\nEvent Types:")
        for event_type, count in sorted(summary["event_types"].items()):
            emoji = TelemetryBridge(None)._get_event_emoji(event_type, "info", {})
            lines.append(f"  {emoji} {event_type}: {count}")
    
    return "\\n".join(lines)