"""Minimal ANSI color codes for terminal output."""


class C:
    R = "\033[0m"

    gray = "\033[90m"
    cyan = "\033[36m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    blue = "\033[34m"
    magenta = "\033[35m"

    keyword = "\033[35m"
    string = "\033[32m"
    comment = "\033[90m"

    @staticmethod
    def strip(text: str) -> str:
        import re

        return re.sub(r"\033\[[0-9;]+m", "", text)
