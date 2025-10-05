"""CLI renderer for cogency event streams.

Event symbols:
  $ - user input
  ~ - agent thinking
  ○ - tool call
  ● - tool result
  > - agent response
  --- - turn separator
"""


class Renderer:
    def __init__(
        self,
        verbose: bool = False,
        model: str | None = None,
        identity: str | None = None,
        messages: list | None = None,
    ):
        self.verbose = verbose
        self.current_state = None
        self.model = model
        self.identity = identity
        self.messages = messages or []
        self.header_shown = False
        self.tool_count = 0
        self.last_metric = None

    async def render_stream(self, agent_stream):
        async for event in agent_stream:
            if not self.header_shown:
                parts = []
                if self.identity:
                    parts.append(f"<{self.identity}>")
                if self.messages:
                    msg_count = len(self.messages)
                    parts.append(f"{msg_count} msg{'s' if msg_count != 1 else ''}")
                
                if parts:
                    print(" | ".join(parts))

                self.header_shown = True
            match event["type"]:
                case "user":
                    if event["content"]:
                        print(f"---\n$ {event['content']}")
                        self.current_state = "user"
                case "think":
                    if event["content"]:
                        print(f"\n~ {event['content']}")
                        self.current_state = "think"
                case "call":
                    from ..tools import tools
                    from ..tools.parse import parse_tool_call
                    
                    self.tool_count += 1
                    try:
                        call = parse_tool_call(event.get("content", ""))
                        tool = tools.get(call.name)
                        content = tool.describe(call.args) if tool else f"{call.name}({call.args})"
                    except:
                        content = event.get("content", "Tool execution")
                    
                    print(f"\n○ {content}")
                    self.current_state = None
                case "execute":
                    pass
                case "result":
                    payload = event.get("payload", {})
                    outcome = payload.get("outcome", "Tool completed")
                    print(f"● {outcome}")
                    self.current_state = "result"
                case "respond":
                    if event["content"]:
                        if self.current_state != "respond":
                            print("\n> ", end="", flush=True)
                            self.current_state = "respond"
                        print(event["content"], end="", flush=True)
                case "end":
                    if self.current_state == "respond":
                        print("\n")
                    
                    # Show final stats
                    parts = []
                    if self.tool_count > 0:
                        parts.append(f"{self.tool_count} tool{'s' if self.tool_count != 1 else ''}")
                    if self.last_metric:
                        tok = self.last_metric['input'] + self.last_metric['output']
                        parts.append(f"{tok} tok")
                    
                    if parts:
                        print(" | ".join(parts))
                case "metric":
                    if "total" in event:
                        self.last_metric = event["total"]
                        if self.verbose:
                            total = event["total"]
                            print(f"% {total['input']}➜{total['output']}|{total['duration']:.1f}s")
                case "error":
                    payload = event.get("payload", {})
                    error_msg = payload.get("error", event.get("content", "Unknown error"))
                    print(f"✗ {error_msg}")
                case "interrupt":
                    print("⚠ Interrupted")
                    return
