"""Modular agent configuration setup - zero duplication."""

from cogency.config import MemoryConfig, PersistConfig, RobustConfig
from cogency.config.dataclasses import AgentConfig, _setup_config
from cogency.events import ConsoleHandler, LoggerHandler, MessageBus, init_bus
from cogency.memory import ImpressionSynthesizer
from cogency.providers.setup import _setup_embed, _setup_llm

# Simplified observability - no complex metrics handlers needed
from cogency.storage.backends.base import _setup_persist
from cogency.tools.registry import _setup_tools


class AgentSetup:
    """Modular agent component setup - explicit, no duplication."""

    @staticmethod
    def llm(config):
        """Setup LLM provider."""
        return _setup_llm(config)

    @staticmethod
    def embed(config, memory_config):
        """Setup embedding provider - only if memory enabled."""
        if memory_config:
            return _setup_embed(config)
        return None

    @staticmethod
    def tools(config):
        """Setup tool registry."""
        return _setup_tools(config or [], None)

    @staticmethod
    def memory(config, llm, persist_config=None):
        """Setup memory system."""
        memory_config = _setup_config(MemoryConfig, config)
        if not memory_config:
            return None

        store = persist_config.store if persist_config else None
        memory = ImpressionSynthesizer(llm, store=store)
        memory.synthesis_threshold = memory_config.synthesis_threshold
        return memory

    @staticmethod
    def persistence(config):
        """Setup persistence layer."""
        persist_config = _setup_config(PersistConfig, config)
        return _setup_persist(persist_config)

    @staticmethod
    def events(config):
        """Setup event system with handlers."""
        bus = MessageBus()

        # Add console handler if enabled
        if config.notify:
            bus.subscribe(ConsoleHandler())

        bus.subscribe(LoggerHandler())

        # Add custom handlers
        if config.handlers:
            for handler in config.handlers:
                if callable(handler) and not hasattr(handler, "handle"):
                    # Function - wrap in simple handler
                    class FunctionHandler:
                        def __init__(self, func):
                            self.func = func

                        def handle(self, event):
                            self.func(event)

                    bus.subscribe(FunctionHandler(handler))
                else:
                    bus.subscribe(handler)

        init_bus(bus)
        return bus

    @staticmethod
    def config(config):
        """Setup unified agent config."""
        agent_config = AgentConfig()
        agent_config.robust = _setup_config(RobustConfig, config.robust)
        agent_config.memory = _setup_config(MemoryConfig, config.memory)

        return agent_config
