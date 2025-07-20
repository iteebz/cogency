"""Robust JSON extraction from LLM responses."""
import json
import re
from typing import Dict, Any, Optional


def extract_json(response: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract JSON from LLM response with markdown cleaning and error handling.
    
    Handles:
    - Markdown code fences (```json and ```)
    - Proper brace matching for JSON objects
    - Graceful fallback on parsing errors
    
    Args:
        response: Raw LLM response string
        fallback: Default dict to return on parsing errors
        
    Returns:
        Parsed JSON dict or fallback
    """
    if not response or not isinstance(response, str):
        return fallback or {}
    
    # Clean and extract JSON text
    json_text = _clean_json_response(response.strip())
    if not json_text:
        return fallback or {}
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return fallback or {}


def _clean_json_response(response: str) -> str:
    """Extract JSON from markdown code blocks with brace matching."""
    # Remove markdown code fences
    if response.startswith("```json"):
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1).strip()
    elif response.startswith("```"):
        json_match = re.search(r'```\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1).strip()
    
    # Extract JSON object with proper brace matching
    return _extract_json_object(response)


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