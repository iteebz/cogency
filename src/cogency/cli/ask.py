import asyncio

from .. import Agent


async def run_agent(
    question: str,
    llm: str = "gemini",
    mode: str = "auto",
    user: str = "cli",
    conv: str | None = None,
    agent_path: str | None = None,
    debug: bool = False,
):
    if agent_path:
        import importlib.util
        import sys
        from pathlib import Path

        path = Path(agent_path).resolve()
        if not path.exists():
            print(f"Agent file not found: {agent_path}")
            return

        spec = importlib.util.spec_from_file_location("custom_agent", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["custom_agent"] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "agent"):
            print(f"Error: {agent_path} must define an 'agent' variable")
            return

        agent = module.agent
    else:
        agent = Agent(
            llm=llm,
            mode=mode,
            debug=debug,
        )

    try:
        from .display import Renderer

        async def stream_with_cancellation():
            try:
                async for event in agent(
                    question, user_id=user, conversation_id=conv, chunks=False
                ):
                    yield event
            except asyncio.CancelledError:
                yield {
                    "type": "cancelled",
                    "content": "Task interrupted by user",
                    "timestamp": __import__("time").time(),
                }
                raise

        renderer = Renderer()
        await renderer.render_stream(stream_with_cancellation())

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"Error: {e}")
