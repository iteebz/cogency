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
        self.debug = debug

    def handle(self, event):
        if not self.enabled:
            return

        event_type = event["type"]
        data = {**event.get("data", {}), **event}

        if event_type == "start":
            print("[INIT] Starting agent")
            query = data.get("query", "")
            if query:
                print(f"[QUERY] {query}")

        elif event_type == "agent_create" and data.get("status") == "complete":
            name = data.get("name", "")
            print(f"[READY] Agent '{name}'")

        elif event_type == "tool" and data.get("ok"):
            name = data.get("name", "tool")
            duration = data.get("duration")
            if duration:
                print(f"[TOOL] {name} complete ({duration}s)")
            else:
                print(f"[TOOL] {name} complete")

        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"[ERROR] {message}")

        elif event_type == "debug" and self.debug:
            message = data.get("message", "Debug info")
            print(f"[DEBUG] {message}")

        elif event_type == "agent_complete":
            print("[DONE] Agent complete")
