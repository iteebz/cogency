"""Event storage and log processing."""

import json
import logging
import os
from collections import deque
from pathlib import Path
from typing import Any, Dict, List


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
    ) -> List[Dict[str, Any]]:
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
            from cogency.config.dataclasses import PathsConfig

            paths = PathsConfig()
            self.log_dir = Path(os.path.expanduser(paths.logs))
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

        # Add relevant data without nesting
        data = event.get("data", {})
        for key, value in data.items():
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


class LoggingBridge(logging.Handler):
    """Bridge standard Python logging into event system."""

    def emit(self, record):
        """Convert log record to event emission."""
        from .core import emit

        # Convert logging level to event level
        level_mapping = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
            logging.CRITICAL: "error",
        }

        emit(
            "log",
            level=level_mapping.get(record.levelno, "info"),
            logger=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
        )
