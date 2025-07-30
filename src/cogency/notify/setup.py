"""Setup utilities for v2 notification system."""


from .formatters import CLIFormatter, EmojiFormatter, Formatter, JSONFormatter


def setup_formatter(notify: bool = True, debug: bool = False, style: str = None) -> Formatter:
    """Setup v2 notification formatter - zero ceremony with smart defaults."""
    if style is not None:
        style = str(style).strip().lower()  # Ensure it's a clean lowercase string
        # Explicit style override
        if style == "cli":
            return CLIFormatter()
        elif style == "emoji":
            return EmojiFormatter()
        elif style == "json":
            return JSONFormatter()
        elif style == "silent":
            return Formatter()
        else:
            return EmojiFormatter()  # Fallback for unknown explicit styles

    # Smart defaults based on flags
    if not notify:
        return Formatter()  # Silent
    elif debug:
        return CLIFormatter()  # CLI formatter shows more detail
    else:
        return EmojiFormatter()  # Default emoji formatter
