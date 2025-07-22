#!/usr/bin/env python3
"""Data Analysis Pipeline - Fibonacci Analytics Demo"""

import asyncio

from cogency import Agent
from cogency.tools import Code, Files, Shell
from cogency.tools.csv import CSV
from cogency.utils import demo_header, trace_args, stream_response


async def main():
    demo_header("📊 Cogency Data Analysis Demo")

    user = "👤 HUMAN: "
    analyst = "📊 ANALYST: "

    # Create data analysis agent with CSV, code, files, and shell tools
    analysis_agent = Agent(
        "data_analyst",
        identity="expert data analyst and Python developer",
        tools=[CSV(), Code(), Files(), Shell()],
        trace=trace_args(),
    )

    # Complete Data Analysis Pipeline
    query = """Create a complete Fibonacci data analysis pipeline:
    
    1. Generate the first 42 Fibonacci numbers using Python
    2. Save them to a CSV file called 'fibonacci_data.csv' with a single 'number' column
    3. Write a Python analysis script 'analyze_fibonacci.py' that:
       - Reads the CSV data
       - Calculates statistics (sum, average, min, max)
       - Finds patterns (even/odd count, ratios between consecutive numbers)
       - Identifies which numbers are perfect squares
       - Generates a summary report
    4. Run the analysis script and show the results
    5. Create a final summary CSV with the analysis results
    
    Show off the complete workflow from data generation → storage → analysis → reporting.
    """
    print(f"\n{user}{query}\n")
    await stream_response(analysis_agent.stream(query), prefix=analyst)


if __name__ == "__main__":
    asyncio.run(main())