from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)

class MultiToolCall(BaseModel):
    calls: List[ToolCall]

class Plan(BaseModel):
    action: str
    answer: Optional[str] = None
    tool_call: Optional[Union[ToolCall, MultiToolCall]] = None
