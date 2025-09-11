"""CLI display - console rendering for agent consciousness."""

from ..core.protocols import Event


def _render_tools(tool_executions):
    """Render tool execution results using for_human() formatting."""
    for execution in tool_executions:
        result = execution.get("result", "")

        if result:
            # Use for_human() if available, otherwise fallback
            if hasattr(result, "for_human"):
                human_output = result.for_human()
            else:
                human_output = str(result)

            # Clean display with gap
            if human_output.strip():
                print(f"● {human_output.strip()}")
                print()  # Gap for readability


def _render_metrics(input_tokens: int, output_tokens: int, cost: float, duration: float):
    """Render final execution metrics with clean separation."""
    print(f"\n{'─' * 30}")
    print(f"{input_tokens}→{output_tokens} tokens | ${cost:.4f} | {duration:.1f}s")


class Renderer:
    """Stream consumer + console display."""

    def __init__(self, verbose: bool = False):
        self.pending_calls = None
        self.verbose = verbose
        self.current_state = None  # Track if we're in think/respond mode

    def _format_tool_input(self, call: dict) -> str:
        """Format tool call for human-readable display."""
        name = call.get("name", "unknown")
        args = call.get("args", {})
        
        # Per-tool human formatting
        match name:
            case "list":
                path = args.get("path", ".")
                pattern = args.get("pattern")
                if pattern and pattern != "*":
                    return f"list {path} (pattern: {pattern})"
                return f"list {path}" if path != "." else "list current directory"
            
            case "read":
                file = args.get("file", "")
                start = args.get("start")
                lines = args.get("lines")
                if start or lines:
                    return f"read {file} (lines {start or 1}-{(start or 1) + (lines or 0)})"
                return f"read {file}"
            
            case "write":
                file = args.get("file", "")
                content = args.get("content", "")
                line_count = len(content.split('\n')) if content else 0
                return f"write {file} ({line_count} lines)"
            
            case "edit":
                file = args.get("file", "")
                old = args.get("old", "")
                new = args.get("new", "")
                return f"edit {file}: {old[:20]}... → {new[:20]}..."
            
            case "shell":
                command = args.get("command", "")
                return f"shell: {command}"
            
            case "search":
                query = args.get("query", "")
                return f"search \"{query}\""
            
            case "scrape":
                url = args.get("url", "")
                return f"scrape {url}"
            
            case "recall":
                query = args.get("query", "")
                return f"recall \"{query}\""
            
            case _:
                # Fallback for unknown tools
                if args:
                    arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
                    return f"{name}({arg_str})"
                return f"{name}()"

    def _format_tool_output(self, call: dict, result) -> str:
        """Format tool result for human-readable display."""
        name = call.get("name", "unknown")
        
        # Use tool's for_human() method if available
        if hasattr(result, "for_human"):
            return result.for_human()
        
        # Per-tool output formatting
        match name:
            case "list":
                # Handle different result formats
                content = ""
                if hasattr(result, "content") and result.content:
                    content = result.content
                elif isinstance(result, str):
                    content = result
                elif hasattr(result, "for_human"):
                    content = result.for_human()
                
                if content and content.strip():
                    # Count actual files/items
                    lines = content.strip().split('\n')
                    if "listed" in content.lower() and "items" in content.lower():
                        # Extract file count from "Directory listed (X items)" format
                        import re
                        match = re.search(r'(\d+) items', content)
                        if match:
                            return f"found {match.group(1)} items"
                    
                    # Fallback: count non-empty lines that look like files
                    file_lines = [line for line in lines[2:] if line.strip() and not line.strip().startswith('-')]
                    return f"found {len(file_lines)} items" if file_lines else "directory scanned"
                
                return "directory empty"
            
            case "read":
                if hasattr(result, "content") and result.content:
                    lines = len(result.content.split('\n'))
                    return f"loaded {lines} lines"
                return "file empty"
            
            case "write":
                return "file created"
            
            case "edit":
                if hasattr(result, "outcome"):
                    # Extract replacement count from outcome
                    outcome = result.outcome
                    if "replacement" in outcome:
                        return "updated 1 match"
                return "file updated"
            
            case "shell":
                if hasattr(result, "outcome"):
                    outcome = result.outcome
                    if "exit: 0" in outcome:
                        return "command completed"
                    elif "exit:" in outcome:
                        return "command failed"
                return "command executed"
            
            case "search":
                if hasattr(result, "content") and result.content:
                    # Count search results
                    result_count = result.content.count("https://")
                    return f"found {result_count} results"
                return "no results"
            
            case "scrape":
                if hasattr(result, "content") and result.content:
                    char_count = len(result.content)
                    return f"extracted {char_count} characters"
                return "page empty"
            
            case "recall":
                if hasattr(result, "content") and result.content:
                    match_count = result.content.count("MATCH:")
                    return f"found {match_count} memories"
                return "no memories found"
            
            case _:
                # Fallback for unknown tools
                if hasattr(result, "outcome"):
                    return result.outcome
                return str(result)[:50] + "..." if len(str(result)) > 50 else str(result)

    def show_metrics(self, metrics: dict):
        """Display metrics after stream completion."""
        _render_metrics(
            metrics["input_tokens"], metrics["output_tokens"], metrics["cost"], metrics["duration"]
        )


    async def render_stream(self, agent_stream):
        """Consume agent events and render to console."""
        async for event in agent_stream:
            match event["type"]:
                case Event.THINK:
                    if event["content"]:
                        if self.current_state != "think":
                            print("\n~ ", end="", flush=True)
                            self.current_state = "think"
                        print(event['content'], end="", flush=True)
                case Event.CALLS:
                    if self.current_state:
                        print()  # Newline after streaming content
                    self.current_state = None
                    self.pending_calls = event["calls"]
                    for call in event["calls"]:
                        print(f"○ {self._format_tool_input(call)}")
                case Event.RESULTS:
                    if self.pending_calls and event.get("results"):
                        for call, result in zip(self.pending_calls, event["results"], strict=True):
                            print(f"● {self._format_tool_output(call, result)}")
                        print()
                        self.pending_calls = None
                case Event.RESPOND:
                    if event["content"]:
                        if self.current_state != "respond":
                            print("\n> ", end="", flush=True)
                            self.current_state = "respond"
                        print(event['content'], end="", flush=True)
                case "cancelled":
                    print(f"\n{event['content']}")
                    return
