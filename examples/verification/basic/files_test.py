#!/usr/bin/env python3
"""Basic file operations tool verification - file system interaction."""

import asyncio
import tempfile
import os

from cogency import Agent
from cogency.tools import Files


async def main():
    print("📁 FILES VERIFICATION")
    print("=" * 30 + "\n")

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}\n")
        
        # Change to temp directory for clean testing
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Simple agent with file operations
            agent = Agent(
                "files_tester",
                identity="file management assistant that handles file operations safely",
                tools=[Files()],
                memory=False,
                max_iterations=5,
                trace=False,  # Clean output
            )

            # Test file operations
            queries = [
                "Create a file called 'test.txt' with content 'Hello Cogency!'",
                "Read the contents of test.txt",
                "List all files in the current directory",
                "Create a directory called 'subdir' and put a file 'nested.txt' inside it",
            ]

            for i, query in enumerate(queries, 1):
                print(f"Test {i}: {query}")
                try:
                    result = await agent.run(query)
                    print(f"Result: {result}\n")
                except Exception as e:
                    print(f"Error: {e}\n")
                await asyncio.sleep(0.5)

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    print("✅ Files verification complete!")


if __name__ == "__main__":
    asyncio.run(main())