"""CLI display - console rendering for streaming agents."""

from ..core.protocols import ToolCall
from ..tools.format import format_call_human


def _render_metrics(input_tokens: int, output_tokens: int, duration: float, verbose: bool = False):
    """Render final execution metrics subtly."""
    if verbose:
        print(f"\n[{input_tokens}→{output_tokens} tokens, {duration:.1f}s]")
    else:
        # Just a subtle hint, no jarring separators
        print(f"[{input_tokens}→{output_tokens} tokens, {duration:.1f}s]")


class Renderer:
    """Stream consumer + console display."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.current_state = None  # Track if we're in think/respond mode

    def show_metrics(self, metrics: dict):
        """Display metrics after stream completion."""
        _render_metrics(
            metrics["input_tokens"], metrics["output_tokens"], metrics["duration"], self.verbose
        )

    async def render_stream(self, agent_stream):
        """Consume agent events and render to console."""

        async for event in agent_stream:
            match event["type"]:
                case "think":
                    if event["content"]:
                        if self.current_state != "think":
                            print("\n\n~ ", end="", flush=True)
                            self.current_state = "think"
                        print(event["content"], end="", flush=True)
                case "call":
                    # Tool call started - show action
                    self.current_state = None

                    # Parse call and format display using Formatter
                    try:
                        tool_call = ToolCall.from_json(event["content"])
                        action_display = format_call_human(tool_call)
                    except Exception:
                        action_display = "Tool execution"

                    print(f"\n\n○ {action_display}")

                case "result":
                    # Tool result - show outcome using event data
                    outcome = event.get("content", "Tool completed")
                    print(f"\n● {outcome}")
                case "respond":
                    if event["content"]:
                        if self.current_state != "respond":
                            print("\n\n> ", end="", flush=True)
                            self.current_state = "respond"
                        print(event["content"], end="", flush=True)
                case "metrics":
                    # Display metrics immediately
                    if "total" in event:
                        total = event["total"]
                        print(f"\n\n% {total['input']}➜{total['output']}|{total['duration']:.1f}s")
                case "cancelled":
                    print(f"\n{event['content']}")
                    return
