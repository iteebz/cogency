# Centralized Tool Registry
# Tools are auto-discovered from this module

from cogency.tools.base import BaseTool

# Explicit imports for clean API
from cogency.tools.calculator import Calculator
from cogency.tools.code import Code
from cogency.tools.csv import CSV
from cogency.tools.date import Date
from cogency.tools.files import Files
from cogency.tools.http import HTTP
from cogency.tools.recall import Recall
from cogency.tools.scrape import Scrape
from cogency.tools.search import Search
from cogency.tools.shell import Shell
from cogency.tools.sql import SQL
from cogency.tools.time import Time
from cogency.tools.weather import Weather

# Export all tools for easy importing
__all__ = [
    "BaseTool",
    "Calculator",
    "CSV",
    "Code",
    "Date",
    "Files",
    "HTTP",
    "Recall",
    "Scrape",
    "Search",
    "Shell",
    "SQL",
    "Time",
    "Weather",
]
