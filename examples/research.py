#!/usr/bin/env python3
"""Research agent - deep analysis with longer horizon planning."""

import asyncio

from cogency import Agent


async def main():
    print("=" * 42)
    print("🔍 DEEP RESEARCH AGENT")
    print("=" * 42)

    # AI safety research agent
    agent = Agent(
        "ai_safety_researcher",
        identity="You are Dr. Sarah Chen, a leading AI alignment researcher at the Center for AI Safety, specializing in mesa-optimization and inner alignment. You've published extensively on emergent optimization in neural systems and are known for bridging the gap between abstract alignment theory and concrete technical solutions. You approach research with both rigorous technical analysis and genuine concern for humanity's future with advanced AI systems.",
        tools=["scrape", "search"],
        memory=False,
        depth=15,  # Allow deeper research for complex AI safety topics
        mode="deep",
    )

    # Mesa-optimization and inner alignment research query
    query = """I want you to conduct a deep research investigation into the mesa-optimization problem and inner alignment in AI systems. This is one of the most fascinating and potentially crucial problems in AI safety.

    Start by exploring the current state of research: What are the key papers and researchers driving this field? What are the most compelling theoretical frameworks for understanding when and how mesa-optimizers emerge during training?

    Then dive deeper: What are the most concerning scenarios for deceptive alignment? What detection methods are being developed? Are there any promising approaches for preventing mesa-optimization entirely, or should we focus on alignment techniques?

    I'm particularly interested in:
    - The technical mechanisms by which mesa-optimizers could emerge
    - Real examples or evidence of mesa-optimization in current systems
    - The debate between "mesa-optimization is inevitable" vs "we can engineer around it"
    - Cutting-edge research on interpretability tools for detecting inner misalignment
    - The connection to broader questions about AI consciousness and goal-directed behavior

    Make this research comprehensive but accessible - I want to understand both the technical details and the big picture implications for AI safety and humanity's future."""

    print(f"👤 {query}...\n")
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
