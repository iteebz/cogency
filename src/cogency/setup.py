"""Modular agent configuration setup - zero duplication."""

from cogency.config import PersistConfig
from cogency.config.dataclasses import _setup_config
from cogency.events import ConsoleHandler, EventBuffer, EventLogger, MessageBus, init_bus
from cogency.events.handlers import LoggingBridge
from cogency.memory.situated import SituatedMemory
from cogency.providers.setup import _setup_embed, _setup_llm

# Simplified observability - no complex metrics handlers needed
from cogency.storage.state import _setup_persist
from cogency.tools.registry import _setup_tools


class AgentSetup:
    """Modular agent component setup - explicit, no duplication."""

    @staticmethod
    def llm(config):
        """Setup LLM provider."""
        return _setup_llm(config)

    @staticmethod
    def embed(config):
        """Setup embedding provider."""
        return _setup_embed(config)

    @staticmethod
    def tools(config):
        """Setup tool registry."""
        return _setup_tools(config or [], None)

    @staticmethod
    def memory(config, llm, persist_config=None, embed_provider=None):
        """Setup memory system with direct dependency injection."""
        # Handle different memory config patterns
        if config is False or config is None:
            return None

        # If already a memory instance, pass through
        if hasattr(config, "update_impression"):  # Duck typing for memory instance
            return config

        # Default case: config=True → create default situated memory
        if config is True:
            store = persist_config if persist_config else None

            # Default archival memory setup
            archival = None
            from cogency.memory.archival import ArchivalMemory

            if not embed_provider:
                from cogency.providers.nomic import Nomic

                embed_provider = Nomic()

            archival = ArchivalMemory(llm, embed_provider)

            return SituatedMemory(llm, store=store, archival=archival)

        # Invalid config
        raise ValueError(
            f"Invalid memory config: {config}. Use True, False, or SituatedMemory instance."
        )

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

        bus.subscribe(EventBuffer())
        bus.subscribe(EventLogger())

        # Configure standard logging to flow through events
        import logging

        root_logger = logging.getLogger("cogency")
        root_logger.setLevel(logging.INFO)
        # Clear any existing handlers to avoid duplication
        root_logger.handlers.clear()
        root_logger.addHandler(LoggingBridge())

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
