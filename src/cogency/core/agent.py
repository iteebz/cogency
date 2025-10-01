"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent(llm="openai")
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

from .. import context
from ..lib import llms
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
        base_dir: str | None = None,
        *,
        identity: str | None = None,
        instructions: str | None = None,
        tools: list[Tool] | None = None,
        mode: str = "auto",
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
            llm: An LLM instance or a string identifier (e.g., "openai", "gemini").
            storage: A Storage implementation. Defaults to local file-based storage.
            base_dir: The base directory for all file operations and storage.
            identity: Core agent identity (who you are). Overrides default Cogency identity.
            instructions: Additional instructions to steer the agent's behavior.
            tools: A list of Tool instances. Defaults to a standard set.
            mode: Coordination mode ("auto", "resume", "replay"). Defaults to "auto".
            max_iterations: Maximum number of execution iterations.
            history_window: Number of historical messages to include in context.
            profile: Enable automatic profile learning. Defaults to True.
            learn_every: Cadence for triggering profile learning.
            scrape_limit: Character limit for web scraping tools.
            security: A Security object defining access levels and timeouts.
            debug: Enable verbose debug logging.
        """
        if debug:
            from ..lib.logger import set_debug

            set_debug(True)

        final_security = security or Security()
        final_storage = storage or default_storage(base_dir=base_dir)
        final_tools = default_tools() if tools is None else tools
        final_llm = llms.create(llm) if isinstance(llm, str) else llm

        self.config = Config(
            llm=final_llm,
            storage=final_storage,
            tools=final_tools,
            base_dir=base_dir,
            identity=identity,
            instructions=instructions,
            mode=mode,
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

    async def __call__(
        self,
        query: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        chunks: bool = False,
    ):
        """Stream events for query.

        Args:
            query: User query
            user_id: User identifier (None = no profile)
            conversation_id: Conversation identifier (None = stateless/ephemeral)
            chunks: If True, stream individual tokens. If False, stream semantic events.
        """
        try:
            # Persist user message for conversation context (if conversation_id provided)
            storage = self.config.storage
            if conversation_id:
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
