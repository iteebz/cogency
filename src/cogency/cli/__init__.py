import asyncio

import typer

app = typer.Typer(
    help="""Streaming agents that resume after tool calls.

Direct usage: cogency "question"
Stateless by default. Use --conv for multi-turn conversations.
Test configurations: --llm (openai/gemini/anthropic) --mode (auto/resume/replay)"""
)


@app.command()
def run(
    question: str = typer.Argument(..., help="Question for the agent"),
    llm: str = typer.Option("openai", "--llm", help="LLM provider (openai, gemini, anthropic)"),
    mode: str = typer.Option("auto", "--mode", help="Stream mode (auto, resume, replay)"),
    user: str = typer.Option("cli", "--user", help="User ID for profile learning"),
    conv: str = typer.Option(None, "--conv", help="Conversation ID for multi-turn context"),
    agent: str = typer.Option(
        None, "--agent", help="Path to custom agent module (e.g., myagent.py)"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Ask the agent a question (stateless by default)."""
    from .ask import run_agent

    asyncio.run(
        run_agent(
            question,
            llm=llm,
            mode=mode,
            user=user,
            conv=conv,
            agent_path=agent,
            debug=debug,
        )
    )


@app.command()
def context(
    target: str = typer.Argument("last", help="Target: 'system' or conversation ID"),
):
    """Show assembled context."""
    from .debug import show_context, show_system_prompt

    if target == "system":
        show_system_prompt()
    else:
        conversation_id = None if target == "last" else target
        show_context(conversation_id)


@app.command()
def conv(conv_id: str = typer.Argument(..., help="Conversation ID to view")):
    """View conversation history."""
    from .conversation import show_conversation

    asyncio.run(show_conversation(conv_id))


@app.command()
def stats():
    """Database statistics."""
    from .admin import show_stats

    show_stats()


@app.command()
def users(user_id: str = typer.Argument(None, help="Specific user ID to show (optional)")):
    """User profiles."""
    from .admin import show_user, show_users

    if user_id:
        show_user(user_id)
    else:
        show_users()


@app.command()
def nuke():
    """Delete .cogency folder completely."""
    from .admin import nuke as nuke_impl

    try:
        nuke_impl()
    except Exception as e:
        print(f"✗ Error during nuke: {e}")
        raise typer.Exit(1) from e


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
