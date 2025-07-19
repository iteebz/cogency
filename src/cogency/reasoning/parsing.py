"""JSON response parsing utilities for ReAct reasoning."""
import json
import re
from typing import Optional, Tuple

from cogency.constants import ReasoningActions


class ReactResponseParser:
    """Utilities for parsing LLM responses in ReAct format."""
    
    @staticmethod
    def _extract_reasoning_and_json(response: str) -> Tuple[str, str]:
        """Extract reasoning text and JSON decision from LLM response."""
        response_cleaned = response.strip()
        
        # Look for REASONING: section
        reasoning_match = re.search(r'REASONING:\s*(.*?)(?:\n\s*JSON_DECISION:|$)', response_cleaned, re.DOTALL | re.IGNORECASE)
        reasoning_text = ""
        if reasoning_match:
            reasoning_text = reasoning_match.group(1).strip()
            # Clean up any bracketed placeholders
            reasoning_text = re.sub(r'\[.*?\]', '', reasoning_text).strip()
        
        # Extract JSON from various formats
        json_text = ""
        
        # First try to find JSON_DECISION: section
        json_match = re.search(r'JSON_DECISION:\s*(.*)', response_cleaned, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_section = json_match.group(1).strip()
            # Look for actual JSON in this section with proper brace matching
            json_text = ReactResponseParser._extract_json_object(json_section)
            if json_text and json_text != json_section:
                # Only use if we actually found a JSON object
                pass
            else:
                json_text = ""
        
        # Fallback: look for any JSON in the response
        if not json_text:
            json_text = ReactResponseParser._clean_json_response(response_cleaned)
        
        return reasoning_text, json_text
    
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
        
        # Look for JSON object pattern with proper brace matching
        return ReactResponseParser._extract_json_object(response_cleaned)
    
    @staticmethod
    def _extract_json_object(text: str) -> str:
        """Extract JSON object with proper brace matching."""
        start_idx = text.find('{')
        if start_idx == -1:
            return text
        
        brace_count = 0
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx:i+1]
        
        return text
    
    @staticmethod
    def extract_reasoning(response: str) -> str:
        """Extract reasoning text from LLM response."""
        reasoning_text, _ = ReactResponseParser._extract_reasoning_and_json(response)
        return reasoning_text if reasoning_text else "Analyzing situation and deciding next action"
    
    @staticmethod
    def can_answer_directly(response: str) -> bool:
        """Check if LLM response indicates it can answer directly."""
        try:
            _, json_text = ReactResponseParser._extract_reasoning_and_json(response)
            data = json.loads(json_text)
            return data.get("action") == ReasoningActions.RESPOND
        except (json.JSONDecodeError, KeyError):
            return False

    @staticmethod
    def extract_answer(response: str) -> str:
        """Extract direct answer from LLM response."""
        try:
            _, json_text = ReactResponseParser._extract_reasoning_and_json(response)
            data = json.loads(json_text)
            return data.get("answer", "")
        except (json.JSONDecodeError, KeyError):
            return ""

    @staticmethod
    def extract_tool_calls(response: str) -> Optional[list]:
        """Extract tool calls from LLM response as parsed list."""
        try:
            _, json_text = ReactResponseParser._extract_reasoning_and_json(response)
            data = json.loads(json_text)
            if data.get("action") == ReasoningActions.USE_TOOL:
                # Single tool call
                return [data["tool_call"]]
            elif data.get("action") == ReasoningActions.USE_TOOLS:
                # Multiple tool calls
                return data["tool_call"]["calls"]
        except (json.JSONDecodeError, KeyError):
            pass
        return None