"""JSON response parsing utilities for ReAct loop."""
import json
import re
from typing import Optional


class ReactResponseParser:
    """Utilities for parsing LLM responses in ReAct format."""
    
    @staticmethod
    def _clean_json_response(response: str) -> str:
        """Extract JSON from markdown code blocks or return cleaned response."""
        response_cleaned = response.strip()
        
        if response_cleaned.startswith("```json"):
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
        elif response_cleaned.startswith("```"):
            json_match = re.search(r'```\s*\n?(.*?)\n?```', response_cleaned, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
        
        return response_cleaned
    
    @staticmethod
    def can_answer_directly(response: str) -> bool:
        """Check if LLM response indicates it can answer directly."""
        try:
            cleaned = ReactResponseParser._clean_json_response(response)
            data = json.loads(cleaned)
            return data.get("action") == "respond"
        except (json.JSONDecodeError, KeyError):
            return False

    @staticmethod
    def extract_answer(response: str) -> str:
        """Extract direct answer from LLM response."""
        try:
            cleaned = ReactResponseParser._clean_json_response(response)
            data = json.loads(cleaned)
            return data.get("answer", "")
        except (json.JSONDecodeError, KeyError):
            return ""

    @staticmethod
    def extract_tool_calls(response: str) -> Optional[str]:
        """Extract tool calls from LLM response for parsing."""
        try:
            cleaned = ReactResponseParser._clean_json_response(response)
            data = json.loads(cleaned)
            if data.get("action") in ["use_tool", "use_tools"]:
                return cleaned
        except (json.JSONDecodeError, KeyError):
            pass
        return None