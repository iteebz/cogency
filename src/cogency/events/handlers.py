"""Event storage and log processing."""

from collections import deque
from typing import Any, Dict, List


class LoggerHandler:
    """Centralized structured logging with rolling buffer for agent.logs()."""

    def __init__(self, max_size: int = 1000, structured: bool = True, level: str = "info"):
        self.events = deque(maxlen=max_size)
        self.structured = structured
        self.level = level
        self.filter_noise = True  # Skip config_load events by default
        self.config = {
            "max_size": max_size,
            "structured": structured,
            "level": level,
            "filter_noise": True,
        }

    def handle(self, event):
        """Store event with level filtering."""
        # Level-based filtering
        event_level = event.get("level", "info")
        if self.level == "info" and event_level == "debug":
            return

        # Filter noise unless debug mode
        if (
            self.filter_noise
            and event.get("type") == "config_load"
            and event.get("data", {}).get("status") in ["loading", "complete"]
        ):
            return

        # Store structured event
        if self.structured:
            structured_event = {
                "timestamp": event.get("timestamp"),
                "type": event.get("type"),
                **event.get("data", {}),  # Flatten data into root level
            }
            # Only include level if it's not the default
            if event_level != "info":
                structured_event["level"] = event_level
            self.events.append(structured_event)
        else:
            self.events.append(event)

    def logs(
        self,
        *,
        mode: str = "debug",
        type: str = None,
        step: str = None,
        summary: bool = None,  # Deprecated, use mode="summary"
        errors_only: bool = False,
        last: int = None,
    ) -> List[Dict[str, Any]]:
        """Return processed logs based on mode."""
        all_logs = list(self.events)

        if not all_logs:
            return []

        # Handle deprecated summary parameter
        if summary is not None:
            if summary:
                return self._build_legacy_summary(all_logs, last=last)
            else:
                mode = "debug"

        if mode == "summary":
            return self._build_execution_summary(all_logs, last=last)
        elif mode == "performance":
            return self._build_performance_analysis(all_logs, last=last)
        elif mode == "errors":
            return self._extract_error_analysis(all_logs, last=last)
        elif mode == "debug":
            return self._get_raw_events(
                all_logs, type=type, step=step, errors_only=errors_only, last=last
            )
        else:
            return self._build_execution_summary(all_logs, last=last)

    def _build_execution_summary(
        self, logs: List[Dict[str, Any]], last: int = None
    ) -> List[Dict[str, Any]]:
        """Build developer-friendly execution summaries."""
        summaries = []
        current_execution = None

        events = logs[-last:] if last else logs

        for event in events:
            event_type = event.get("type")
            timestamp = event.get("timestamp")

            # Start new execution tracking
            if event_type == "start":
                current_execution = {
                    "execution_id": f"exec_{int(timestamp)}",
                    "query": event.get("query", ""),
                    "start_time": timestamp,
                    "mode": "direct_response",  # Default assumption
                    "iterations": 0,
                    "tools_used": [],
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "provider_info": {},
                    "success": False,
                    "response_source": "unknown",
                    "errors": [],
                }

            elif current_execution:
                # Track execution details
                if event_type == "triage" and not event.get("early_return"):
                    current_execution["mode"] = "react"

                elif event_type == "react_iteration":
                    current_execution["iterations"] = event.get("iteration", 0)

                elif event_type == "tool" and event.get("status") == "complete":
                    tool_name = event.get("name", "unknown")
                    if tool_name not in current_execution["tools_used"]:
                        current_execution["tools_used"].append(tool_name)

                elif event_type == "tokens":
                    cost_str = event.get("cost", "$0")
                    if isinstance(cost_str, str) and cost_str.startswith("$"):
                        current_execution["total_cost"] += float(cost_str[1:])
                    current_execution["total_tokens"] += event.get("tin", 0) + event.get("tout", 0)
                    current_execution["provider_info"] = {
                        "provider": event.get("provider", ""),
                        "model": event.get("model", ""),
                    }

                elif event_type == "error":
                    current_execution["errors"].append(
                        {"message": event.get("message", ""), "timestamp": timestamp}
                    )

                elif event_type == "agent_complete":
                    current_execution["success"] = True
                    current_execution["response_source"] = event.get("source", "triage")
                    current_execution["duration"] = timestamp - current_execution["start_time"]

                    # Format for developer consumption
                    summary = {
                        "execution_id": current_execution["execution_id"],
                        "query": current_execution["query"][:100] + "..."
                        if len(current_execution["query"]) > 100
                        else current_execution["query"],
                        "mode": current_execution["mode"],
                        "duration": round(current_execution["duration"], 2),
                        "iterations": current_execution["iterations"],
                        "tools_used": current_execution["tools_used"],
                        "cost": f"${current_execution['total_cost']:.4f}",
                        "tokens": current_execution["total_tokens"],
                        "provider": f"{current_execution['provider_info'].get('provider', '')}/{current_execution['provider_info'].get('model', '')}",
                        "success": current_execution["success"],
                        "response_source": current_execution["response_source"],
                        "error_count": len(current_execution["errors"]),
                    }

                    summaries.append(summary)
                    current_execution = None

        return summaries

    def _build_performance_analysis(
        self, logs: List[Dict[str, Any]], last: int = None
    ) -> List[Dict[str, Any]]:
        """Build performance-focused analysis for optimization."""
        performance_data = []
        step_timings = {}
        current_step = None
        step_start = None

        events = logs[-last:] if last else logs

        for event in events:
            event_type = event.get("type")
            timestamp = event.get("timestamp")

            # Track step boundaries - simplified for actual event structure
            if event_type in ["triage", "reason", "action", "respond"]:
                if current_step and step_start:
                    # Close previous step
                    duration = timestamp - step_start
                    if current_step not in step_timings:
                        step_timings[current_step] = []
                    step_timings[current_step].append(duration)

                current_step = event_type
                step_start = timestamp

        # Aggregate step performance
        for step, durations in step_timings.items():
            performance_data.append(
                {
                    "step": step,
                    "avg_duration": round(sum(durations) / len(durations), 3),
                    "min_duration": round(min(durations), 3),
                    "max_duration": round(max(durations), 3),
                    "call_count": len(durations),
                }
            )

        return performance_data

    def _extract_error_analysis(
        self, logs: List[Dict[str, Any]], last: int = None
    ) -> List[Dict[str, Any]]:
        """Extract and analyze errors for debugging."""
        errors = []

        events = logs[-last:] if last else logs

        for event in events:
            if event.get("type") == "error" or event.get("status") == "error":
                error_info = {
                    "timestamp": event.get("timestamp"),
                    "type": event.get("type"),
                    "message": event.get("message", event.get("error", "Unknown error")),
                    "context": {
                        k: v
                        for k, v in event.items()
                        if k not in ["message", "error", "timestamp", "type"]
                    },
                }
                errors.append(error_info)

        return errors

    def _get_raw_events(
        self,
        logs: List[Dict[str, Any]],
        type: str = None,
        step: str = None,
        errors_only: bool = False,
        last: int = None,
    ) -> List[Dict[str, Any]]:
        """Return raw events for deep debugging."""
        events = logs

        if errors_only:
            events = [e for e in events if e.get("type") == "error" or e.get("status") == "error"]
        if type:
            events = [e for e in events if e.get("type") == type]
        if step:
            events = [e for e in events if e.get("type") == step]

        if last:
            events = events[-last:]

        return events

    def _build_legacy_summary(
        self, logs: List[Dict[str, Any]], last: int = None
    ) -> List[Dict[str, Any]]:
        """Build legacy summary format for backward compatibility."""
        # Legacy summary returns meaningful step events, not execution summaries
        meaningful_types = ["start", "triage", "reason", "action", "respond", "agent_complete"]
        events = logs[-last:] if last else logs

        summary_events = []
        for event in events:
            event_type = event.get("type")
            if event_type in meaningful_types:
                # Transform to expected format
                summary_event = {
                    "step": "complete" if event_type == "agent_complete" else event_type,
                    "timestamp": event.get("timestamp"),
                    "type": event_type,
                    **{k: v for k, v in event.items() if k not in ["type", "timestamp"]},
                }

                # Add specific fields based on event type
                if event_type == "start":
                    summary_event["query"] = event.get("query", "")
                elif event_type == "triage" and not event.get("early_return"):
                    summary_event["mode"] = "react"

                summary_events.append(summary_event)

        return summary_events

    def configure(self, **options):
        """Update handler configuration."""
        for key, value in options.items():
            if hasattr(self, key):
                setattr(self, key, value)
            # Also update config dict
            if key in self.config:
                self.config[key] = value
