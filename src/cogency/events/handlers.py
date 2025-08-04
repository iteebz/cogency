"""Event consumption handlers - extensible business logic."""

from collections import deque
from typing import Any, Dict, List


class ConsoleHandler:
    """Clean real-time user feedback - no dual system mess."""

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = debug

    def handle(self, event):
        """Handle notification events with clean output."""
        if not self.enabled:
            return

        event_type = event["type"]
        data = event["data"]

        # Agent lifecycle
        if event_type == "start":
            query = data.get("query", "")
            print("🚀 Starting agent...")
            if query and len(query) < 100:
                print(f"📝 {query}")

        elif event_type == "agent_create":
            name = data.get("name", "agent")
            status = data.get("status", "")
            if status == "complete":
                print(f"✅ Agent '{name}' ready")

        # Processing steps
        elif event_type == "triage":
            state = data.get("state", "")
            if state == "complete":
                tools = data.get("selected_tools", 0)
                if tools:
                    print(f"🔧 Selected {tools} tools")
                else:
                    print("💭 Direct response")

        elif event_type == "reason":
            state = data.get("state", "")
            if state in ["planning", "analyzing"]:
                print(f"🧠 {state.title()}...")

        elif event_type == "action":
            tool = data.get("tool", "tool")
            print(f"⚡ Using {tool}")

        elif event_type == "respond":
            state = data.get("state", "")
            if state == "generating":
                print("📝 Generating...")
            elif state == "complete":
                print("✅ Response ready")

        # Tools
        elif event_type == "tool":
            name = data.get("name", "tool")
            duration = data.get("duration", 0)
            status = data.get("status", "")

            if status == "complete" and data.get("success"):
                timing_info = f" ({duration:.1f}s)" if duration >= 1.0 else ""
                print(f"✅ {name}{timing_info}")
            elif status in ["failed", "validation_error", "execution_error"]:
                timing_info = f" ({duration:.1f}s)" if duration >= 1.0 else ""
                print(f"❌ {name} failed{timing_info}")
            elif data.get("ok"):  # Legacy format
                timing_info = f" ({duration:.1f}s)" if duration >= 1.0 else ""
                print(f"✅ {name}{timing_info}")
            elif status == "start":
                # Don't print start events to reduce noise
                pass

        # Token usage
        elif event_type == "tokens":
            tin = data.get("tin", 0)
            tout = data.get("tout", 0)
            cost = data.get("cost", "$0.0000")
            provider = data.get("provider", "")
            model = data.get("model", "")

            # Only show for significant token usage or high cost
            if tin + tout > 500 or float(cost.replace("$", "")) > 0.01:
                print(f"💰 {tin + tout} tokens {cost} ({provider}/{model})")

        # LLM operations
        elif event_type == "llm":
            provider = data.get("provider", "llm")
            status = data.get("status", "")

            if status == "start":
                # Don't show start to reduce noise
                pass
            elif status == "complete" and data.get("success"):
                print(f"🧠 {provider} complete")
            elif status == "error":
                print(f"❌ {provider} failed")

        # System
        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"❌ {message}")

        elif event_type == "debug" and self.debug:
            message = data.get("message", "Debug")
            print(f"🐛 {message}")

        # Config (quiet unless debug)
        elif event_type == "config_load" and self.debug:
            component = data.get("component", "component")
            status = data.get("status", "")
            if status == "complete":
                print(f"⚙️  {component} loaded")


class LoggerHandler:
    """Centralized structured logging with rolling buffer for agent.logs()."""

    def __init__(self, max_size: int = 1000, structured: bool = True):
        self.events = deque(maxlen=max_size)
        self.structured = structured
        self.config = {
            "max_size": max_size,
            "include_timestamps": True,
            "include_metadata": True,
            "filter_noise": True,  # Skip config_load events by default
        }

    def handle(self, event):
        """Store event with optional filtering."""
        # Filter noise unless debug mode
        if (
            self.config["filter_noise"]
            and event["type"] == "config_load"
            and event["data"].get("status") in ["loading", "complete"]
        ):
            return

        # Store structured event
        if self.structured:
            structured_event = {
                "timestamp": event["timestamp"],
                "type": event["type"],
                **event["data"],  # Flatten data into root level
            }
            self.events.append(structured_event)
        else:
            self.events.append(event)

    def logs(self) -> List[Dict[str, Any]]:
        """Return all stored events in structured format."""
        return list(self.events)

    def configure(self, **options):
        """Update handler configuration."""
        self.config.update(options)


class CallbackHandler:
    """Execute custom callback for each event - websockets, streaming, etc."""

    def __init__(self, callback):
        """Initialize with callback function.

        Args:
            callback: Function called with each event dict
        """
        self.callback = callback

    def handle(self, event):
        """Execute callback with event data."""
        if self.callback:
            self.callback(event)
