"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent(llm="openai")
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

from .. import context
from ..context.constants import DEFAULT_USER_ID
from ..lib.storage import default_storage
from ..tools import tools as default_tools
from . import replay, resume
from .config import Config, Security
from .exceptions import AgentError
from .protocols import LLM, Storage, Tool


class Agent:
    """Agent with a clear, explicit, and immutable configuration.

    The Agent is the primary interface for interacting with the Cogency framework.
    Its constructor is the single point of configuration, providing a self-documenting
    and type-safe way to set up agent behavior.

    Usage:
      agent = Agent(llm="openai", storage=default_storage())
      async for event in agent("What is the capital of France?"):
          print(event)
    """

    def __init__(
        self,
        llm: str | LLM,
        storage: Storage | None = None,
        *,
        tools: list[Tool] | None = None,
        mode: str = "auto",
        instructions: str | None = None,
        max_iterations: int = 10,
        history_window: int = 20,
        profile: bool = True,
        learn_every: int = 5,
        scrape_limit: int = 3000,
        security: Security | None = None,
        debug: bool = False,
    ):
        """Initializes the Agent with an explicit configuration.

        Args:
            llm: An LLM instance or a string identifier ("openai", "gemini", "anthropic").
            storage: A Storage implementation. Defaults to a local file-based storage.
            tools: A list of Tool instances. If None, a default set of file management
                tools is provided based on the security access level.
            mode: Coordination mode ("auto", "resume", "replay"). Defaults to "auto".
            instructions: High-level instructions to steer the agent's behavior.
            max_iterations: Maximum number of execution iterations to prevent runaways.
            history_window: Number of historical messages to include in the context.
            profile: Enable automatic profile learning. Defaults to True.
            learn_every: Cadence (in number of messages) for triggering profile learning.
            scrape_limit: Character limit for web scraping tools.
            security: A Security object defining access levels and timeouts.
                Defaults to a sandbox environment.
            debug: Enable verbose debug logging.
        """
        if debug:
            from ..lib.logger import set_debug

            set_debug(True)

        final_security = security or Security()
        final_storage = storage or default_storage()

        if tools is None:
            from ..tools import FileEdit, FileList, FileRead, FileSearch, FileWrite

            access = final_security.access
            file_tools = [
                FileRead(access=access),
                FileWrite(access=access),
                FileEdit(access=access),
                FileList(access=access),
                FileSearch(access=access),
            ]
            other_tools = [
                tool
                for tool in default_tools()
                if not isinstance(tool, (FileRead, FileWrite, FileEdit, FileList, FileSearch))
            ]
            final_tools = file_tools + other_tools
        else:
            final_tools = tools

        # The internal Config object is now a private implementation detail,
        # assembled from the clear, explicit arguments of this constructor.
        self.config = Config(
            llm=self._create_llm(llm),
            storage=final_storage,
            tools=final_tools,
            mode=mode,
            instructions=instructions,
            max_iterations=max_iterations,
            history_window=history_window,
            profile=profile,
            learn_every=learn_every,
            scrape_limit=scrape_limit,
            security=final_security,
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
