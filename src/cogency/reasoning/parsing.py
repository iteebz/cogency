"""JSON response parsing utilities for ReAct reasoning."""
import json
import re
from typing import Optional, Tuple

from cogency.constants import ReasoningActions
from cogency.utils.json import extract_json


class ReactResponseParser:
    """Utilities for parsing LLM responses in ReAct format."""
    
    @staticmethod
    def _extract_reasoning_and_json(response: str) -> Tuple[str, str]:
        """Extract reasoning text and JSON decision from LLM response."""
        response_cleaned = response.strip()
        
        # Extract JSON from response using central utility
        parsed_data = extract_json(response_cleaned)
        reasoning_text = ""
        json_text = ""
        
        if parsed_data:
            # Extract reasoning from JSON field
            reasoning_text = parsed_data.get("reasoning", "")
            json_text = json.dumps(parsed_data)
        else:
            # Fallback: try to find any JSON structure
            json_match = re.search(r'\{.*\}', response_cleaned, re.DOTALL)
            if json_match:
                json_section = json_match.group(0)
                parsed_fallback = extract_json(json_section)
                if parsed_fallback:
                    reasoning_text = parsed_fallback.get("reasoning", "")
                    json_text = json.dumps(parsed_fallback)
        
        return reasoning_text, json_text
    
    
    @staticmethod
    def extract_reasoning(response: str) -> str:
        """Extract reasoning text from LLM response."""
        reasoning_text, _ = ReactResponseParser._extract_reasoning_and_json(response)
        if reasoning_text and reasoning_text.strip():
            return reasoning_text.strip()
        
        # Ultimate fallback: show that we're analyzing the request  
        return "Analyzing the request and determining the best approach"
    
    @staticmethod
    def can_answer_directly(response: str) -> bool:
        """Check if LLM response indicates it can answer directly."""
        try:
            _, json_text = ReactResponseParser._extract_reasoning_and_json(response)
            data = extract_json(json_text)
            return data.get("action") == ReasoningActions.RESPOND
        except KeyError:
            return False


    @staticmethod
    def extract_tool_calls(response: str) -> Optional[list]:
        """Extract tool calls from LLM response as parsed list."""
        try:
            _, json_text = ReactResponseParser._extract_reasoning_and_json(response)
            data = extract_json(json_text)
            if data.get("action") == ReasoningActions.USE_TOOL:
                # Single tool call
                return [data["tool_call"]]
            elif data.get("action") == ReasoningActions.USE_TOOLS:
                # Multiple tool calls
                return data["tool_call"]["calls"]
        except KeyError:
            pass
        return None