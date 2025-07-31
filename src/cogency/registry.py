"""Service registry for dependency injection - no globals."""

from typing import Any, Optional

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig


class ServiceRegistry:
    """Clean dependency injection - no global state."""

    def __init__(self):
        # Core services
        self.llm: Optional[Any] = None
        self.embed: Optional[Any] = None
        self.tools: Optional[Any] = None
        self.memory: Optional[Any] = None

        # Notification system
        self.formatter: Optional[Any] = None
        self.notifier: Optional[Any] = None

        # Configuration
        self.config: Optional[Any] = None
        self.persistence: Optional[Any] = None


class AgentConfig:
    """Single config object - no dynamic type() nonsense."""

    def __init__(self):
        self.robust: Optional[RobustConfig] = None
        self.observe: Optional[ObserveConfig] = None
        self.persist: Optional[PersistConfig] = None
        self.memory: Optional[MemoryConfig] = None
