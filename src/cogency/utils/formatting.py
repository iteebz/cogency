"""Centralized formatting utilities for consistent display across Cogency.

This module contains pure formatting functions that transform data into 
human-readable text, independent of output channels or presentation concerns.
"""
from typing import Any, Dict, List, Optional, Union


def truncate(text: str, max_len: int = 30) -> str:
    """Smart truncation preserving meaning.
    
    Args:
        text: Text to truncate
        max_len: Maximum length
        
    Returns:
        Truncated text
    """
    if not text or not isinstance(text, str):
        return ""
        
    if len(text) <= max_len:
        return text
    
    # URLs: preserve domain
    if text.startswith(('http://', 'https://')):
        try:
            from urllib.parse import urlparse
            domain = urlparse(text).netloc
            return f"{domain}/..." if len(domain) <= max_len - 4 else f"{domain[:max_len-3]}..."
        except Exception:
            pass
    
    # Paths: preserve filename
    if '/' in text:
        filename = text.split('/')[-1]
        if len(filename) <= max_len - 4:
            return f".../{filename}"
    
    # Words: break at boundaries
    if ' ' in text:
        words = text.split()
        result = words[0]
        for word in words[1:]:
            if len(result + word) + 4 <= max_len:
                result += f" {word}"
            else:
                return f"{result}..."
        return result
    
    return f"{text[:max_len-3]}..."


def format_tool_params(params: Dict[str, Any]) -> str:
    """Format tool parameters for display.
    
    Args:
        params: Tool parameters
        
    Returns:
        Formatted parameter string
    """
    if not params:
        return ""
    
    # Simple formatting: first value only
    first_val = list(params.values())[0] if params.values() else ""
    return f"({truncate(str(first_val), 25)})" if first_val else ""


def format_tool_result(result: Any) -> str:
    """Extract meaningful info from results for display.
    
    Args:
        result: Tool execution result
        
    Returns:
        Formatted result string
    """
    if result is None:
        return "completed"
    
    try:
        if isinstance(result, dict):
            # Check for common success/error patterns
            if "error" in result:
                return f"✗ {truncate(str(result['error']), 40)}"
            
            # Standard result patterns
            for key in ["result", "summary", "data", "content", "message"]:
                if key in result:
                    return truncate(str(result[key]), 50)
            
            # Success indicators
            if result.get("success") is True:
                return "✓ success"
            elif result.get("success") is False:
                return "✗ failed"
        
        elif isinstance(result, (list, tuple)):
            return f"{len(result)} items" if len(result) > 1 else "empty" if len(result) == 0 else str(result[0])
        
        elif isinstance(result, bool):
            return "✓ success" if result else "✗ failed"
        
        return truncate(str(result), 60)
    except Exception:
        return "completed"
