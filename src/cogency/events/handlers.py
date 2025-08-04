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
            print("[INIT] Starting agent")
            if query and len(query) < 100:
                print(f"[QUERY] {query}")

        elif event_type == "agent_create":
            name = data.get("name", "agent")
            status = data.get("status", "")
            if status == "complete":
                print(f"[READY] Agent '{name}'")

        # Processing steps
        elif event_type == "triage":
            state = data.get("state", "")
            if state == "complete":
                tools = data.get("selected_tools", 0)
                if tools:
                    print(f"[TRIAGE] {tools} tools selected")
                else:
                    print("[TRIAGE] Direct response mode")

        elif event_type == "reason":
            state = data.get("state", "")
            if state in ["planning", "analyzing"]:
                print(f"[THINK] {state.title()}")

        elif event_type == "action":
            tool = data.get("tool", "tool")
            print(f"[ACTION] {tool}")

        elif event_type == "respond":
            state = data.get("state", "")
            if state == "generating":
                print("[GEN] Generating response")
            elif state == "complete":
                print("[DONE] Response ready")

        # Tools - only show completion/errors
        elif event_type == "tool":
            name = data.get("name", "tool")
            duration = data.get("duration", 0)
            status = data.get("status", "")

            if status == "complete" and data.get("success"):
                timing_info = f" ({duration:.1f}s)" if duration >= 0.1 else ""
                print(f"[TOOL] {name} complete{timing_info}")
            elif status in ["failed", "validation_error", "execution_error"]:
                timing_info = f" ({duration:.1f}s)" if duration >= 0.1 else ""
                print(f"[ERROR] {name} failed{timing_info}")
            elif data.get("ok"):  # Legacy format
                timing_info = f" ({duration:.1f}s)" if duration >= 0.1 else ""
                print(f"[TOOL] {name} complete{timing_info}")

        # Token usage - always show for transparency
        elif event_type == "tokens":
            tin = data.get("tin", 0)
            tout = data.get("tout", 0)
            cost = data.get("cost", "$0.0000")
            provider = data.get("provider", "")
            model = data.get("model", "")

            total_tokens = tin + tout
            model_info = f"{provider}/{model}" if provider and model else ""
            print(f"[COST] {total_tokens} tokens, {cost} {model_info}")

        # LLM operations - show provider detection
        elif event_type == "llm":
            provider = data.get("provider", "llm")
            status = data.get("status", "")

            if status == "complete" and data.get("success"):
                print(f"[LLM] {provider} complete")
            elif status == "error":
                print(f"[ERROR] {provider} failed")

        # System errors - always show
        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"[ERROR] {message}")

        elif event_type == "debug" and self.debug:
            message = data.get("message", "Debug")
            print(f"[DEBUG] {message}")

        # Config (only in debug mode)
        elif event_type == "config_load" and self.debug:
            component = data.get("component", "component")
            status = data.get("status", "")
            if status == "complete":
                print(f"[CONFIG] {component} loaded")


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

    def logs(
        self,
        *,
        type: str = None,
        step: str = None,
        summary: bool = False,
        errors_only: bool = False,
        last: int = None,
    ) -> List[Dict[str, Any]]:
        """Return stored events with optional filtering."""
        all_logs = list(self.events)

        if not all_logs:
            return []

        # Apply filters
        filtered = all_logs

        if errors_only:
            filtered = [log for log in filtered if log.get("type") == "error"]
        elif type:
            filtered = [log for log in filtered if log.get("type") == type]

        if step:
            filtered = [log for log in filtered if log.get("type") == step]

        # Apply summary transformation
        if summary:
            return self._summarize_logs(filtered)

        # Apply last N limit
        if last:
            filtered = filtered[-last:]

        return filtered

    def _summarize_logs(self, logs: List[Dict]) -> List[Dict]:
        """Create high-level execution summary from logs."""
        summary = []

        # Key execution milestones
        key_events = ["start", "triage", "reason", "action", "respond", "agent_complete", "error"]

        for log in logs:
            if log.get("type") in key_events:
                # Clean up event for summary view
                summary_event = {
                    "step": log.get("type"),
                    "timestamp": log.get("timestamp"),
                }

                # Add relevant context
                if log.get("type") == "start":
                    summary_event["query"] = log.get("query", "")[:100]  # Truncate long queries
                elif log.get("type") == "triage":
                    if log.get("state") == "complete":
                        summary_event["mode"] = "direct" if log.get("early_return") else "react"
                elif log.get("type") == "action":
                    summary_event["tool_count"] = log.get("tool_count", 0)
                elif log.get("type") == "agent_complete":
                    summary_event["source"] = log.get("source")
                    summary_event["iterations"] = log.get("iterations", 0)
                elif log.get("type") == "error":
                    summary_event["message"] = log.get("message", "")[:200]  # Truncate long errors

                summary.append(summary_event)

        return summary

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
