import re
from typing import Optional, Tuple, Any, Dict

def _extract_tool_call(llm_response: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    tool_call = None
    if llm_response.startswith("TOOL_CALL:"):
        try:
            tool_call_str = llm_response[len("TOOL_CALL:"):].strip()
            
            match = re.match(r"(\w+)\((.*)\)", tool_call_str)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                return tool_name, {"raw_args": args_str}
        except Exception as e:
            pass # Error parsing tool call: {e}
    
    return tool_call