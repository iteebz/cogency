"""Cognitive flow abstraction - Clean, simple, zero ceremony."""

from typing import Any, Optional

from cogency.memory.backends.base import MemoryBackend


class Flow:
    """Simple flow configuration for agent workflow."""

    def __init__(
        self,
        llm: Any,
        tools: Any,
        memory: Optional[MemoryBackend],
        identity: Optional[str] = None,
        json_schema: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        # Store key attributes for execution
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.identity = identity
        self.json_schema = json_schema
        self.system_prompt = system_prompt
