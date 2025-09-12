"""CLI display - console rendering for agent consciousness."""

# No enum - just strings


def _render_metrics(input_tokens: int, output_tokens: int, duration: float):
    """Render final execution metrics with clean separation."""
    print(f"\n{'─' * 30}")
    print(f"{input_tokens}→{output_tokens} tokens | {duration:.1f}s")


class Renderer:
    """Stream consumer + console display."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.current_state = None  # Track if we're in think/respond mode

    def show_metrics(self, metrics: dict):
        """Display metrics after stream completion."""
        _render_metrics(metrics["input_tokens"], metrics["output_tokens"], metrics["duration"])

    async def render_stream(self, agent_stream):
        """Consume agent events and render to console."""
        async for event in agent_stream:
            match event["type"]:
                case "think":
                    if event["content"]:
                        if self.current_state != "think":
                            print("\n~ ", end="", flush=True)
                            self.current_state = "think"
                        print(event["content"] + " ", end="", flush=True)
                case "tool":
                    # Clean tool event display - humans see semantic action + clean result
                    if self.current_state:
                        print()  # Newline after streaming content
                    self.current_state = None
                    
                    status_marker = "●" if event.get("status") == "success" else "✗"
                    action_display = event.get("display", "Tool execution")
                    result_display = event.get("result_human", "")
                    
                    print(f"{status_marker} {action_display}")
                    if result_display:
                        print(f"  {result_display}")
                    print()  # Gap for readability
                case "respond":
                    if event["content"]:
                        if self.current_state != "respond":
                            print("\n> ", end="", flush=True)
                            self.current_state = "respond"
                        print(event["content"] + " ", end="", flush=True)
                case "cancelled":
                    print(f"\n{event['content']}")
                    return
