"""User interface - general messaging system."""
from typing import List, Callable, Awaitable, Dict, Any, Optional
import json


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji from registered tools with fallback."""
    try:
        from cogency.tools.registry import ToolRegistry
        for tool_class in ToolRegistry._tools:
            try:
                tool = tool_class()
                if tool.name.lower() == tool_name.lower():
                    return tool.emoji
            except:
                continue
        return "🛠️"
    except:
        return "🛠️"


def _truncate(text: str, max_len: int = 30) -> str:
    """Smart truncation preserving meaning."""
    if len(text) <= max_len:
        return text
    
    # URLs: preserve domain
    if text.startswith(('http://', 'https://')):
        try:
            from urllib.parse import urlparse
            domain = urlparse(text).netloc
            return f"{domain}/..." if len(domain) <= max_len - 4 else f"{domain[:max_len-3]}..."
        except:
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


def format_tool_params(tool_name: str, params: Dict[str, Any]) -> str:
    """Format tool parameters for display."""
    if not params:
        return ""
    
    try:
        name = tool_name.lower()
        
        # Tool-specific formatting
        if name == "weather":
            return f"({params.get('city', '')})"
        
        elif name == "calculator":
            op, x1, x2 = params.get("operation"), params.get("x1"), params.get("x2")
            symbols = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
            if op in symbols and x1 is not None and x2 is not None:
                return f"({x1} {symbols[op]} {x2})"
            elif op == "square_root" and x1 is not None:
                return f"(√{x1})"
        
        elif "search" in name:
            query = params.get("query", params.get("q", ""))
            return f"({_truncate(query, 35)})" if query else ""
        
        elif name == "recall":
            query = params.get("query", "")
            return f"({_truncate(query, 30)})" if query else ""
        
        elif name == "file":
            action, filename = params.get("action"), params.get("filename")
            if action and filename:
                return f"({action}, {_truncate(filename, 25)})"
            return f"({_truncate(filename or '', 30)})" if filename else ""
        
        elif name == "http":
            url, method = params.get("url"), params.get("method", "get").upper()
            return f"({method} {_truncate(url, 30)})" if url else ""
        
        elif name in ["shell", "code"]:
            cmd = params.get("command", params.get("code", ""))
            return f"({_truncate(cmd, 35)})" if cmd else ""
        
        # Generic: first value
        first_val = list(params.values())[0]
        return f"({_truncate(str(first_val), 25)})"
    
    except:
        return ""


def contextualize_result(tool_name: str, result: Any) -> str:
    """Extract meaningful info from results."""
    if result is None:
        return "completed"
    
    try:
        name = tool_name.lower()
        
        if isinstance(result, dict):
            # Tool-specific
            if name == "weather" and "temperature" in result and "condition" in result:
                return f"{result['temperature']} {result['condition']}"
            elif name == "calculator" and "result" in result:
                return str(result["result"])
            elif "search" in name and "results_count" in result:
                count = result["results_count"]
                return f"{count} results" if count != 1 else "1 result"
            elif name == "http" and "status_code" in result:
                code = result["status_code"]
                return f"{'✓' if 200 <= code < 300 else '✗'} {code}"
            elif name in ["shell", "code"]:
                if result.get("success"):
                    output = result.get("output", result.get("stdout", ""))
                    return _truncate(output.strip(), 50) if output and output.strip() else "✓ success"
                else:
                    error = result.get("error", result.get("stderr", "failed"))
                    return _truncate(str(error), 40)
            
            # Generic dict
            for key in ["result", "data", "content", "message"]:
                if key in result:
                    return _truncate(str(result[key]), 50)
        
        elif isinstance(result, (list, tuple)):
            return f"{len(result)} items" if len(result) > 1 else "empty" if len(result) == 0 else str(result[0])
        
        elif isinstance(result, bool):
            return "✓ success" if result else "✗ failed"
        
        return _truncate(str(result), 60)
    
    except:
        return "completed"


def should_show_reasoning(text: str) -> bool:
    """Skip obvious reasoning."""
    if not text or len(text.strip()) < 10:
        return False
    
    obvious = [
        "i need to use", "i'll use the", "user wants", "let me", "i should", "i will",
        "i have all", "all needed information", "i can answer", "now i'll", "first i'll",
        "i need to calculate", "i need to search", "i need to check", "i need to get",
        "i have the result", "now i need to add", "i need to add the", "next i'll"
    ]
    return not any(pattern in text.lower() for pattern in obvious)


class AgentMessenger:
    """Clean, unified messaging for agent-user communication."""
    
    @staticmethod
    async def tool_execution(
        callback: Callable[[str], Awaitable[None]], 
        tool_name: str, 
        params: Dict[str, Any], 
        result: Any,
        success: bool = True
    ) -> None:
        """Display tool execution with emoji, params, and result."""
        try:
            emoji = get_tool_emoji(tool_name)
            formatted_params = format_tool_params(tool_name, params)
            
            if success:
                formatted_result = contextualize_result(tool_name, result)
                await callback(f"{emoji} {tool_name}{formatted_params} → {formatted_result}\n")
            else:
                error_msg = str(result) if result else "failed"
                await callback(f"{emoji} {tool_name}{formatted_params} → ❌ {error_msg}\n")
        except Exception:
            # Fallback to simple display
            await callback(f"🛠️ {tool_name} → {'completed' if success else 'failed'}\n")
    
    @staticmethod
    async def reasoning(
        callback: Callable[[str], Awaitable[None]], 
        text: str,
        force_show: bool = False
    ) -> None:
        """Show reasoning only when non-obvious."""
        try:
            if force_show or should_show_reasoning(text):
                await callback(f"🧠 {text}\n")
        except Exception:
            pass
    
    @staticmethod
    async def memory_operation(
        callback: Callable[[str], Awaitable[None]], 
        operation_type: str, 
        content: str
    ) -> None:
        """Display memory operations clearly."""
        try:
            if operation_type == "save":
                await callback(f"💾 {content}\n")
            elif operation_type == "recall":
                await callback(f"🧠 {content}\n")
        except Exception:
            pass
    
    @staticmethod
    async def error(
        callback: Callable[[str], Awaitable[None]], 
        error_msg: str, 
        context: Optional[str] = None
    ) -> None:
        """Display errors with context."""
        try:
            if context:
                await callback(f"❌ {error_msg} ({context})\n")
            else:
                await callback(f"❌ {error_msg}\n")
        except Exception:
            pass
    
    @staticmethod
    async def agent_response(callback: Callable[[str], Awaitable[None]], response: str) -> None:
        """🤖 AGENT: Final response."""
        await callback(f"\n🤖 {response}\n")
    
    @staticmethod
    async def spacing(callback: Callable[[str], Awaitable[None]]) -> None:
        """Add spacing between phases."""
        await callback("\n")
    
    # Legacy methods for backward compatibility during transition
    @staticmethod
    async def memorize(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """Legacy: Memory extraction/saving."""
        await AgentMessenger.memory_operation(callback, "save", message)
    
    @staticmethod
    async def tooling(callback: Callable[[str], Awaitable[None]], tool_names: List[str]) -> None:
        """Legacy: Tool selection - now silent unless debugging."""
        pass  # Eliminated ceremony
    
    @staticmethod
    async def reason(callback: Callable[[str], Awaitable[None]], message: str = "Analyzing information and deciding next action") -> None:
        """Legacy: Reasoning phase."""
        await AgentMessenger.reasoning(callback, message)
    
    @staticmethod
    async def act(callback: Callable[[str], Awaitable[None]], tool_names: List[str]) -> None:
        """Legacy: Tool execution phase - now handled by tool_execution."""
        pass  # Eliminated ceremony - actual execution shown by tool_execution
    
    @staticmethod
    async def observe(callback: Callable[[str], Awaitable[None]], message: str) -> None:
        """Legacy: Processing tool results - now handled by tool_execution."""
        pass  # Eliminated ceremony - results shown by tool_execution
    
    @staticmethod
    async def human_input(callback: Callable[[str], Awaitable[None]], query: str) -> None:
        """👤 HUMAN: User input."""
        await callback(f"👤 {query}\n")
