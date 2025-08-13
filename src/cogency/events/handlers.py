"""Event storage and log processing."""

import json
from collections import deque
from pathlib import Path
from typing import Any

from cogency.config.paths import paths


class EventBuffer:
    """Simple event storage for agent.logs() debugging."""

    def __init__(self, max_size: int = 1000):
        self.events = deque(maxlen=max_size)

    def handle(self, event):
        """Store event in buffer."""
        self.events.append(event)

    def logs(
        self,
        *,
        type: str = None,
        errors_only: bool = False,
        last: int = None,
    ) -> list[dict[str, Any]]:
        """Return filtered events for debugging."""
        events = list(self.events)

        if errors_only:
            events = [e for e in events if e.get("type") == "error" or e.get("status") == "error"]
        if type:
            events = [e for e in events if e.get("type") == type]
        if last:
            events = events[-last:]

        return events


class EventLogger:
    """Structured event logging to disk for dogfooding analysis."""

    def __init__(self, log_path: str = None):
        if log_path is None:
            self.log_dir = Path(paths.logs)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = None  # Will be set dynamically
        else:
            self.log_path = Path(log_path)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_daily_log_path(self):
        """Get today's log file path."""
        if self.log_path is not None:
            return self.log_path

        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"{today}.jsonl"

    def handle(self, event):
        """Write structured events to JSONL file."""
        # Filter out noise - focus on meaningful events
        event_type = event.get("type")
        if event_type in ["config_load"]:
            return

        # Create clean log entry
        log_entry = {
            "timestamp": event.get("timestamp"),
            "type": event_type,
            "level": event.get("level", "info"),
        }

        # Add relevant data without nesting - now flattened in event
        for key, value in event.items():
            # Skip core event fields
            if key in ["timestamp", "type", "level"]:
                continue
            # Skip overly verbose fields
            if (
                key in ["messages", "full_response"]
                and isinstance(value, (str, list))
                and len(str(value)) > 200
            ):
                log_entry[key] = f"[{len(str(value))} chars]"
            else:
                log_entry[key] = value

        # Append to daily JSONL file
        try:
            daily_log_path = self._get_daily_log_path()
            with open(daily_log_path, "a") as f:
                f.write(json.dumps(log_entry, default=str) + "\n")
        except Exception:
            # Fail silently - don't break execution for logging issues
            pass
