"""CLI interface for Cogency."""

import asyncio
import json

import typer

app = typer.Typer(
    name="cogency", help="Streaming agents", no_args_is_help=False
)


@app.command()
def ask(
    question: str = typer.Argument(help="Question for the agent"),
    llm: str = typer.Option("gemini", "--llm", help="LLM provider (openai, gemini, anthropic)"),
    mode: str = typer.Option("auto", "--mode", help="Stream mode (auto, resume, replay)"),
    user: str = typer.Option("ask_user", "--user", help="User identity"),
    instructions: str = typer.Option(None, "--instructions", help="Custom agent instructions"),
    max_iterations: int = typer.Option(10, "--max-iterations", help="Maximum reasoning iterations"),
    no_tools: bool = typer.Option(False, "--no-tools", help="Disable tools"),
    no_profile: bool = typer.Option(False, "--no-profile", help="Disable user memory"),
    no_sandbox: bool = typer.Option(False, "--no-sandbox", help="Disable security sandbox"),
    new: bool = typer.Option(False, "--new", help="Start fresh conversation"),
    debug: bool = typer.Option(False, "--debug", help="Show execution traces"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed debug events"),
):
    """Ask the agent a question."""
    from .ask import run_agent

    asyncio.run(
        run_agent(
            question,
            llm,
            mode,
            user,
            instructions,
            max_iterations,
            no_tools,
            no_profile,
            no_sandbox,
            new,
            debug,
            verbose,
        )
    )


@app.command()
def last(conv_id: str = typer.Argument(None, help="Conversation ID")):
    """Show last conversation flow."""
    from .debug import show_conversation

    show_conversation(conv_id)


@app.command()
def context(conv_id: str = typer.Argument(None, help="Conversation ID")):
    """Show assembled context."""
    from .debug import show_context

    show_context(conv_id)


@app.command()
def db():
    """Database inspection."""
    from .debug import query_main

    query_main()


@app.command()
def stats():
    """Database statistics."""
    from .admin import show_stats

    show_stats()


@app.command()
def users():
    """User profiles."""
    from .admin import users_main

    users_main()


@app.command()
def profile():
    """Show user profile."""
    import asyncio
    from ..context.profile import get

    async def _show_profile():
        user_id = "ask_user"  # Default CLI user
        user_profile = await get(user_id)
        if user_profile:
            print(json.dumps(user_profile))
        else:
            print("{}")

    asyncio.run(_show_profile())


nuke_app = typer.Typer(help="Nuclear cleanup commands")


@nuke_app.command("all")
def nuke_all():
    """Delete all data (with confirmation)."""
    from .admin import nuke_everything

    nuke_everything()


@nuke_app.command("sandbox")
def nuke_sandbox_cmd():
    """Delete sandbox only."""
    from .admin import nuke_sandbox

    nuke_sandbox()


@nuke_app.command("db")
def nuke_db_cmd():
    """Delete database only."""
    from .admin import nuke_db

    nuke_db()


app.add_typer(nuke_app, name="nuke")


def main():
    """CLI entry point with smart argument handling."""
    import sys
    
    # If first arg doesn't match a command, treat as direct question
    if len(sys.argv) > 1 and sys.argv[1] not in [
        "ask", "last", "context", "db", "stats", "users", "profile", "nuke", "--help", "-h"
    ]:
        # Insert 'ask' command for direct questions
        sys.argv.insert(1, "ask")
    
    app()


if __name__ == "__main__":
    main()
