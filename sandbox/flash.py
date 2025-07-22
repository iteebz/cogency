import asyncio
from cogency import Agent
from cogency.tools.calculator import Calculator
from cogency.tools.weather import Weather
from cogency.tools.shell import Shell
from cogency.tools.search import Search
from cogency.tools.files import Files
from cogency.tools.code import Code
from cogency.tools.csv import CSV
from cogency.tools.date import Date

from cogency.tools.http import HTTP
from cogency.tools.recall import Recall
from cogency.tools.registry import ToolRegistry
from cogency.tools.scrape import Scrape
from cogency.tools.sql import SQL
from cogency.tools.time import Time

import sys

async def main():
    # Get query from command line arguments or use a default
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is 2 + 2?"

    # Instantiate the agent with no memory and the Calculator tool
    agent = Agent(
        "flash",
        memory=True,
        tools=[Calculator(), Weather(), Shell(), Search(), Files(), Code(), CSV(), Date(), HTTP(), Scrape(), SQL(), Time()],
        verbose=True,
        trace=False
    )

    # Invoke the agent with the provided or default query
    response = await agent.run(query)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
