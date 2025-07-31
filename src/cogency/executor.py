"""Agent execution engine - handles all complexity."""

import asyncio
from typing import Any, AsyncIterator, Optional

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig, setup_config
from cogency.mcp import setup_mcp
from cogency.memory import Memory
from cogency.notify import Notifier, setup_formatter
from cogency.persist.utils import get_state
from cogency.phases import setup_phases
from cogency.registry import AgentConfig, ServiceRegistry
from cogency.services import setup_embed, setup_llm
from cogency.state import State
from cogency.tools import setup_tools
from cogency.utils import validate_query


class AgentExecutor:
    """Handles all agent complexity - service setup, dependency injection, execution."""
    
    def __init__(self, name: str, registry: ServiceRegistry):
        self.name = name
        self._registry = registry
        self.user_states: dict[str, State] = {}
        self.last_state: Optional[dict] = None
        
        # Extract config properties
        self.mode = "adapt"
        self.depth = 10
        self.notify = True
        self.debug = False
        self.identity = ""
        self.output_schema = None
        self.on_notify = None
        
        # Setup dependencies
        self.llm = registry.llm
        self.embed = registry.embed
        self.tools = registry.tools
        self.memory = registry.memory
        self.formatter = registry.formatter
        self.notifier = registry.notifier
        self.config = registry.config
        self.persistence = registry.persistence
        
        # Setup phases
        self.phases = setup_phases(
            self.llm, self.tools, self.memory, self.identity, self.output_schema
        )
        self.mcp_server = setup_mcp(self, False)
    
    @classmethod
    async def create(cls, name: str) -> "AgentExecutor":
        """Create executor with default configuration."""
        registry = ServiceRegistry()
        
        # Setup services
        registry.llm = setup_llm(None)
        registry.embed = setup_embed(None)
        registry.tools = setup_tools(None, None)
        registry.formatter = setup_formatter(True, False)
        registry.notifier = Notifier(registry.formatter, None)
        
        # Setup config
        registry.config = AgentConfig()
        registry.config.robust = setup_config(RobustConfig, True)
        registry.config.observe = setup_config(ObserveConfig, False)
        registry.config.persist = setup_config(PersistConfig, False)
        registry.config.memory = setup_config(MemoryConfig, False)
        
        registry.memory = None
        registry.persistence = None
        
        return cls(name, registry)
    
    @classmethod
    async def from_config(cls, config) -> "AgentExecutor":
        """Create executor from builder config."""
        from cogency.persist import setup_persistence
        
        # Create registry with dependencies
        registry = ServiceRegistry()
        registry.llm = setup_llm(config.llm)
        registry.embed = setup_embed(config.embed)
        registry.tools = setup_tools(config.tools, None)
        registry.formatter = config.formatter or setup_formatter(config.notify, config.debug)
        registry.notifier = Notifier(registry.formatter, config.on_notify)
        
        # Setup configs
        persist_config = setup_config(
            PersistConfig,
            config.persist,
            store=getattr(config.persist, "store", None)
            if hasattr(config.persist, "store")
            else None,
        )
        memory_config = setup_config(MemoryConfig, config.memory)
        
        registry.config = AgentConfig()
        registry.config.robust = setup_config(RobustConfig, config.robust)
        registry.config.observe = setup_config(ObserveConfig, config.observe)
        registry.config.persist = persist_config
        registry.config.memory = memory_config
        
        # Setup memory
        if memory_config:
            store = memory_config.store or (persist_config.store if persist_config else None)
            registry.memory = Memory(registry.llm, store=store, user_id=memory_config.user_id)
            registry.memory.synthesis_threshold = memory_config.synthesis_threshold
        else:
            registry.memory = None
        
        registry.persistence = setup_persistence(persist_config)
        
        # Create executor
        executor = cls(config.name, registry)
        executor.mode = config.mode
        executor.depth = config.depth
        executor.notify = config.notify
        executor.debug = config.debug
        executor.identity = config.identity or ""
        executor.output_schema = config.output_schema
        
        # Re-setup phases with updated config
        executor.phases = setup_phases(
            registry.llm,
            registry.tools,
            registry.memory,
            executor.identity,
            executor.output_schema,
        )
        
        # Setup MCP
        executor.mcp_server = setup_mcp(executor, config.mcp)
        
        return executor
    
    def _setup_notifier(self, callback=None):
        """Setup notification system."""
        return Notifier(formatter=self.formatter, on_notify=callback or self.on_notify)
    
    async def run(self, query: str, user_id: str = "default") -> str:
        """Execute agent and return complete response."""
        try:
            # Input validation
            error = validate_query(query)
            if error:
                return error
            
            # Get or create state
            state = await get_state(
                user_id,
                query,
                self.depth,
                self.user_states,
                self.config.persist,
            )
            
            state.add_message("user", query)
            
            # Memory operations
            if self.memory:
                await self.memory.load()
                await self.memory.remember(query, human=True)
            
            # Set agent mode
            state.agent_mode = self.mode
            if self.mode != "adapt":
                state.mode = self.mode
            
            # Execute phases
            from cogency.execution import run_agent
            
            notifier = self._setup_notifier()
            
            await run_agent(
                state,
                self.phases["preprocess"],
                self.phases["reason"],
                self.phases["act"],
                self.phases["respond"],
                notifier,
            )
            self.last_state = state
            
            # Extract response
            response = getattr(state, "response", None)
            
            # Learn from response
            if self.memory and response:
                await self.memory.remember(response, human=False)
            
            return response or "No response generated"
            
        except Exception as e:
            import traceback
            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            print(error_msg)
            raise e
    
    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution."""
        # Input validation
        error = validate_query(query)
        if error:
            yield f"{error}\n"
            return
        
        # Get or create state
        state = await get_state(
            user_id,
            query,
            self.depth,
            self.user_states,
            self.config.persist,
        )
        
        state.add_message("user", query)
        
        # Memory operations
        if self.memory:
            await self.memory.load()
            await self.memory.remember(query, human=True)
        
        # Setup streaming
        queue: asyncio.Queue[str] = asyncio.Queue()
        
        async def stream_callback(notification) -> None:
            formatted = self.formatter.format(notification)
            if formatted:
                await queue.put(formatted)
        
        notifier = self._setup_notifier(callback=stream_callback)
        
        # Execute
        from cogency.execution import run_agent
        
        task = asyncio.create_task(
            run_agent(
                state,
                self.phases["preprocess"],
                self.phases["reason"],
                self.phases["act"],
                self.phases["respond"],
                notifier,
            )
        )
        
        # Stream results
        try:
            while not task.done():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield message
                except asyncio.TimeoutError:
                    continue
            
            # Drain remaining
            while not queue.empty():
                yield queue.get_nowait()
                
        finally:
            result = await task
            self.last_state = result
            
            # Learn from response
            if self.memory and result and hasattr(result, "response"):
                await self.memory.remember(result.response, human=False)
    
    def traces(self) -> list[dict[str, Any]]:
        """Get execution traces (debug mode only)."""
        if not self.debug:
            return []
        
        return [
            {"type": n.type, "timestamp": n.timestamp, **n.data}
            for n in self.notifier.notifications
        ]
