"""System Test: Tool Integration Capability Baseline"""

import asyncio
import os

from cogency import BASIC_TOOLS, Agent


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Agent with tool capabilities
    agent = Agent(tools=BASIC_TOOLS)

    # Complex task requiring tools
    result = await agent(
        "Create a Python script that reads a file called data.txt and counts the words in it"
    )

    print(f"Tool-enabled result: {result}")
    print(f"Conversation: {result.conversation_id}")

    # Custom tools example
    from cogency.tools import Tool

    class Calculator(Tool):
        name = "calculate"
        description = "Perform mathematical calculations"

        async def execute(self, expression: str):
            try:
                return eval(expression)  # Note: eval is dangerous in production
            except Exception as e:
                return f"Error: {e}"

    # Agent with custom tool
    calc_agent = Agent(tools=[Calculator()])
    result = await calc_agent("What is 15 * 23 + 7?")
    print(f"Calculator result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
