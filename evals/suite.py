"""Comprehensive eval suite - test all of cogency's capabilities."""

from error_recovery import ErrorRecoveryEval
from memory_persistence import MemoryPersistenceEval
from multi_provider import MultiProviderEval
from reasoning import ReasoningEval
from reasoning_chain import ReasoningChainEval
from tool_usage import ToolUsageEval

# Beautiful eval suite - covers cogency's breadth
COGENCY_SUITE = [
    ReasoningEval,  # Basic mathematical reasoning
    ToolUsageEval,  # Tool integration and usage
    MemoryPersistenceEval,  # Memory across interactions
    ReasoningChainEval,  # Multi-step logical reasoning
    ErrorRecoveryEval,  # Error handling and resilience
    MultiProviderEval,  # Cross-provider consistency
]

# Quick suite for rapid testing
QUICK_SUITE = [
    ReasoningEval,
    ToolUsageEval,
]

# Provider-specific suite
PROVIDER_SUITE = [
    MultiProviderEval,
]
