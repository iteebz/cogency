"""Agent execution steps.

This module provides the core execution pipeline steps that agents use to process
requests. The steps are:

- triage: Routing, memory extraction, tool filtering
- reason: Focused reasoning and decision making
- act: Tool execution based on reasoning decisions
- respond: Response generation and formatting
- synthesize: Memory consolidation and profile updates

Note: Step functions are typically used via Agent.run() rather than directly.
The _setup_steps function handles production composition with observability,
resilience, and checkpointing capabilities.
"""

# Internal only - no public exports

__all__ = []
