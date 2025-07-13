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
    """Parse tool arguments string into typed dictionary."""
    parsed_args = {}
    if not raw_args:
        return parsed_args
        
    for arg_pair in raw_args.split(","):
        key, value_str = arg_pair.split("=", 1)
        key = key.strip()
        value_str = value_str.strip()

        # Attempt to convert to int, float, or bool
        if value_str.isdigit():
            parsed_args[key] = int(value_str)
        elif value_str.replace(".", "", 1).isdigit():
            parsed_args[key] = float(value_str)
        elif value_str.lower() == "true":
            parsed_args[key] = True
        elif value_str.lower() == "false":
            parsed_args[key] = False
        else:
            # Treat as string, remove surrounding quotes
            if value_str.startswith("'") and value_str.endswith("'"):
                parsed_args[key] = value_str[1:-1]
            elif value_str.startswith('"') and value_str.endswith('"'):
                parsed_args[key] = value_str[1:-1]
            else:
                parsed_args[key] = value_str
                
    return parsed_args


def extract_tool_call(llm_response: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract tool call from LLM response."""
    if llm_response.startswith("TOOL_CALL:"):
        try:
            tool_call_str = llm_response[len("TOOL_CALL:") :].strip()

            import re

            match = re.match(r"(\w+)\((.*)\)", tool_call_str)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                return tool_name, {"raw_args": args_str}
        except Exception:
            pass

    return None


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
