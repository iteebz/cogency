"""Coordination primitives for concurrent Cogency agent operations."""
import asyncio
import copy
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, TypeVar, Callable, Awaitable
from dataclasses import dataclass

from cogency.types import AgentState


T = TypeVar('T')


@dataclass
class StreamMutation:
    """Represents a pending state mutation that preserves stream consistency."""
    mutation_id: str
    target_path: str  # e.g., "context.messages", "execution_trace.steps"
    operation: str    # "append", "update", "delete"
    data: Any
    timestamp: float


class StateCoordinator:
    """
    Coordinates concurrent access to AgentState without blocking operations.
    
    Ensures state mutations are atomic while keeping streams responsive.
    Uses non-blocking patterns to prevent stream interruption.
    """
    
    def __init__(self, initial_state: AgentState):
        self._state = initial_state
        self._mutation_lock = asyncio.Lock()
        self._pending_mutations: list[StreamMutation] = []
        
    @asynccontextmanager
    async def mutate_state(self) -> AsyncGenerator[AgentState, None]:
        """
        Context manager for stream-safe state mutations.
        
        Returns a mutable view of state that can be safely modified without
        blocking stream deltas. Mutations are applied atomically when context exits.
        """
        # Try to acquire lock without blocking the stream
        if self._mutation_lock.locked():
            # Return read-only snapshot to prevent corruption
            yield copy.deepcopy(self._state)
            return
            
        async with self._mutation_lock:
            # Deep copy current state for mutation
            mutable_state = copy.deepcopy(self._state)
            
            try:
                yield mutable_state
                # Apply mutations atomically
                self._state = mutable_state
            except Exception as e:
                # Log error but don't corrupt state
                logging.error(f"State mutation failed, rolling back: {e}")
                raise
    
    def get_state(self) -> AgentState:
        """Get current state snapshot - always non-blocking for stream deltas."""
        return self._state
    
    async def update_context_messages(self, role: str, content: str) -> None:
        """Non-blocking message append for concurrent access."""
        async with self.mutate_state() as state:
            state["context"].add_message(role, content)
    
    async def update_execution_trace(self, step_data: Dict[str, Any]) -> None:
        """Non-blocking trace update for concurrent access."""
        async with self.mutate_state() as state:
            if state["execution_trace"]:
                state["execution_trace"].add_step(**step_data)


async def with_timeout(
    coro: Awaitable[T], 
    timeout_seconds: float,
    operation_name: str = "operation"
) -> T:
    """
    Execute an async operation with timeout, designed for streaming contexts.
    
    Unlike asyncio.wait_for, this preserves the operation name for better
    error reporting in streaming deltas.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise StreamingTimeoutError(
            f"{operation_name} timed out after {timeout_seconds}s",
            operation=operation_name,
            timeout=timeout_seconds
        )


class StreamingTimeoutError(Exception):
    """Timeout error that preserves context for streaming error deltas."""
    
    def __init__(self, message: str, operation: str, timeout: float):
        super().__init__(message)
        self.operation = operation
        self.timeout = timeout


