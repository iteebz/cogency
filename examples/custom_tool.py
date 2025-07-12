#!/usr/bin/env python3
"""
This example walks through implementing a custom tool using the BaseTool interface.

Key concepts:
1. Inherit from BaseTool
2. Implement run(), get_schema(), and get_usage_examples()
3. Add to agent's tools list
4. Agent automatically discovers and uses it

Run with: poetry run python custom_tool.py
"""

import math
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
from cogency.agent import Agent
from cogency.llm import GeminiLLM


class CalculatorTool(BaseTool):
    """Example custom tool that performs basic arithmetic operations.
    
    This tool demonstrates the complete BaseTool interface implementation
    and serves as a template for creating your own tools.
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="A calculator tool that can perform basic arithmetic operations (add, subtract, multiply, divide) and calculate square roots.",
        )

    def run(self, operation: str, x1: float = None, x2: float = None) -> Dict[str, Any]:
        """Execute the calculator operation.
        
        Args:
            operation: The mathematical operation to perform
            x1: First operand (required for all operations)
            x2: Second operand (required for binary operations)
            
        Returns:
            Dict containing the result or error information
        """
        if operation == "add":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for addition."}
            result = x1 + x2
        elif operation == "subtract":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for subtraction."}
            result = x1 - x2
        elif operation == "multiply":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for multiplication."}
            result = x1 * x2
        elif operation == "divide":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for division."}
            if x2 == 0:
                return {"error": "Cannot divide by zero"}
            result = x1 / x2
        elif operation == "square_root":
            if x1 is None:
                return {"error": "x1 is required for square_root."}
            if x1 < 0:
                return {"error": "Cannot calculate square root of a negative number."}
            result = math.sqrt(x1)
        else:
            return {"error": f"Unsupported operation: {operation}"}
        
        return {"result": result}

    def get_schema(self) -> str:
        """Return tool call schema for LLM formatting.
        
        This tells the LLM how to format tool calls for this tool.
        """
        return "calculator(operation='add|subtract|multiply|divide|square_root', x1=float, x2=float)"

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls for LLM guidance.
        
        These examples help the LLM understand how to use the tool properly.
        """
        return [
            "calculator(operation='add', x1=5, x2=3)",
            "calculator(operation='multiply', x1=7, x2=8)",
            "calculator(operation='square_root', x1=9)",
        ]


def main():
    """Demo the custom calculator tool."""
    print("=== Custom Tool Example ===")
    print("Building and using a custom calculator tool with cogency\n")
    
    # Test the tool directly first
    print("🔧 Testing tool directly...")
    calc = CalculatorTool()
    result = calc.run("add", 15, 27)
    print(f"15 + 27 = {result['result']}")
    
    # Now test with agent
    print("\n🤖 Testing with agent...")
    
    # Set your API key
    api_key = "AIzaSyA7QHtdxjtKwpGvNEgtBsyt7kCVpedFNNQ"
    llm = GeminiLLM(api_keys=api_key)  # New cleaner interface
    
    # Create agent with our custom tool
    agent = Agent(
        name="CalculatorAgent",
        llm=llm,
        tools=[CalculatorTool()]  # Just add your tool to the list!
    )
    
    # Test queries
    queries = [
        "What is 123 + 456?",
        "Calculate the square root of 144",
        "What is 15 multiplied by 8?"
    ]
    
    for query in queries:
        print(f"\n> {query}")
        try:
            result = agent.run(query, enable_trace=True, print_trace=True)
            print(f"💡 {result['response']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎉 Custom Tool Integration Complete!")
    print("="*50)
    print("Key Takeaways:")
    print("1. Inherit from BaseTool")
    print("2. Implement run(), get_schema(), get_usage_examples()")
    print("3. Add to agent.tools list")
    print("4. Agent automatically discovers and uses it!")
    print("\nThat's it! Build any tool you can imagine.")


if __name__ == "__main__":
    main()