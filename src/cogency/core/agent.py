"""Agent interface with dual API: Result patterns or streaming events.

Usage:
  agent = Agent()              # Configuration closure
  result = await agent(query)  # Returns Result[str] - no exceptions at boundary
  async for event in agent.stream(query):  # Raw event stream with error events
"""

from ..context import context
from ..lib.logger import logger
from ..lib.storage import SQLite
from ..tools import TOOLS
from .config import Config
from .protocols import LLM, Event, Mode, Storage
from .stream import stream


class Agent:
    """Agent as configuration closure - stateless execution."""

    def __init__(
        self,
        llm: str | LLM = "gemini",
        storage: Storage | None = None,
        tools: list | None = None,
        instructions: str | None = None,
        mode: str = "auto",
        max_iterations: int = 3,
        profile: bool = True,
        sandbox: bool = True,
    ):
        # Build internal config from parameters - single source of truth
        # Agent(llm="gemini") is better DX than Agent(Config(llm="gemini"))
        # Config is internal data structure, not user-facing API
        self.config = Config(
            llm=self._create_llm(llm),
            storage=storage or SQLite(),
            tools=tools if tools is not None else TOOLS,
            instructions=instructions,
            mode=mode,
            max_iterations=max_iterations,
            profile=profile,
            sandbox=sandbox,
        )

        # Validate mode during construction
        try:
            Mode(mode)
        except ValueError:
            valid_modes = [m.value for m in Mode]
            raise ValueError(f"mode must be one of {valid_modes}, got: {mode}") from None

        # Stateless - agent is pure function with configuration closure

    def _create_llm(self, llm) -> LLM:
        """Create LLM instance from string or pass through existing instance."""
        # If already an LLM instance, use it
        from .protocols import LLM

        if isinstance(llm, LLM):
            return llm

        # String → built-in LLM
        if llm == "gemini":
            from ..lib.llms import Gemini

            return Gemini()
        if llm == "openai":
            from ..lib.llms import OpenAI

            return OpenAI()
        if llm == "anthropic":
            from ..lib.llms import Anthropic

            return Anthropic()

        valid = ["openai", "gemini", "anthropic"]
        raise ValueError(f"Unknown LLM '{llm}'. Valid options: {', '.join(valid)}")

    def _conversation_id(self, user_id: str, conversation_id: str | None) -> str:
        """Get or generate conversation ID."""
        return conversation_id or f"{user_id}_session"

    async def __call__(
        self, query: str, user_id: str = "default", conversation_id: str | None = None
    ) -> str:
        conversation_id = self._conversation_id(user_id, conversation_id)

        try:
            # Collect all streaming events
            respond_events = []
            async for event in stream(
                self.config,
                query,
                user_id,
                conversation_id,
                on_complete=context.record,
                on_learn=context.learn,
            ):
                if event["type"] == Event.RESPOND:
                    respond_events.append(event["content"])

            # Aggregate response events
            response = "".join(respond_events).strip()
            if not response:
                raise RuntimeError("Agent produced no response")
            return response
        except Exception as e:
            logger.debug(f"Failed: {e}")
            # Convert specific errors to helpful messages
            error_msg = str(e)
            if "Agent produced no response" in error_msg:
                logger.debug("Agent produced no response - likely API key or configuration issue")
                raise RuntimeError(
                    "Agent execution failed - check API keys and configuration"
                ) from None
            if "LLM connection failed" in error_msg:
                raise RuntimeError(
                    "LLM connection failed - check API keys and configuration"
                ) from None
            raise RuntimeError(
                "Agent execution failed"
            ) from None  # [SEC-003] No error chain leakage

    async def stream(
        self, query: str, user_id: str = "default", conversation_id: str | None = None
    ):
        conversation_id = self._conversation_id(user_id, conversation_id)

        try:
            async for event in stream(
                self.config,
                query,
                user_id,
                conversation_id,
                on_complete=context.record,
                on_learn=context.learn,
            ):
                yield event
        except Exception as e:
            logger.debug(f"Stream failed: {e}")
            # Convert connection errors to helpful messages
            if "LLM connection failed" in str(e):
                raise RuntimeError(
                    "LLM connection failed - check API keys and configuration"
                ) from None
            raise RuntimeError("Stream failed") from None  # [SEC-003] No error chain leakage
