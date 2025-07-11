from typing import TypedDict, Optional, Tuple, Any, Dict
from cogency.context import Context
from abc import ABC, abstractmethod

class AgentState(TypedDict):
    context: Context
    tool_called: bool

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        pass