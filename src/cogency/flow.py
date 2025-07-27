"""Cognitive flow abstraction."""

from typing import Any, Optional

from langgraph.graph import END, StateGraph

from cogency.memory.backends.base import MemoryBackend
from cogency.nodes.act import Act
from cogency.nodes.preprocess import Preprocess
from cogency.nodes.reason import Reason
from cogency.nodes.respond import Respond
from cogency.state import State


class Flow:
    """LangGraph wrapper for agent workflow."""

    def __init__(
        self,
        llm: Any,
        tools: Any,
        memory: Optional[MemoryBackend],
        identity: Optional[str] = None,
        json_schema: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        # Store key attributes for test access
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.identity = identity
        self.json_schema = json_schema
        self.system_prompt = system_prompt

        self.common_kwargs = {
            "llm": llm,
            "tools": tools,
            "system_prompt": system_prompt or "",
            "identity": identity,
        }
        self.flow = self._build(memory, json_schema)

    def _build(self, memory: Optional[MemoryBackend], json_schema: Optional[str]) -> Any:
        """Build flow graph with self-routing nodes."""
        nodes = {
            "preprocess": Preprocess(memory=memory, **self.common_kwargs),
            "reason": Reason(**self.common_kwargs),
            "act": Act(tools=self.common_kwargs["tools"]),
            "respond": Respond(json_schema=json_schema, **self.common_kwargs),
        }

        flow = StateGraph(State)

        for name, node in nodes.items():
            flow.add_node(name, node)

        flow.set_entry_point("preprocess")

        # All nodes self-route except respond which ends
        for name, node in nodes.items():
            if hasattr(node, "next_node") and callable(node.next_node):
                if name == "respond":
                    flow.add_edge(name, END)
                else:
                    flow.add_conditional_edges(name, node.next_node)

        return flow.compile()
