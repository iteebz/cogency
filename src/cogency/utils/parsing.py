import json
from typing import Any, Dict, Optional, Tuple, List


def parse_plan_response(response: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Parse plan node JSON response to determine routing action."""
    if response is None:
        return "respond", {"action": "direct_response", "content": "No response"}
    try:
        data = json.loads(response)
        action = data.get("action")
        if action == "tool_needed":
            return "reason", data
        elif action == "direct_response":
            return "respond", data
        else:
            # Fallback to prefix parsing for compatibility
            if response.startswith("TOOL_NEEDED:"):
                return "reason", {"action": "tool_needed", "content": response[12:]}
            return "respond", {"action": "direct_response", "content": response}
    except json.JSONDecodeError:
        # Fallback to prefix parsing
        if response.startswith("TOOL_NEEDED:"):
            return "reason", {"action": "tool_needed", "content": response[12:]}
        return "respond", {"action": "direct_response", "content": response}


def parse_reflect_response(response: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Parse reflect node JSON response to determine routing action."""
    if response is None:
        return "respond", {"status": "complete", "content": "No response"}
    try:
        data = json.loads(response)
        status = data.get("status")
        if status == "continue":
            return "reason", data
        elif status == "complete":
            return "respond", data
        else:
            # Fallback: if status is missing or unknown, default to complete
            return "respond", {"status": "complete", "content": response}
    except json.JSONDecodeError:
        # Fallback to prefix parsing
        if response.startswith("TASK_COMPLETE:"):
            return "respond", {"status": "complete", "content": response[14:]}
        # Default to complete instead of continue to prevent loops
        return "respond", {"status": "complete", "content": response}


def parse_tool_args(raw_args: str) -> Dict[str, Any]:
    """Parse tool arguments - SIMPLE AND ROBUST."""
    if not raw_args:
        return {}
    
    import ast
    import re
    try:
        # Convert function args to dict syntax: key=value -> 'key': value
        dict_str = re.sub(r'(\w+)=', r"'\1':", raw_args)
        dict_str = f"{{{dict_str}}}"
        return ast.literal_eval(dict_str)
    except:
        # Fallback: try to eval individual values
        result = {}
        for pair in raw_args.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip()
                try:
                    result[k] = ast.literal_eval(v)
                except:
                    result[k] = v.strip("'\"")
        return result


def extract_tool_call(llm_response: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract tool call from LLM response - supports both single and parallel calls."""
    import re
    
    # Search for TOOL_CALL: anywhere in the response
    tool_call_match = re.search(r"TOOL_CALL:\s*(\w+)\((.*?)\)", llm_response, re.DOTALL)
    if tool_call_match:
        tool_name = tool_call_match.group(1)
        args_str = tool_call_match.group(2).strip()
        return tool_name, {"raw_args": args_str}
    
    # Search for PARALLEL_CALLS: anywhere in the response  
    parallel_match = re.search(r"PARALLEL_CALLS:\s*(.*)", llm_response, re.DOTALL)
    if parallel_match:
        parallel_str = parallel_match.group(1).strip()
        return "PARALLEL", {"parallel_calls": parallel_str}

    return None


def parse_parallel_calls(parallel_str: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Parse parallel tool calls string into list of (tool_name, args) tuples."""
    import re
    
    # Remove brackets and split by tool calls
    parallel_str = parallel_str.strip()
    if parallel_str.startswith("[") and parallel_str.endswith("]"):
        parallel_str = parallel_str[1:-1]
    
    calls = []
    # Simple parsing - split by commas not inside parentheses
    call_parts = []
    paren_count = 0
    current_part = ""
    
    for char in parallel_str:
        if char == "(":
            paren_count += 1
        elif char == ")":
            paren_count -= 1
        elif char == "," and paren_count == 0:
            call_parts.append(current_part.strip())
            current_part = ""
            continue
        current_part += char
    
    if current_part.strip():
        call_parts.append(current_part.strip())
    
    for call_str in call_parts:
        match = re.match(r"(\w+)\((.*)\)", call_str.strip())
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            calls.append((tool_name, {"raw_args": args_str}))
    
    return calls


def prepare_node_messages(context, tools: List, prompt_template: str):
    """Prepare messages for node execution with tool instructions."""
    # Build proper message sequence: include conversation history + current input
    messages = list(context.messages)
    if not any(
        msg.get("role") == "user" and msg.get("content") == context.current_input
        for msg in messages
    ):
        messages.append({"role": "user", "content": context.current_input})

    tool_instructions = ""
    if tools:
        # Full tool schemas for precise formatting
        schemas = []
        all_examples = []
        for tool in tools:
            schemas.append(f"- {tool.name}: {tool.description}")
            schemas.append(f"  Schema: {tool.get_schema()}")
            all_examples.extend([f"  {example}" for example in tool.get_usage_examples()])

        tool_instructions = prompt_template.format(
            tool_schemas="\n".join(schemas), tool_examples="\n".join(all_examples)
        )

    if tool_instructions:
        messages.insert(0, {"role": "system", "content": tool_instructions})
        
    return messages
