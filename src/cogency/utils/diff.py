"""State diff computation and trace message generation."""
from copy import deepcopy
from typing import Dict, Any


def compute_diff(before: dict, after: dict) -> dict:
    """Compute meaningful differences between states."""
    diff = {}
    
    # Check for selected_tools changes
    if before.get("selected_tools") != after.get("selected_tools"):
        diff["selected_tools"] = after.get("selected_tools", [])
    
    # Check for context message changes
    before_context = before.get("context")
    after_context = after.get("context")
    
    if before_context and after_context:
        before_msgs = len(before_context.messages) if hasattr(before_context, 'messages') else 0
        after_msgs = len(after_context.messages) if hasattr(after_context, 'messages') else 0
        
        if before_msgs != after_msgs:
            diff["new_messages"] = after_msgs - before_msgs
            if after_msgs > 0 and hasattr(after_context, 'messages'):
                diff["latest_message"] = after_context.messages[-1]
    
    # Check for new keys in result
    for key in after:
        if key not in before and key not in ["context", "trace"]:
            diff[key] = after[key]
    
    return diff


def generate_trace_message(node: str, delta: dict) -> str:
    """Generate meaningful trace message from state diff."""
    
    if node == "think":
        if "thinking_response" in delta:
            response = delta["thinking_response"]
            if "DIRECT_RESPONSE" in response:
                return "Determined query can be answered directly"
            elif "NEED_TOOLS" in response:
                return "Identified that tools are needed"
            else:
                return "Completed analysis of query"
        return "Analyzed user query"
    
    elif node == "plan":
        if "selected_tools" in delta:
            tools = delta["selected_tools"]
            if tools:
                tool_names = [t.name for t in tools]
                return f"Selected {len(tools)} tools: {', '.join(tool_names)}"
            else:
                return "No tools selected"
        
        if "plan_response" in delta:
            try:
                import json
                plan_data = json.loads(delta["plan_response"])
                action = plan_data.get("action", "")
                if action == "direct_response":
                    return "Decided to respond directly"
                elif action == "tool_needed":
                    return "Planned tool execution"
            except:
                pass
        
        return "Generated execution plan"
    
    elif node == "act":
        if "new_messages" in delta:
            msg_count = delta["new_messages"]
            if msg_count > 0:
                return f"Executed {msg_count} tool call(s)"
        return "Executed tools"
    
    elif node == "reflect":
        if "reflection_response" in delta:
            try:
                import json
                reflection = json.loads(delta["reflection_response"])
                status = reflection.get("status", "")
                if status == "complete":
                    return "Task marked complete"
                elif status == "continue":
                    return "Task needs more work"
                elif status == "error":
                    return "Error detected in task"
            except:
                pass
        return "Evaluated task completion"
    
    elif node == "respond":
        if "response" in delta:
            response = delta["response"]
            word_count = len(response.split())
            return f"Generated {word_count}-word response"
        return "Generated response"
    
    return f"Completed {node}"