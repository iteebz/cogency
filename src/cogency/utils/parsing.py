"""Consolidated parsing utilities - clean extraction from LLM responses."""
import json
import re
from typing import Any, Dict, List, Optional, Union
from cogency.utils.json import extract_json


async def call_llm_simple(llm, messages: List[Dict[str, str]]) -> str:
    """Call LLM and return response. That's it."""
    return await llm.run(messages)


def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response. Return None if no valid JSON."""
    return extract_json(response)


def extract_tool_calls_from_json(json_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Extract tool calls from parsed JSON. Return None if no tool calls."""
    if not json_data:
        return None
        
    # New format: direct tool_calls array
    if "tool_calls" in json_data:
        return json_data.get("tool_calls", [])
    
    # Legacy format support
    action = json_data.get("action")
    if action == "use_tools":
        return json_data.get("tool_calls", [])
    return None




# Removed should_respond_directly - ceremony eliminated. Direct response is implicit when no tool_calls.


def extract_reasoning_text(response: str) -> str:
    """Extract reasoning text from LLM response."""
    # First try JSON
    json_data = extract_json_from_response(response)
    if json_data and "reasoning" in json_data:
        return json_data["reasoning"]
    
    # Try text-based REASONING: pattern
    reasoning_match = re.search(r'REASONING:\s*(.+?)(?=\nJSON_DECISION:|$)', response, re.DOTALL | re.IGNORECASE)
    if reasoning_match:
        return reasoning_match.group(1).strip()
    
    return "Analyzing the request and determining the best approach"