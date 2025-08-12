"""Tool action formatting for console display."""

from .input_parser import extract_command, extract_file_operation, extract_query, extract_url


def format_tool_action(tool: str, input_text: str) -> str:
    """Format tool action for console display."""
    formatters = {
        "shell": _format_shell,
        "files": _format_files,
        "scrape": _format_scrape,
        "search": _format_search,
    }

    formatter = formatters.get(tool, _format_generic)
    return formatter(tool, input_text)


def _format_shell(tool: str, input_text: str) -> str:
    """Format shell command display."""
    cmd = extract_command(input_text)
    return f"Shell({cmd})" if cmd else "Shell()"


def _format_files(tool: str, input_text: str) -> str:
    """Format file operation display."""
    return extract_file_operation(input_text)


def _format_scrape(tool: str, input_text: str) -> str:
    """Format scrape URL display."""
    url = extract_url(input_text)
    return f"Scrape({url})" if url else "Scrape()"


def _format_search(tool: str, input_text: str) -> str:
    """Format search query display."""
    query = extract_query(input_text)
    return f"Search({query})" if query else "Search()"


def _format_generic(tool: str, input_text: str) -> str:
    """Format generic tool display."""
    # Try to extract any meaningful content
    if isinstance(input_text, str) and input_text.strip():
        content = input_text.strip()[:50]  # Limit length
        if content and not content.startswith("{"):
            return f"{tool.title()}({content})"
    return f"{tool.title()}()"
