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

    def __init__(self, show_stream: bool = False, verbose: bool = False):
        self.pending_calls = None
        self.thinking_started = False
        self.show_stream = show_stream
        self.verbose = verbose
        self.token_count = 0

    def show_metrics(self, metrics: dict):
        """Display metrics after stream completion."""
        _render_metrics(
            metrics["input_tokens"], metrics["output_tokens"], metrics["cost"], metrics["duration"]
        )

    async def render_stream(self, agent_stream):
        """Consume agent events and render to console."""

        async for event in agent_stream:
            # STREAM DEBUGGING - show raw tokens when enabled
            if self.show_stream and event["type"] in [Event.THINK, Event.RESPOND]:
                self.token_count += 1
                if (
                    self.token_count % 10 == 0 or len(event.get("content", "")) > 0
                ):  # Sample every 10th token
                    token_preview = repr(event.get("content", ""))[:50]
                    print(f"STREAM TOKEN {self.token_count}: {token_preview}")

            # Skip debug events unless verbose mode
            if event["type"] == "yield" and not self.verbose:
                continue

            match event["type"]:
                case Event.THINK:
                    content = event["content"]
                    if content and content.strip():
                        if not self.thinking_started:
                            print(f"~ {content.strip()}", end="", flush=True)
                            self.thinking_started = True
                        else:
                            print(content, end="", flush=True)
                case Event.CALLS:
                    # Reset thinking state and show tool calls
                    if self.thinking_started:
                        print()  # Newline after thinking
                        self.thinking_started = False
                    self.pending_calls = event["calls"]
                    for call in event["calls"]:
                        name = call.get("name", "unknown")
                        args = call.get("args", {})
                        if args:
                            arg_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
                            print(f"○ {name}({arg_str})")
                        else:
                            print(f"○ {name}()")
                case Event.RESULTS:
                    # Zip with pending calls for display
                    if self.pending_calls and event.get("results"):
                        executions = []
                        for call, result in zip(self.pending_calls, event["results"], strict=True):
                            executions.append({"call": call, "result": result})
                        _render_tools(executions)
                        self.pending_calls = None
                case Event.RESPOND:
                    if self.thinking_started:
                        print()  # Newline after thinking
                        self.thinking_started = False
                    print(event["content"], end="", flush=True)
                case Event.YIELD:
                    # Stream termination signal - natural handover point
                    if self.thinking_started:
                        print()  # Clean newline after thinking
                        self.thinking_started = False
                    return  # Exit stream consumption
