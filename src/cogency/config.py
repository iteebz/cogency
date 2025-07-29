from dataclasses import dataclass
from typing import Any, List, Optional

# Runtime limits
MAX_TOOL_CALLS = 3  # Limit to prevent JSON parsing issues


@dataclass
class Robust:
    """Comprehensive robustness configuration (retry, checkpointing, circuit breaker, rate limiting)."""

    # Core toggles
    retry: bool = True
    circuit: bool = True
    rate_limit: bool = True
    checkpoint: bool = True

    # Retry policy (from resilient-result)
    attempts: int = 3
    timeout: Optional[float] = None

    # Backoff strategy
    backoff: str = "exponential"  # "exponential", "linear", "fixed"
    backoff_delay: float = 0.1
    backoff_factor: float = 2.0
    backoff_max: float = 30.0

    # Circuit breaker (disabled by default)
    circuit_failures: int = 5
    circuit_window: int = 300

    # Rate limiting (disabled by default)
    rate_limit_rps: float = 10.0
    rate_limit_burst: Optional[int] = None

    # Checkpointing
    ckpt_max_age: int = 1
    ckpt_dir: Optional[str] = None


@dataclass
class Observe:
    """Observability/telemetry configuration for metrics collection."""

    # Metrics collection
    metrics: bool = True
    timing: bool = True
    counters: bool = True

    # Phase-specific telemetry
    phases: Optional[List[str]] = None  # ["reason", "act"] or None for all

    # Export configuration
    export_format: str = "prometheus"  # "prometheus", "json", "opentelemetry"
    export_endpoint: Optional[str] = None


@dataclass
class Persist:
    """Configuration for state persistence."""

    enabled: bool = True
    backend: Optional[Any] = None  # This will hold the actual backend instance (e.g., FileBackend)
    # Add any other persistence-specific settings here


def setup_config(config_type, param, backend=None):
    """Setup config objects with auto-detection."""
    if param is False:
        return None
    if isinstance(param, config_type):
        return param
    if param is True:
        return config_type()
    if backend:
        return config_type(backend=backend)
    return None
