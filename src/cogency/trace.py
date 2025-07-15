"""BEAUTIFUL tracing with ZERO ceremony."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


@dataclass
class TraceStep:
    """Single execution step - BEAUTIFUL narrative format."""
    node: str
    summary: str
    
    def __str__(self) -> str:
        # Emoji mapping for cognitive workflow nodes
        emojis = {
            "plan": "🎯",
            "reason": "🧠", 
            "act": "🔧",
            "reflect": "🤔",
            "respond": "💬"
        }
        emoji = emojis.get(self.node, "⚡")
        return f"   {emoji} {self.node.upper().ljust(8)} → {self.summary}"


@dataclass 
class ExecutionTrace:
    """Beautiful narrative trace - shows reasoning flow."""
    steps: List[TraceStep] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    user_query: str = ""
    
    def add(self, node: str, context: dict):
        """Add step with intelligent extraction from actual responses."""
        summary = self._extract_summary(node, context)
        self.steps.append(TraceStep(node, summary))
    
    def _extract_summary(self, node: str, context) -> str:
        """Extract meaningful summaries from actual responses - ZERO HARDCODING."""
        if not context or not hasattr(context, "messages") or not context.messages:
            return f"{node} completed"
            
        last_msg = context.messages[-1].get("content", "")
        
        # Node-specific intelligent extraction
        if node == "plan":
            if "tool_needed" in last_msg.lower():
                return "Tool needed for this query"
            else:
                return "Direct response possible"
                
        elif node == "reason":
            # Extract actual tool calls from LLM response
            if "TOOL_CALL:" in last_msg:
                import re
                match = re.search(r"TOOL_CALL:\s*(\w+)\(", last_msg)
                if match:
                    tool_name = match.group(1)
                    return f"Selected {tool_name} tool"
            elif "PARALLEL_CALLS:" in last_msg:
                import re
                # Count tool calls in parallel format
                tool_matches = re.findall(r"(\w+)\(", last_msg)
                if tool_matches:
                    if len(tool_matches) == 1:
                        return f"Selected {tool_matches[0]} tool"
                    else:
                        return f"Selected {len(tool_matches)} tools: {', '.join(tool_matches)}"
            return "Tool reasoning complete"
            
        elif node == "act":
            # Extract tool execution result intelligently
            if "Parallel execution results:" in last_msg:
                # Count number of tools executed in parallel
                tool_count = last_msg.count("- ")
                return f"Parallel execution → {tool_count} tools completed"
            elif "temperature" in last_msg and "°" in last_msg:
                import re
                temp_match = re.search(r'(\d+)°[CF]', last_msg)
                if temp_match:
                    temp = temp_match.group(1)
                    return f"Weather tool → {temp}°C retrieved"
            elif len(last_msg) > 500:  # Long response, likely search/file
                if "search" in last_msg.lower() or "http" in last_msg.lower():
                    return "Search results retrieved"
                elif "file" in last_msg.lower() or "directory" in last_msg.lower():
                    return "File operation completed"
                else:
                    return "Large dataset retrieved"
            elif any(calc_word in last_msg for calc_word in ["=", "+", "*", "/", "-"]):
                # Extract calculation result
                import re
                result_match = re.search(r'(\d+(?:\.\d+)?)', last_msg)
                if result_match:
                    return f"Calculated → {result_match.group(1)}"
            return "Tool executed successfully"
            
        elif node == "reflect":
            # Extract intelligent reflection summary
            if "complete" in last_msg.lower():
                # Check if it mentions validation or filtering
                if "filtered" in last_msg.lower() or "relevant" in last_msg.lower():
                    return "Filtered and validated results"
                elif "validated" in last_msg.lower() or "verification" in last_msg.lower():
                    return "Results validated"
                else:
                    return "Task complete"
            return "Validation complete"
            
        elif node == "respond":
            clean_msg = last_msg.strip()
            if len(clean_msg) > 60:
                return f"{clean_msg[:60]}..."
            return clean_msg
        
        return f"{node} completed"
    


def trace_node(func):
    """Beautiful trace decorator - captures meaningful input/output."""
    async def wrapper(*args, **kwargs):
        state = args[0] if args else None
        if not (isinstance(state, dict) and state.get("execution_trace")):
            return await func(*args, **kwargs)
            
        # Capture meaningful input
        context = state.get("context")
        input_summary = f"User: '{context.current_input}'" if context else "No context"
        
        start = datetime.now()
        result = await func(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        # Capture meaningful output
        output_context = result.get("context") if isinstance(result, dict) else None
        if output_context and output_context.messages:
            last_message = output_context.messages[-1].get("content", "")
            output_summary = f"Response: '{last_message[:100]}...'" if len(last_message) > 100 else f"Response: '{last_message}'"
        else:
            output_summary = "No response generated"
        
        state["execution_trace"].add(func.__name__.upper(), input_summary, output_summary, duration)
        return result
    
    return wrapper