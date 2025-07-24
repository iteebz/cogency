#!/usr/bin/env python3
"""ML Engineering agent - neural network training pipeline."""

import asyncio

from cogency import Agent
from cogency.tools import Code, Files, Shell
from cogency.utils.cli import trace_args


async def main():
    print("=" * 42 + "\n")
    print("🧠 MACHINE LEARNING ENGINEER")
    print("=" * 42 + "\n")

    # Create ML engineering agent
    agent = Agent(
        "ml_engineer",
        identity="You are Dr. Elena Rodriguez, a senior ML engineer at DeepMind with expertise in neural architecture design and training optimization. You've built production ML systems at scale and are known for creating elegant, efficient training pipelines. You approach problems with both theoretical rigor and practical engineering excellence, always focusing on reproducible results and clean code architecture.",
        tools=[Code(), Files(), Shell()],
        memory=False,
        max_iterations=25,  # ML projects may need more iterations
        trace=trace_args(),
    )

    # Challenge the agent with a comprehensive ML pipeline
    query = """Build a complete neural network training pipeline from scratch that demonstrates modern ML engineering practices.

    Requirements:
    - Generate synthetic dataset with interesting patterns
    - Design and implement a neural network architecture (PyTorch or TensorFlow)
    - Create a proper training loop with metrics logging
    - Implement data preprocessing and validation splits
    - Add model evaluation and visualization of results
    - Include proper project structure with requirements.txt
    - Write tests to verify the pipeline works
    - Demonstrate the trained model making predictions

    Focus on clean, production-ready ML code that showcases best practices in model development, not just a toy example. Show your expertise in building robust ML systems."""

    print("🚀 Challenge: Build a complete neural network training pipeline!")

    # Stream the response
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
