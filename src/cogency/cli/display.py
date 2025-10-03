from ..tools.format import format_call_human


class Renderer:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.current_state = None

    async def render_stream(self, agent_stream):
        async for event in agent_stream:
            match event["type"]:
                case "user":
                    if event["content"]:
                        if self.current_state != "user":
                            print("\n\n$ ", end="", flush=True)
                            self.current_state = "user"
                        print(event["content"], end="", flush=True)
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
                        from ..tools.parse import parse_tool_call

                        tool_call = parse_tool_call(event["content"])
                        action_display = format_call_human(tool_call)
                    except Exception:
                        action_display = "Tool execution"

                    print(f"\n\n○ {action_display}")

                case "result":
                    payload = event.get("payload", {})
                    outcome = payload.get("outcome", "Tool completed")
                    print(f"\n● {outcome}")
                    self.current_state = "result"
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
