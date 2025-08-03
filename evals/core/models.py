"""Core evaluation data models."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FailureType(str, Enum):
    """Classification of evaluation failures."""

    LOGIC = "logic"  # Model wrong answer
    RATE_LIMIT = "rate_limit"  # API quota/throttling
    TIMEOUT = "timeout"  # Network/processing timeout
    ERROR = "error"  # Unexpected exception
    SECURITY = "security"  # Security violation detected
    PERFORMANCE = "performance"  # Performance/resource issue


class SubCaseResult(BaseModel):
    """Result of a single test case within an evaluation."""

    name: str
    passed: bool
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    failure_type: Optional[FailureType] = None


class EvalResult(BaseModel):
    """Result of running an evaluation."""

    name: str
    passed: bool
    score: float  # 0.0 to 1.0
    duration: float  # seconds
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    failure_type: Optional[FailureType] = None
    retries: int = 0
    metadata: Dict[str, Any] = {}
    sub_cases: List[SubCaseResult] = []
