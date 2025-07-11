from typing import TypedDict, Optional, Tuple, Any, Dict
from cogency.context import Context
from abc import ABC, abstractmethod

class AgentState(TypedDict):
    context: Context
    tool_called: bool
    tool_needed: bool
    task_complete: bool
    last_node: Optional[str]

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        pass