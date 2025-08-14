"""Action namespace - decisions to results transformation.

Core action primitive: execute decisions and produce results.
Supports the 'act' step in agent execution loops.
"""

from .execute import act

__all__ = ["act"]
