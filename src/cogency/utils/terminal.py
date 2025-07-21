"""Terminal output utilities - clean, rich, magical demo UX."""
import asyncio
from typing import AsyncIterator, List, Optional
from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown

console = Console()


async def stream_response(stream: AsyncIterator[str], char_delay: float = 0.005, rich: bool = True, prefix: str = "🤖: ") -> str:
    """Stream response with smooth character-by-character output.
    
    Args:
        stream: Async iterator of string chunks
        char_delay: Delay between characters for smooth typing effect
        rich: Whether to render with rich formatting
        prefix: Custom prefix for agent responses (default: "🤖: ")
        
    Returns:
        Complete response text
    """
    # Print prefix first
    if rich:
        console.print(prefix, end="", highlight=False)
    else:
        print(prefix, end="", flush=True)
    
    full_response = ""
    
    async for chunk in stream:
        full_response += chunk
        for char in chunk:
            if rich:
                console.print(char, end="", highlight=False)
            else:
                print(char, end="", flush=True)
            if char_delay > 0:
                await asyncio.sleep(char_delay)
    
    return full_response.strip()


def demo_header(title: str, width: int = 35) -> None:
    """Print clean demo header with emoji and separator."""
    console.print("\n[dim]" + "=" * width + "[/dim]")
    console.print(f"[bold deep_pink4]{title}[/bold deep_pink4]")
    console.print("[dim]" + "=" * width + "[/dim]")


def separator(width: int = 50) -> None:
    """Print separator line."""
    console.print("\n[dim]" + "=" * width + "[/dim]")


def section(title: str) -> None:
    """Print section header."""
    console.print(f"\n[bold yellow]--- {title} ---[/bold yellow]")


def showcase(title: str, items: List[str]) -> None:
    """Print demo showcase section with bullet points.
    
    Args:
        title: Showcase section title (e.g. "🎯 This demo showcases:")
        items: List of features/capabilities to highlight
    """
    console.print(f"\n[bold green]{title}[/bold green]")
    for item in items:
        console.print(f"   [dim]•[/dim] [cyan]{item}[/cyan]")


def tips(items: List[str]) -> None:
    """Print tips section with bullet points."""
    console.print("\n[bold magenta]💡 Tips:[/bold magenta]")
    for tip in items:
        console.print(f"   [dim]•[/dim] [bright_white]{tip}[/bright_white]")


def info(message: str) -> None:
    """Print info message with emoji."""
    console.print(f"[bold blue]💡 {message}[/bold blue]")


def config_item(name: str, description: str) -> None:
    """Print configuration item."""
    console.print(f"[bold white]{name}:[/bold white] [cyan]{description}[/cyan]")


def config_code(code: str) -> None:
    """Print configuration code block."""
    console.print(f"[dim]{code}[/dim]")