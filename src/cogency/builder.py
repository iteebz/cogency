"""Agent builder with fluent interface - zero ceremony construction."""

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

if TYPE_CHECKING:
    from cogency.agent import Agent

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig
from cogency.notify import Formatter
from cogency.services import LLM, Embed
from cogency.tools import Tool


class AgentConfig:
    """Single config object - no dynamic type() nonsense."""

    def __init__(self):
        # Core
        self.name: str = "cogency"
        self.identity: Optional[str] = None
        self.output_schema: Optional[Dict[str, Any]] = None

        # Services
        self.llm: Optional[LLM] = None
        self.embed: Optional[Embed] = None
        self.tools: Optional[List[Tool]] = None

        # Memory
        self.memory: Union[bool, MemoryConfig] = False

        # Execution
        self.mode: str = "adapt"
        self.depth: int = 10

        # Feedback
        self.notify: bool = True
        self.debug: bool = False
        self.formatter: Optional[Formatter] = None
        self.on_notify: Optional[Callable] = None

        # System behaviors
        self.robust: Union[bool, RobustConfig] = True
        self.observe: Union[bool, ObserveConfig] = False
        self.persist: Union[bool, PersistConfig] = False

        # Integrations
        self.mcp: bool = False


class AgentBuilder:
    """Fluent interface for zero-ceremony Agent construction."""

    def __init__(self, name: str = "cogency"):
        self._config = AgentConfig()
        self._config.name = name

    # Core configuration
    def with_identity(self, identity: str) -> "AgentBuilder":
        """Set agent identity/personality."""
        new_builder = self._copy()
        new_builder._config.identity = identity
        return new_builder

    def with_schema(self, schema: Dict[str, Any]) -> "AgentBuilder":
        """Set output schema."""
        new_builder = self._copy()
        new_builder._config.output_schema = schema
        return new_builder

    # Services
    def with_llm(self, llm: LLM) -> "AgentBuilder":
        """Set custom LLM."""
        new_builder = self._copy()
        new_builder._config.llm = llm
        return new_builder

    def with_embed(self, embed: Embed) -> "AgentBuilder":
        """Set custom embedding service."""
        new_builder = self._copy()
        new_builder._config.embed = embed
        return new_builder

    def with_tools(self, tools: Union[List[str], List[Tool]]) -> "AgentBuilder":
        """Add tools by name or instances."""
        new_builder = self._copy()
        new_builder._config.tools = tools
        return new_builder

    # Memory
    def with_memory(
        self, store=None, user_id: Optional[str] = None, synthesis_threshold: int = 10
    ) -> "AgentBuilder":
        """Enable memory with optional config."""
        new_builder = self._copy()
        if store or user_id or synthesis_threshold != 10:
            new_builder._config.memory = MemoryConfig(
                store=store, user_id=user_id, synthesis_threshold=synthesis_threshold
            )
        else:
            new_builder._config.memory = True
        return new_builder

    # Execution modes
    def fast_mode(self) -> "AgentBuilder":
        """Set fast execution mode."""
        new_builder = self._copy()
        new_builder._config.mode = "fast"
        return new_builder

    def deep_mode(self) -> "AgentBuilder":
        """Set deep reasoning mode."""
        new_builder = self._copy()
        new_builder._config.mode = "deep"
        return new_builder

    def adapt_mode(self) -> "AgentBuilder":
        """Set adaptive mode (default)."""
        new_builder = self._copy()
        new_builder._config.mode = "adapt"
        return new_builder

    def with_depth(self, depth: int) -> "AgentBuilder":
        """Set reasoning depth."""
        new_builder = self._copy()
        new_builder._config.depth = depth
        return new_builder

    # Feedback
    def debug(self, enabled: bool = True) -> "AgentBuilder":
        """Enable debug mode."""
        new_builder = self._copy()
        new_builder._config.debug = enabled
        return new_builder

    def silent(self) -> "AgentBuilder":
        """Disable notifications."""
        new_builder = self._copy()
        new_builder._config.notify = False
        return new_builder

    def with_formatter(self, formatter: Formatter) -> "AgentBuilder":
        """Set custom formatter."""
        new_builder = self._copy()
        new_builder._config.formatter = formatter
        return new_builder

    def with_callback(self, callback: Callable) -> "AgentBuilder":
        """Set notification callback."""
        new_builder = self._copy()
        new_builder._config.on_notify = callback
        return new_builder

    # System behaviors
    def robust(self, attempts: int = 3, backoff: float = 1.0) -> "AgentBuilder":
        """Enable robust execution with retries."""
        new_builder = self._copy()
        new_builder._config.robust = RobustConfig(attempts=attempts, backoff=backoff)
        return new_builder

    def observe(self, metrics: bool = True, timing: bool = True) -> "AgentBuilder":
        """Enable observability."""
        new_builder = self._copy()
        new_builder._config.observe = ObserveConfig(metrics=metrics, timing=timing)
        return new_builder

    def persist(self, store=None) -> "AgentBuilder":
        """Enable persistence."""
        new_builder = self._copy()
        new_builder._config.persist = PersistConfig(enabled=True, store=store)
        return new_builder

    # Integrations
    def with_mcp(self) -> "AgentBuilder":
        """Enable MCP server."""
        new_builder = self._copy()
        new_builder._config.mcp = True
        return new_builder

    # Build
    def build(self) -> "Agent":
        """Build the Agent instance."""
        from cogency.agent import Agent

        return Agent._from_config(self._config)

    def _copy(self) -> "AgentBuilder":
        """Create a copy for immutable chaining."""
        import copy

        new_builder = AgentBuilder.__new__(AgentBuilder)
        new_builder._config = copy.deepcopy(self._config)
        return new_builder


# Convenience function
def agent_builder(name: str = "cogency") -> AgentBuilder:
    """Create Agent builder with fluent interface."""
    return AgentBuilder(name)
