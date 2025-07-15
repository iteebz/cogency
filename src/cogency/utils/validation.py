"""Tool call validation - single responsibility."""
import json
import re
from typing import List
from cogency.tools.base import BaseTool


def validate_tools(llm_response: str, tools: List[BaseTool]) -> str:
    """Validate and correct tool calls in LLM response."""
    try:
        data = json.loads(llm_response)
        
        if data.get("action") == "tool_needed" and "tool_call" in data:
            tool_call = data["tool_call"]
            valid_tool_names = [tool.name for tool in tools]
            
            # Validate single tool call
            if "SINGLE_TOOL:" in tool_call:
                tool_part = tool_call.split("SINGLE_TOOL:")[-1].strip()
                tool_name = tool_part.split("(")[0].strip()
                
                if tool_name not in valid_tool_names:
                    closest_tool = valid_tool_names[0] if valid_tool_names else "unknown"
                    corrected_call = tool_call.replace(tool_name, closest_tool)
                    data["tool_call"] = corrected_call
                    return json.dumps(data)
            
            # Validate multi tool call
            elif "MULTI_TOOL:" in tool_call:
                tool_pattern = r'(\w+)\('
                found_tools = re.findall(tool_pattern, tool_call)
                corrected_call = tool_call
                
                for found_tool in found_tools:
                    if found_tool not in valid_tool_names:
                        closest_tool = valid_tool_names[0] if valid_tool_names else "unknown"
                        corrected_call = corrected_call.replace(f"{found_tool}(", f"{closest_tool}(")
                
                if corrected_call != tool_call:
                    data["tool_call"] = corrected_call
                    return json.dumps(data)
        
        return llm_response
        
    except json.JSONDecodeError:
        return llm_response