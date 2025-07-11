# Agent Architecture Overview

This document defines the default reasoning loop used by Cogency agents. It balances robustness, extensibility, and transparency for multi-step tasks involving tool use, memory, and iterative reflection.

## Core Agent Loop

The agent operates through a series of distinct steps to achieve its goals:

1. **Plan:** The agent first decides on a high-level strategy. It determines if a direct response is sufficient or if tools are needed to accomplish the task.
2. **Reason (Loop):** If tools are required, the agent iteratively determines which tool to use and how to use it. This involves selecting the right tool and preparing its inputs.
3. **Act:** The agent executes the chosen tool with the prepared inputs.
4. **Reflect (Loop):** After an action, the agent evaluates the tool's output. It decides if the task is complete, if further actions are needed, or if any errors occurred that require re-planning.
5. **Respond:** Finally, the agent formulates a clear, conversational answer for the user, incorporating any information gathered or actions performed.