"""CLI interface for Cogency."""

import asyncio

import typer

app = typer.Typer(
    help="""Streaming agents that resume after tool calls.

Direct usage: cogency "question" --new
Conversations continue by default, use --new for fresh start.
Test configurations: --llm (openai/gemini) --mode (resume/replay)"""
)


@app.command()
def run(
    question: str = typer.Argument(..., help="Question for the agent"),
    llm: str = typer.Option("openai", "--llm", help="LLM provider (openai, gemini, anthropic)"),
    mode: str = typer.Option("auto", "--mode", help="Stream mode (auto, resume, replay)"),
    new: bool = typer.Option(False, "--new", help="Start fresh conversation (default: continue)"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Ask the agent a question (continues conversation by default)."""
    from .ask import run_agent

    asyncio.run(
        run_agent(
            question,
            llm=llm,
            mode=mode,
            new=new,
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
def last(conv_id: str = typer.Argument(None, help="Conversation ID")):
    """Show last conversation flow."""
    from .debug import show_conversation

    show_conversation(conv_id)


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
    import shutil
    from pathlib import Path

    try:
        cogency_dir = Path(".cogency")  # Don't call get_cogency_dir() - it creates the dir!
        if cogency_dir.exists():
            shutil.rmtree(cogency_dir)
            print(f"✓ Deleted {cogency_dir}")
        else:
            print("✓ No .cogency folder to delete")
    except Exception as e:
        print(f"✗ Error during nuke: {e}")
        raise typer.Exit(1) from e


def main():
    """CLI entry point."""
    try:
        app()
    except Exception as e:
        print(f"CLI Error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
