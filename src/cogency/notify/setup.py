"""Setup utilities for v2 notification system."""


from .formatters import CLIFormatter, EmojiFormatter, Formatter, JSONFormatter


def setup_formatter(notify: bool = True, debug: bool = False, style: str = None) -> Formatter:
    """Setup v2 notification formatter - zero ceremony with smart defaults."""
    if style:
        # Explicit style override
        return {
            "cli": CLIFormatter(),
            "emoji": EmojiFormatter(),
            "json": JSONFormatter(),
            "silent": Formatter(),  # Base class is silent
        }.get(style, EmojiFormatter())

    # Smart defaults based on flags
    if not notify:
        return Formatter()  # Silent
    elif debug:
        return CLIFormatter()  # CLI formatter shows more detail
    else:
        return EmojiFormatter()  # Default emoji formatter
