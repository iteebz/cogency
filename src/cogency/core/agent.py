"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent()
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

from .. import context
from ..context.constants import DEFAULT_USER_ID
from ..lib.storage import default_storage
from ..tools import tools as default_tools
from . import replay, resume
from .config import Config
from .exceptions import AgentError
from .protocols import LLM, Tool


class Agent:
    """Agent with immutable configuration and fresh context assembly per call.

    Parameters
    ----------
    llm:
        Provider identifier (``"openai"`` by default) or an ``LLM`` implementation.
    mode:
        Coordination mode (``"auto"`` | ``"resume"`` | ``"replay"``). Defaults to ``"auto"``.
    tools:
        A list of `Tool` instances. Defaults to all auto-discovered tools if not provided.
    storage:
        ``Storage`` implementation used for conversation history.
    profile:
        Enable automatic profile learning for long-lived conversations. Enabled by default.

    Additional keyword arguments are forwarded to :class:`cogency.core.config.Config`.
    """

    def __init__(self, llm: str | LLM = "openai", tools: list[Tool] | None = None, **kwargs):
        if kwargs.pop("debug", False):
            from ..lib.logger import set_debug

            set_debug(True)

        # Handle access parameter
        access = kwargs.pop("access", None)
        if access is not None:
            from .config import Security

            kwargs["security"] = Security(access=access)

        # Set the tools for the agent's configuration.
        if tools is None:
            from ..tools import FileEdit, FileList, FileRead, FileSearch, FileWrite

            # Get access level from config or default
            tool_access = access or "sandbox"

            # Create tools with appropriate access level
            file_tools = [
                FileRead(access=tool_access),
                FileWrite(access=tool_access),
                FileEdit(access=tool_access),
                FileList(access=tool_access),
                FileSearch(access=tool_access),
            ]

            # Get non-file tools from registry
            other_tools = [
                tool
                for tool in default_tools()
                if not isinstance(tool, (FileRead, FileWrite, FileEdit, FileList, FileSearch))
            ]

            kwargs["tools"] = file_tools + other_tools
        else:
            kwargs["tools"] = tools

        if "storage" not in kwargs:
            kwargs["storage"] = default_storage()

        self.config = Config(
            llm=self._create_llm(llm),
            **kwargs,  # All fields pass through to Config
        )

        # Validate mode during construction
        valid_modes = ["auto", "resume", "replay"]
        if self.config.mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got: {self.config.mode}")

    def _create_llm(self, llm) -> LLM:
        """Create LLM instance from string or pass through existing instance."""
        from .protocols import LLM

        if isinstance(llm, LLM):
            return llm

        # Dictionary dispatch for LLM creation
        llm_factories = {
            "gemini": lambda: __import__("cogency.lib.llms", fromlist=["Gemini"]).Gemini(),
            "openai": lambda: __import__("cogency.lib.llms", fromlist=["OpenAI"]).OpenAI(),
            "anthropic": lambda: __import__("cogency.lib.llms", fromlist=["Anthropic"]).Anthropic(),
        }

        if llm not in llm_factories:
            valid = list(llm_factories.keys())
            raise ValueError(f"Unknown LLM '{llm}'. Valid options: {', '.join(valid)}")

        return llm_factories[llm]()

    async def __call__(
        self,
        query: str,
        user_id: str = DEFAULT_USER_ID,
        conversation_id: str | None = None,
        chunks: bool = False,
    ):
        """Stream events for query.

        Args:
            query: User query
            user_id: User identifier
            conversation_id: Conversation identifier
            chunks: If True, stream individual tokens. If False, stream semantic events.
        """
        conversation_id = conversation_id or user_id

        try:
            # Persist user message for conversation context
            storage = self.config.storage
            await storage.save_message(conversation_id, user_id, "user", query)

            if self.config.mode == "resume":
                mode_stream = resume.stream
            elif self.config.mode == "auto":
                # Try resume first, fall back to replay on failure
                try:
                    async for event in resume.stream(
                        query,
                        user_id,
                        conversation_id,
                        config=self.config,
                        chunks=chunks,
                    ):
                        yield event
                    # Trigger profile learning if enabled
                    if self.config.profile:
                        context.learn(
                            user_id,
                            profile_enabled=self.config.profile,
                            storage=storage,
                            learn_every=self.config.learn_every,
                            llm=self.config.llm,
                        )
                    return
                except Exception as e:
                    from ..lib.logger import logger

                    logger.debug(f"Resume failed, falling back to replay: {e}")
                    mode_stream = replay.stream
            else:
                mode_stream = replay.stream

            async for event in mode_stream(
                query,
                user_id,
                conversation_id,
                config=self.config,
                chunks=chunks,
            ):
                yield event

            # Trigger profile learning if enabled
            if self.config.profile:
                context.learn(
                    user_id,
                    profile_enabled=self.config.profile,
                    storage=storage,
                    learn_every=self.config.learn_every,
                    llm=self.config.llm,
                )
        except Exception as e:  # pragma: no cover - defensive logging path
            from ..lib.logger import logger

            logger.error(f"Stream execution failed: {type(e).__name__}: {e}")
            raise AgentError(
                f"Stream execution failed: {type(e).__name__}", cause=e
            ) from None  # [SEC-003] No error chain leakage
