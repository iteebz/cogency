import json
from typing import Any, Dict, Optional, Tuple, List, Union
from pydantic import ValidationError
from cogency.schemas import ToolCall, MultiToolCall, Plan

def parse_plan(response: str) -> Optional[Dict[str, Any]]:
    """Parse plan node JSON response - PURE PARSING ONLY."""
    try:
        data = json.loads(response)
        plan = Plan.model_validate(data)
        return plan.model_dump()
    except (json.JSONDecodeError, ValidationError):
        return None

def parse_reflect(response: str) -> Optional[Dict[str, Any]]:
    """Parse reflect node JSON response - PURE PARSING ONLY."""
    try:
        data = json.loads(response)
        return data
    except json.JSONDecodeError:
        return None