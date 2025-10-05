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

    async def render_stream(self, agent_stream):
        async for event in agent_stream:
            if not self.header_shown:
                parts = []
                if self.model:
                    parts.append(f"model: {self.model}")
                if self.identity:
                    parts.append(f"identity: {self.identity}")
                if parts:
                    print(" | ".join(parts))

                if self.messages:
                    print(f"History ({len(self.messages)} messages):")
                    for msg in self.messages:
                        role = msg.get("role", "?")
                        content = msg.get("content", "")[:80]
                        print(f"  [{role}] {content}")

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
                    content = event.get("content", "Tool execution")
                    print(f"○ {content}")
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
                case "metric":
                    if self.verbose and "total" in event:
                        total = event["total"]
                        print(f"% {total['input']}➜{total['output']}|{total['duration']:.1f}s")
                case "error":
                    payload = event.get("payload", {})
                    error_msg = payload.get("error", event.get("content", "Unknown error"))
                    print(f"✗ {error_msg}")
                case "interrupt":
                    print("⚠ Interrupted")
                    return
