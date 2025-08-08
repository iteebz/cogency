"""Configuration dataclasses for agent features."""

from dataclasses import dataclass
from typing import Any, List, Optional

# Runtime limits
MAX_TOOL_CALLS = 3  # Limit to prevent JSON parsing issues


@dataclass
class RobustConfig:
    """Robustness configuration."""

    # Core toggles
    retry: bool = False
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
class MemoryConfig:
    """Memory configuration."""

    # Core toggles
    enabled: bool = True
    persist: bool = True

    # Synthesis thresholds
    synthesis_threshold: int = 16000  # Character limit for recent interactions
    max_impressions: int = 50  # Prune oldest impressions past this limit

    # Context injection policy
    recall_steps: List[str] = None  # ["reason"] or None for reason-only

    # User identification
    user_id: str = "default"

    def __post_init__(self):
        if self.recall_steps is None:
            self.recall_steps = ["reason"]  # Default: reason-only


@dataclass
class PathsConfig:
    """Path configuration."""

    base_dir: str = ".cogency"
    checkpoints: Optional[str] = None
    sandbox: Optional[str] = None
    state: Optional[str] = None
    memory: Optional[str] = None
    reports: Optional[str] = None
    evals: Optional[str] = None

    def __post_init__(self):
        """Set defaults under .cogency/"""
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
        if self.evals is None:
            self.evals = f"{self.base_dir}/evals"


@dataclass
class PersistConfig:
    """Configuration for state persistence."""

    enabled: bool = True
    store: Optional[Any] = None  # This will hold the actual store instance (e.g., Filesystem)
    # Add any other persistence-specific settings here


@dataclass
class AgentConfig:
    """Agent configuration container."""

    name: str = "cogency"
    identity: Optional[str] = (
        "You are Cogency, a helpful AI assistant with a knack for getting things done efficiently. Keep it concise and clear."
    )
    output_schema: Optional[Any] = None
    llm: Optional[Any] = None
    embed: Optional[Any] = None
    tools: Optional[Any] = None
    memory: Optional[Any] = None
    mode: str = "adapt"
    max_iterations: Optional[int] = None
    notify: bool = True
    debug: bool = False
    formatter: Optional[Any] = None
    on_notify: Optional[Any] = None
    robust: Optional[Any] = None
    handlers: List[Any] = None


def _setup_config(config_type, param, store=None):
    """Setup configuration object from parameter."""
    if param is False:
        return None
    if isinstance(param, config_type):
        return param
    if param is True:
        return config_type()
    if store:
        return config_type(store=store)
    return None
