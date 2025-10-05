"""CLI renderer for cogency event streams.

Event symbols:
  $ - user input
  ~ - agent thinking
  ○ - tool call (in progress)
  ● - tool result (completed)
  > - agent response
  --- - turn separator
"""

from ..lib.color import C


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
        self.pending_call = None
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_task = None

    async def render_stream(self, agent_stream):
        async for event in agent_stream:
            if not self.header_shown:
                parts = []
                if self.messages:
                    msg_count = len(self.messages)
                    parts.append(f"{msg_count} msg{'s' if msg_count != 1 else ''}")
                    
                    last_metrics = self._get_last_metrics()
                    if last_metrics:
                        tok_in = last_metrics.get('input', 0)
                        tok_out = last_metrics.get('output', 0)
                        parts.append(f"{tok_in}→{tok_out} tok")
                
                if parts:
                    print(f"{C.gray}" + " | ".join(parts) + f"{C.R}")

                self.header_shown = True
            match event["type"]:
                case "user":
                    if event["content"]:
                        print(f"{C.gray}---{C.R}\n{C.cyan}${C.R} {event['content']}")
                        self.current_state = "user"
                case "think":
                    content = event["content"]
                    if content and content.strip():
                        if self.current_state != "think":
                            self._transition_state("think")
                        print(content.lstrip() if self.current_state == "think" else content, end="", flush=True)
                case "call":
                    from ..tools.parse import parse_tool_call
                    
                    self._transition_state(None)
                    self.tool_count += 1
                    try:
                        call = parse_tool_call(event.get("content", ""))
                        self.pending_call = call
                        in_progress = self._format_in_progress(call)
                        print(f"\r{C.cyan}○{C.R} {in_progress}", end="", flush=True)
                    except:
                        self.pending_call = None
                case "execute":
                    if self.pending_call:
                        import asyncio
                        self.spinner_task = asyncio.create_task(self._animate_spinner())
                case "result":
                    if self.spinner_task:
                        self.spinner_task.cancel()
                        self.spinner_task = None
                    
                    if self.pending_call:
                        action = self._format_action(self.pending_call, event)
                        print(f"\r{C.green}●{C.R} {action}\n", end="", flush=True)
                        self.pending_call = None
                    self._transition_state(None)
                case "respond":
                    content = event["content"]
                    if content and content.strip():
                        if self.current_state != "respond":
                            self._transition_state("respond")
                        print(content.lstrip() if self.current_state == "respond" else content, end="", flush=True)
                case "end":
                    self._transition_state(None)
                    print()
                case "metric":
                    if "total" in event:
                        self.last_metric = event["total"]
                        if self.verbose:
                            total = event["total"]
                            print(f"% {total['input']}➜{total['output']}|{total['duration']:.1f}s")
                case "error":
                    payload = event.get("payload", {})
                    error_msg = payload.get("error", event.get("content", "Unknown error"))
                    print(f"{C.red}✗{C.R} {error_msg}")
                case "interrupt":
                    print(f"{C.yellow}⚠{C.R} Interrupted")
                    return

    async def _animate_spinner(self):
        import asyncio
        if not self.pending_call:
            return
        
        name = self._normalize_tool_name(self.pending_call.name)
        arg = self._extract_primary_arg(self.pending_call)
        base = f'{name}("{arg}")' if arg else f"{name}()"
        
        try:
            while True:
                frame = self.spinner_frames[self.spinner_index]
                print(f"\r{C.cyan}{frame}{C.R} {base}", end="", flush=True)
                self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
                await asyncio.sleep(0.08)
        except asyncio.CancelledError:
            pass
    
    def _transition_state(self, new_state: str | None):
        if self.current_state in ("think", "respond"):
            print(C.R, end="", flush=True)
        
        match new_state:
            case "think":
                if self.current_state is None:
                    print(f"{C.gray}~{C.R} ", end="", flush=True)
                else:
                    print(f"\n{C.gray}~{C.R} ", end="", flush=True)
            case "respond":
                if self.current_state is None:
                    print(f"> ", end="", flush=True)
                else:
                    print(f"\n> ", end="", flush=True)
        
        self.current_state = new_state
    
    def _get_last_metrics(self) -> dict | None:
        if not self.messages:
            return None
        
        for msg in reversed(self.messages):
            if msg.get("type") == "metric" and "total" in msg:
                return msg["total"]
        return None

    def _format_in_progress(self, call) -> str:
        name = self._normalize_tool_name(call.name)
        arg = self._extract_primary_arg(call)
        return f'{name}("{arg}")...' if arg else f"{name}()..."
    
    def _format_action(self, call, result_event) -> str:
        payload = result_event.get("payload", {})
        name = self._normalize_tool_name(call.name)
        arg = self._extract_primary_arg(call)
        outcome = self._extract_outcome(payload)
        
        base = f'{name}("{arg}")' if arg else f"{name}()"
        return f"{base}: {outcome}" if outcome else base
    
    def _normalize_tool_name(self, name: str) -> str:
        import re
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return snake
    
    def _extract_primary_arg(self, call) -> str:
        args = call.args
        if not isinstance(args, dict):
            return ""
        
        arg_keys = ["file", "path", "file_path", "pattern", "query", "command", "url", "dir"]
        for key in arg_keys:
            if key in args and args[key]:
                value = str(args[key])
                return value if len(value) < 50 else value[:47] + "..."
        
        if args:
            first_val = str(next(iter(args.values())))
            return first_val if len(first_val) < 50 else first_val[:47] + "..."
        
        return ""
    
    def _extract_outcome(self, payload) -> str:
        if "error" in payload and payload["error"]:
            err = payload.get("outcome", "error")
            return err
        
        outcome = payload.get("outcome", "")
        if outcome:
            return outcome
        
        return "ok"
    
