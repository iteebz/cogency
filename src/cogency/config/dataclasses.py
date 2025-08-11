"""Configuration dataclasses for agent features."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Union

# Runtime limits
MAX_TOOL_CALLS = 3  # Limit to prevent JSON parsing issues



@dataclass
class MemoryConfig:
    """Memory configuration."""

    # Core toggles
    enabled: bool = True
    persist: bool = True
    archival: bool = True  # Enable archival memory system

    # Synthesis thresholds
    synthesis_threshold: int = 16000  # Character limit for recent interactions
    max_impressions: int = 50  # Prune oldest impressions past this limit

    # Context injection policy
    recall_steps: List[str] = None  # ["reason"] or None for reason-only

    # User identification
    user_id: str = "default"

    # Archival memory path
    path: Optional[str] = None  # Custom path for memory storage

    def __post_init__(self):
        if self.recall_steps is None:
            self.recall_steps = ["reason"]  # Default: reason-only


@dataclass
class PathsConfig:
    """Path configuration."""

    base_dir: str = ".cogency"
    sandbox: Optional[str] = None
    state: Optional[str] = None
    memory: Optional[str] = None
    logs: Optional[str] = None
    reports: Optional[str] = None
    evals: Optional[str] = None

    def __post_init__(self):
        """Set defaults under .cogency/ with environment variable override."""
        import os
        
        # Allow .env override of base directory
        env_base_dir = os.getenv("COGENCY_BASE_DIR")
        if env_base_dir:
            self.base_dir = os.path.expanduser(env_base_dir)
        
        if self.sandbox is None:
            self.sandbox = f"{self.base_dir}/sandbox"
        if self.state is None:
            self.state = f"{self.base_dir}/state"
        if self.memory is None:
            self.memory = f"{self.base_dir}/memory"
        if self.logs is None:
            self.logs = f"{self.base_dir}/logs"
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
    llm: Optional["Provider"] = None
    embed: Optional["Provider"] = None
    tools: Optional[Any] = None
    memory: Optional[Any] = None
    mode: str = "adapt"
    max_iterations: int = 10
    notify: bool = True
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
