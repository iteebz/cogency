"""Configuration dataclasses - runtime limits, robustness, observability settings."""

from dataclasses import dataclass
from typing import Any, List, Optional

# Runtime limits
MAX_TOOL_CALLS = 3  # Limit to prevent JSON parsing issues


@dataclass
class RobustConfig:
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
class ObserveConfig:
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
class MemoryConfig:
    """LLM-native memory configuration - persistence, thresholds, context injection."""

    # Core toggles
    enabled: bool = True
    persist: bool = True

    # Synthesis thresholds
    synthesis_threshold: int = 16000  # Character limit for recent interactions
    max_impressions: int = 50  # Prune oldest impressions past this limit

    # Context injection policy
    recall_phases: List[str] = None  # ["reason", "respond", "both"] or None for reason-only

    # Store configuration
    store: Optional[Any] = None
    user_id: str = "default"

    def __post_init__(self):
        if self.recall_phases is None:
            self.recall_phases = ["reason"]  # Default: reason-only


@dataclass
class PathsConfig:
    """Centralized path configuration with smart .cogency/* defaults."""
    
    base_dir: str = ".cogency"
    checkpoints: Optional[str] = None
    sandbox: Optional[str] = None  
    state: Optional[str] = None
    memory: Optional[str] = None
    reports: Optional[str] = None
    
    def __post_init__(self):
        """Smart defaults under .cogency/"""
        if self.checkpoints is None:
            self.checkpoints = f"{self.base_dir}/checkpoints"
        if self.sandbox is None:
            self.sandbox = f"{self.base_dir}/sandbox"
        if self.state is None:
            self.state = f"{self.base_dir}/state"
        if self.memory is None:
            self.memory = f"{self.base_dir}/memory"
        if self.reports is None:
            self.reports = f"{self.base_dir}/reports"


@dataclass
class PersistConfig:
    """Configuration for state persistence."""

    enabled: bool = True
    store: Optional[Any] = None  # This will hold the actual store instance (e.g., Filesystem)
    # Add any other persistence-specific settings here


def setup_config(config_type, param, store=None):
    if param is False:
        return None
    if isinstance(param, config_type):
        return param
    if param is True:
        return config_type()
    if store:
        return config_type(store=store)
    return None
