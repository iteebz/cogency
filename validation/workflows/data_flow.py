#!/usr/bin/env python3
"""Multi-tool workflow: Complex data processing pipeline."""

import asyncio
import os
import tempfile

from cogency import Agent
from cogency.tools import Calculator, Code, Files


async def main():
    print("📊➡️🚀➡️🧮 DATA PROCESSING WORKFLOW")
    print("=" * 45 + "\n")

    # Create temp directory for data files
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Agent with file ops, code execution, and calculator
            agent = Agent(
                "data_processor",
                identity="data analyst who processes files, runs code, and calculates results",
                tools=[Files(), Code(), Calculator()],
                memory=False,
                depth=10,  # Complex workflow needs iterations
                trace=False,
            )

            # Complex data processing workflow
            query = """I need to process some sales data:

            1. Create a CSV file called 'sales.csv' with this data:
               product,quantity,price
               apples,12,1.25
               oranges,8,0.85
               bananas,15,0.65

            2. Write Python code to read the CSV and calculate:
               - Total revenue for each product
               - Overall total revenue
               - Average price per unit

            3. Use the calculator to verify the total revenue calculation

            Please execute this complete data processing pipeline."""

            print("🎯 WORKFLOW QUERY:")
            print(f"{query}\n")
            print("=" * 45)

            try:
                result = await agent.run(query)
                print(f"\n✅ WORKFLOW RESULT:\n{result}")
            except Exception as e:
                print(f"\n❌ WORKFLOW ERROR: {e}")

        finally:
            os.chdir(original_cwd)

    print("\n" + "=" * 45)
    print("🎵 Expected workflow:")
    print("  1. Create CSV file with sales data")
    print("  2. Write Python code to process the data")
    print("  3. Execute code to analyze sales")
    print("  4. Use calculator to verify totals")
    print("  5. Present complete analysis")
    print("=" * 45)


if __name__ == "__main__":
    asyncio.run(main())
