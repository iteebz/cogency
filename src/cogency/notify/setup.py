"""Setup utilities for v2 notification system."""


from .formatters import CLIFormatter, EmojiFormatter, Formatter, JSONFormatter


def setup_formatter(style: str = "emoji") -> Formatter:
    """Setup v2 notification formatter - zero ceremony."""
    return {
        "cli": CLIFormatter(),
        "emoji": EmojiFormatter(),
        "json": JSONFormatter(),
        "silent": Formatter(),  # Base class is silent
    }.get(style, EmojiFormatter())
