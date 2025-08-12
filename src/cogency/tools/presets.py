"""Explicit tool composition helpers - no magic, just convenience."""

from .files import Files
from .recall import Recall
from .retrieve import Retrieve
from .scrape import Scrape
from .search import Search
from .shell import Shell


def devops_tools():
    """Development and operations toolset.

    Returns:
        List containing Files, Shell, and Search tools
    """
    return [Files(), Shell(), Search()]


def research_tools():
    """Research and analysis toolset.

    Returns:
        List containing Search, Scrape, and Retrieve tools
    """
    return [Search(), Scrape(), Retrieve()]


def analysis_tools():
    """Document and data analysis toolset.

    Returns:
        List containing Files, Retrieve, and Recall tools
    """
    return [Files(), Retrieve(), Recall()]


def web_tools():
    """Web interaction toolset.

    Returns:
        List containing Search and Scrape tools
    """
    return [Search(), Scrape()]


def filesystem_tools():
    """File system interaction toolset.

    Returns:
        List containing Files and Shell tools
    """
    return [Files(), Shell()]


def memory_tools():
    """Memory and knowledge toolset.

    Returns:
        List containing Retrieve and Recall tools
    """
    return [Retrieve(), Recall()]
