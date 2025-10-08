from cogency.lib import telemetry


async def _process_stream_event(context, event):
    ev_type = event["type"]
    content = event.get("content")

    if ev_type in {"think", "call", "respond"} and context.metrics and content:
        context.metrics.add_output(content)

    if event:
        telemetry.add_event(context.telemetry_events, event)

    # Minimal implementation to make the test pass
    if ev_type == "end":
        context.complete = True

    if ev_type == "execute" and context.metrics:
        metrics_event = context.metrics.event()
        telemetry.add_event(context.telemetry_events, metrics_event)
        context.metrics.start_step()

    if ev_type == "result" and context.metrics:
        metrics_event = context.metrics.event()
        telemetry.add_event(context.telemetry_events, metrics_event)
        context.metrics.start_step()
