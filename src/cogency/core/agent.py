"""Agent: Pure interface to ReAct algorithm."""

import time
from dataclasses import dataclass

from ..lib.providers import create_embedder, create_llm
from ..tools import BASIC_TOOLS
from .react import react, stream_react


@dataclass
class AgentResult:
    """Agent execution result with response and conversation continuity."""

    response: str
    conversation_id: str


class Agent:
    """Pure interface to ReAct algorithm."""

    def __init__(self, llm="gemini", embedder=None, tools=None, max_iterations=5, debug=None):
        """Initialize agent with explicit configuration.

        Args:
            llm: LLM provider ("openai", "gemini", "anthropic") or provider instance
            embedder: Embedder provider or instance (optional)
            tools: List of tools (defaults to BASIC_TOOLS)
            max_iterations: Maximum reasoning iterations
            debug: Observability config (True=console, str=file_path, False/None=off)
        """
        self.llm = create_llm(llm) if isinstance(llm, str) else llm
        self.embedder = (
            create_embedder(embedder) if embedder and isinstance(embedder, str) else embedder
        )
        self.tools = {t.name: t for t in (tools if tools is not None else BASIC_TOOLS)}
        self.max_iterations = max_iterations
        self._setup_logging(debug)

    def _setup_logging(self, debug):
        """Setup logging like requests - standard library approach."""
        import logging

        if debug is True:
            # Console debug
            logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s", force=True)
        elif isinstance(debug, str):
            # File debug
            logging.basicConfig(
                level=logging.DEBUG,
                filename=debug,
                format="%(asctime)s %(name)s: %(message)s",
                force=True,
            )

    async def __call__(
        self, query: str, *, user_id: str = None, conversation_id: str = None, memory: bool = True
    ) -> AgentResult:
        """Sacred interface with optional memory multitenancy and conversation continuity."""
        import logging

        logger = logging.getLogger("cogency")

        if user_id is None:
            user_id = "default"

        start_time = time.time()
        logger.info(f"Processing: {query[:60]}{'...' if len(query) > 60 else ''}")

        final_event = await react(
            self.llm,
            self.tools,
            query,
            user_id,
            self.max_iterations,
            conversation_id,
            memory=memory,
            embedder=self.embedder,
        )

        duration = time.time() - start_time

        if final_event["type"] == "error":
            logger.error(f"Failed: {final_event['message']}")
            return AgentResult(
                response=f"LLM Error: {final_event['message']}",
                conversation_id=f"{user_id}_{int(time.time())}",
            )

        logger.info(f"Completed in {duration:.1f}s")
        return AgentResult(
            response=final_event["answer"], conversation_id=final_event["conversation_id"]
        )

    async def stream(
        self, query: str, *, user_id: str = None, conversation_id: str = None, memory: bool = True
    ):
        """Stream ReAct reasoning states as structured events.

        Yields structured events for each ReAct loop iteration:
        - iteration: Loop iteration number
        - context: Context assembly completion
        - reasoning: LLM response content
        - tool: Tool execution results
        - complete: Final answer with conversation_id
        - error: Failure states

        Usage:
            async for event in agent.stream("Complex task"):
                if event["type"] == "reasoning":
                    print(f"Thinking: {event['content'][:100]}...")
        """
        if user_id is None:
            user_id = "default"

        async for event in stream_react(
            self.llm,
            self.tools,
            query,
            user_id,
            self.max_iterations,
            conversation_id,
            task_id=None,
            memory=memory,
            embedder=self.embedder,
        ):
            yield event
