"""Interactive mode functionality."""

import time


async def interactive_mode(agent, stream=False, debug=False, timing=False) -> None:
    """Enhanced interactive chat mode."""
    session_start = time.time()
    interaction_count = 0

    print("🔬 Cogency Agent" + (" (Debug Mode)" if debug else ""))
    if stream:
        print("📡 Streaming enabled")
    if timing:
        print("⏱️ Timing enabled")
    print("Type 'exit' to quit")
    print("-" * 40)

    while True:
        try:
            prompt = "🧪 > " if debug else "> "
            message = input(f"\n{prompt}").strip()
            if message.lower() in ["exit", "quit"]:
                break
            if message:
                interaction_count += 1
                interaction_start = time.time()

                if debug:
                    print(f"\n--- Interaction {interaction_count} ---")

                if stream:
                    # Streaming mode - simplified without format_stream_event
                    try:
                        async for event in agent.run_stream(message):
                            if hasattr(event, 'content') and event.content:
                                print(event.content, end='', flush=True)
                        print()  # Final newline
                    except AttributeError:
                        # Fallback if streaming not available
                        response, conversation_id = await agent.run(message)
                        print(f"\n{response}")
                else:
                    # Interactive mode uses persistent conversation per session
                    # Use tuple return pattern for consistency
                    response, conversation_id = await agent.run(message)
                    print(f"\n{response}")

                if timing or debug:
                    interaction_time = time.time() - interaction_start
                    print(f"\n⏱️ Duration: {interaction_time:.2f}s")

                    # Show telemetry in debug mode
                    if debug:
                        show_interaction_telemetry(agent)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            if timing or debug:
                total_time = time.time() - session_start
                print(f"📋 Session: {total_time:.1f}s, {interaction_count} interactions")
            break
        except Exception as e:
            print(f"✗ Error: {e}")
            if debug:
                import traceback

                print(f"Debug traceback:\n{traceback.format_exc()}")


def show_interaction_telemetry(agent):
    """Show telemetry for the current interaction."""
    try:
        # Get recent events from agent's logs
        logs = agent.logs(last=10)  # Last 10 events

        if not logs:
            return

        # Show compact event summary
        print("📊 Telemetry:")

        # Count events by type
        event_counts = {}
        tool_events = []
        errors = []

        for event in logs:
            event_type = event.get("type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Collect specific event types
            data = event.get("data", {})
            if event_type == "tool":
                tool_name = data.get("name", "unknown")
                status = data.get("status", "unknown")
                tool_events.append(f"{tool_name}({status})")
            elif event.get("level") == "error" or data.get("status") == "error":
                errors.append(data.get("error", "unknown error"))

        # Display summary
        summary_parts = []
        for event_type, count in event_counts.items():
            if event_type == "agent":
                continue  # Skip verbose agent events
            summary_parts.append(f"{event_type}:{count}")

        if summary_parts:
            print(f"  Events: {', '.join(summary_parts)}")

        if tool_events:
            tools_str = ", ".join(tool_events)
            print(f"  Tools: {tools_str}")

        if errors:
            print(f"  ❌ Errors: {len(errors)}")
            for error in errors[:2]:  # Show first 2 errors
                print(f"    • {error[:50]}...")

    except Exception:
        # Fail silently - don't break interaction for telemetry issues
        pass
