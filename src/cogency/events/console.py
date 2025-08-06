"""Console output for development."""


def console_callback(event):
    """Console callback - shows useful intermediate processes."""
    event_type = event["type"]
    data = {**event.get("data", {}), **event}

    if event_type == "start":
        print("🤔 Thinking...")

    elif event_type == "reason":
        content = data.get("content", "")
        if content:
            if len(content) > 120:
                content = content[:120] + "..."
            print(f"💭 {content}")

    elif event_type == "action":
        tool = data.get("tool", "")
        if tool:
            print(f"🛠️ {tool}")

    elif event_type == "tool" and data.get("ok"):
        name = data.get("name", "tool")
        print(f"✅ {name}")

    elif event_type == "agent_complete":
        print("✅ Done")

    elif event_type == "error":
        message = data.get("message", "Error")
        print(f"❌ {message}")


class ConsoleHandler:
    """Handler that prints to console."""

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = True  # Force debug to see input format

    def handle(self, event):
        if not self.enabled:
            return

        event_type = event["type"]
        data = {**event.get("data", {}), **event}

        # Show thinking/planning state
        if event_type == "start":
            query = data.get("query", "")
            if query:
                lines = [line.strip() for line in query.strip().split('\n') if line.strip()]
                if len(lines) <= 3:
                    print(f"⏺ {query.strip()}")
                else:
                    print(f"⏺ {lines[0]}")
                    print("   ⎿ " + " ".join(lines[1:])[:100] + ("..." if len(" ".join(lines[1:])) > 100 else ""))

        # Show actions being taken  
        elif event_type == "action" and data.get("state") == "executing":
            tool = data.get("tool", "")
            input_text = data.get("input", "")
            
            # DEBUG: Print all data to understand format
            if self.debug:
                print(f"[DEBUG] Full event data: {data}")
                print(f"[DEBUG] Tool: {tool}, Input: {input_text}")
            
            if tool == "shell":
                # Extract command from input
                try:
                    if isinstance(input_text, dict):
                        cmd = input_text.get("command", "")
                        print(f"⏺ Shell({cmd})")
                    elif "command" in str(input_text):
                        import re
                        match = re.search(r'"command":\s*"([^"]+)"', str(input_text))
                        if match:
                            cmd = match.group(1)
                            print(f"⏺ Shell({cmd})")
                        else:
                            print(f"⏺ Shell({str(input_text)[:50]}...)")
                    else:
                        print(f"⏺ Shell()")
                except:
                    print(f"⏺ Shell()")
                    
            elif tool == "files":
                # Extract file operation details
                try:
                    if isinstance(input_text, dict):
                        action = input_text.get("action", "")
                        path = input_text.get("path", "")
                        content = input_text.get("content", "")
                        
                        if action == "create" and path:
                            print(f"⏺ Create({path})")
                        elif action == "read" and path:
                            print(f"⏺ Read({path})")
                        elif action == "update" and path:
                            print(f"⏺ Update({path})")
                        elif action and path:
                            print(f"⏺ {action.title()}({path})")
                        elif action:
                            print(f"⏺ Files({action})")
                        else:
                            print(f"⏺ Files()")
                    elif "action" in str(input_text):
                        import re
                        action_match = re.search(r'"action":\s*"([^"]+)"', str(input_text))
                        path_match = re.search(r'"path":\s*"([^"]+)"', str(input_text))
                        
                        action = action_match.group(1) if action_match else ""
                        path = path_match.group(1) if path_match else ""
                        
                        if action and path:
                            print(f"⏺ {action.title()}({path})")
                        elif action:
                            print(f"⏺ Files({action})")
                        else:
                            print(f"⏺ Files()")
                    else:
                        print(f"⏺ Files()")
                except:
                    print(f"⏺ Files()")
            else:
                print(f"⏺ {tool.title()}()")

        # Show results 
        elif event_type == "tool" and data.get("ok"):
            name = data.get("name", "tool")
            result = data.get("result", "")
            
            # Show meaningful result summary
            if name == "shell":
                lines = result.split('\n') if result else []
                output_lines = [line for line in lines if not line.startswith('command:') and line.strip()]
                if output_lines:
                    first_line = output_lines[0].strip()
                    if len(first_line) > 80:
                        first_line = first_line[:80] + "..."
                    print(f"  ⎿  {first_line}")
                    if len(output_lines) > 1:
                        print(f"     +{len(output_lines)-1} more lines")
                else:
                    print(f"  ⎿  Command completed")
                    
            elif name == "files":
                if "created" in result.lower():
                    print(f"  ⎿  File created")
                elif "updated" in result.lower() or "modified" in result.lower():
                    print(f"  ⎿  File updated")
                elif "content:" in result:
                    lines = result.split('\n')
                    content_lines = [line for line in lines if line.strip() and not line.startswith('content:')]
                    if content_lines:
                        print(f"  ⎿  Read {len(content_lines)} lines")
                    else:
                        print(f"  ⎿  File read")
                else:
                    print(f"  ⎿  Operation completed")
            else:
                # Generic result
                if result and len(result) < 100:
                    print(f"  ⎿  {result}")
                else:
                    print(f"  ⎿  Completed")

        # Show errors clearly
        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"  ⎿  Error: {message}")

        # Show final completion
        elif event_type == "agent_complete":
            print("⏺ Task completed")

        # Debug mode shows internal events
        elif self.debug and event_type not in ["start", "action", "tool", "error", "agent_complete"]:
            print(f"[DEBUG] {event_type}: {data}")
