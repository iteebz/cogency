import asyncio
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Union

from cogency import decorators
from cogency.config import Observe, Persist, Robust, setup_config
from cogency.mcp import setup_mcp
from cogency.memory.store import Store, setup_memory
from cogency.persist.utils import get_state
from cogency.phases import setup_phases
from cogency.services import LLM, Embed, setup_embed, setup_llm
from cogency.state import State
from cogency.tools import Tool, setup_tools
from cogency.utils import Notifier, validate_query


class Agent:
    """Cognitive agent with streaming execution, tool integration, memory and adaptive reasoning"""

    def __init__(
        self,
        name: str = "cogency",
        *,  # Force keyword-only arguments
        # Backend Systems (things with constructors)
        llm: Optional[LLM] = None,
        embed: Optional[Embed] = None,
        tools: Optional[List[Tool]] = None,
        memory: Optional[Store] = None,
        # Agent Personality
        identity: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        # Execution Control
        mode: Literal["fast", "deep", "adapt"] = "adapt",
        depth: int = 10,
        # User Feedback
        notify: bool = True,
        debug: bool = False,
        # System Behaviors (@phase decorator control)
        robust: Union[bool, Robust] = True,
        observe: Union[bool, Observe] = False,
        persist: Union[bool, Persist] = False,
        # Integrations
        mcp: bool = False,
    ) -> None:
        self.name = name
        self.debug = debug
        self.notify = notify
        self.depth = depth

        # Mode - direct assignment, no ceremony
        self.mode = mode

        # Setup services with auto-detection
        self.llm = setup_llm(llm)
        self.embed = setup_embed(embed)
        self.memory = setup_memory(memory)
        self.tools = setup_tools(tools, self.memory)

        # Config setup with auto-detection
        self.config = type(
            "Config",
            (),
            {
                "robust": setup_config(Robust, robust),
                "observe": setup_config(Observe, observe),
                "persist": setup_config(Persist, persist, store=persist),
            },
        )()

        # Configure decorators
        decorators.configure(
            robust=self.config.robust,
            observe=self.config.observe,
            persistence=self.config.persist,
        )

        # Agent personality
        self.identity = identity or ""
        self.output_schema = output_schema

        # State management
        self.user_states: dict[str, State] = {}
        self.last_state: Optional[dict] = None  # Store for traces()

        # Setup phases with zero ceremony
        self.phases = setup_phases(
            self.llm,
            self.tools,
            self.memory,
            self.identity,
            self.output_schema,
        )

        # Setup MCP server
        self.mcp_server = setup_mcp(self, mcp)

    def _notify_cb(self, state: State):
        """Create notification callback for phases."""

        def notify(event_type: str, message: str):
            asyncio.create_task(self._handle_notification(event_type, message, state))

        return notify

    async def _handle_notification(self, event_type: str, message: str, state: State) -> None:
        """Handle notification with proper separation of concerns."""
        if state.callback and state.notify:
            await state.callback(message)

        # Store notification for debugging
        state.notifications.append(
            {"event_type": event_type, "message": message, "iteration": state.iteration}
        )

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution"""
        # Input validation
        error = validate_query(query)
        if error:
            yield f"{error}\n"
            return

        # Get or create state with persistence support
        state = await get_state(
            user_id,
            query,
            self.depth,
            self.user_states,
            self.config.persist,
        )

        state.add_message("user", query)

        # Stream execution using Notifier
        notifier = Notifier(
            state=state,
            phases=self.phases,
            trace=self.debug,
            verbose=self.notify,
        )

        async for chunk in notifier.notify():
            yield chunk

        # Store state for traces()
        self.last_state = notifier.get_notifications()

    async def run(self, query: str, user_id: str = "default") -> str:
        """Run agent and return complete response as string (async)"""
        try:
            # Get or create state with persistence support
            state = await get_state(
                user_id,
                query,
                self.depth,
                self.user_states,
                self.config.persist,
            )
            state.notify = self.notify
            state.debug = self.debug

            # Set agent mode - direct, no ceremony
            state.agent_mode = self.mode
            if self.mode != "adapt":
                state.mode = self.mode

            # Set up trace callback for non-streaming mode
            if self.debug:
                state.callback = print

            # Use simple execution loop with zero ceremony
            from cogency.execution import run_agent

            # Create notify callback
            notify = self._notify_cb(state)

            # Phase instances already have dependencies injected
            await run_agent(
                state,
                self.phases["preprocess"],
                self.phases["reason"],
                self.phases["act"],
                self.phases["respond"],
                notify,
            )
            self.last_state = state

            # Extract response from state
            response = getattr(state, "response", None)
            return response or "No response generated"

        except Exception as e:
            # Make errors EXPLICIT
            import traceback

            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return f"ERROR: {e}"

    def traces(self) -> list[dict[str, Any]]:
        """Get traces from last execution for debugging"""
        if self.last_state:
            return self.last_state
        return []


__all__ = ["Agent", "State"]
