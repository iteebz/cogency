"""Adaptive reasoning depth control with confidence-based stopping criteria."""
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class StoppingReason(Enum):
    """Reasons for stopping the reasoning loop."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    TIME_LIMIT = "time_limit"
    RESOURCE_LIMIT = "resource_limit"
    DIMINISHING_RETURNS = "diminishing_returns"
    MAX_ITERATIONS = "max_iterations"
    TASK_COMPLETE = "task_complete"
    ERROR_THRESHOLD = "error_threshold"


@dataclass
class ReasoningMetrics:
    """Metrics for tracking reasoning progress and performance."""
    iteration: int = 0
    start_time: float = 0.0
    total_tools_executed: int = 0
    successful_tools: int = 0
    failed_tools: int = 0
    confidence_scores: List[float] = None
    execution_times: List[float] = None
    tool_results_quality: List[float] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = []
        if self.execution_times is None:
            self.execution_times = []
        if self.tool_results_quality is None:
            self.tool_results_quality = []


@dataclass
class StoppingCriteria:
    """Configuration for adaptive stopping criteria."""
    # Confidence-based stopping
    confidence_threshold: float = 0.85
    min_confidence_samples: int = 2
    
    # Time-based limits
    max_reasoning_time: float = 30.0  # seconds
    iteration_timeout: float = 10.0   # seconds per iteration
    
    # Resource limits
    max_iterations: int = 5
    max_tools_per_iteration: int = 10
    max_total_tools: int = 25
    
    # Diminishing returns detection
    improvement_threshold: float = 0.1
    stagnation_iterations: int = 2
    
    # Error handling
    max_consecutive_errors: int = 3
    error_rate_threshold: float = 0.7


class AdaptiveController:
    """Controls reasoning depth with intelligent stopping criteria."""
    
    def __init__(self, criteria: StoppingCriteria = None, max_reasoning_steps: int = None):
        self.criteria = criteria or StoppingCriteria()
        if max_reasoning_steps is not None:
            self.criteria.max_iterations = max_reasoning_steps
        self.metrics = ReasoningMetrics()
        self.iteration_history = []
        self.consecutive_errors = 0
        
    def start_reasoning(self) -> None:
        """Initialize reasoning session."""
        self.metrics = ReasoningMetrics()
        self.metrics.start_time = time.time()
        self.iteration_history = []
        self.consecutive_errors = 0
        
    def step(self) -> None:
        """Increment step counter for testing purposes."""
        self.metrics.iteration += 1
        
    def should_continue_reasoning(self, 
                                execution_results: Dict[str, Any] = None,
                                iteration_start_time: float = None) -> Tuple[bool, StoppingReason]:
        """Determine if reasoning should continue based on adaptive criteria."""
        current_time = time.time()
        
        # Check time limits
        if current_time - self.metrics.start_time > self.criteria.max_reasoning_time:
            return False, StoppingReason.TIME_LIMIT
            
        if iteration_start_time and (current_time - iteration_start_time) > self.criteria.iteration_timeout:
            return False, StoppingReason.TIME_LIMIT
            
        # Check iteration limits
        if self.metrics.iteration >= self.criteria.max_iterations:
            return False, StoppingReason.MAX_ITERATIONS
            
        # Check resource limits
        if self.metrics.total_tools_executed >= self.criteria.max_total_tools:
            return False, StoppingReason.RESOURCE_LIMIT
            
        # Check error threshold
        if self.consecutive_errors >= self.criteria.max_consecutive_errors:
            return False, StoppingReason.ERROR_THRESHOLD
            
        # Check overall error rate
        if self.metrics.total_tools_executed > 0:
            error_rate = self.metrics.failed_tools / self.metrics.total_tools_executed
            if error_rate > self.criteria.error_rate_threshold:
                return False, StoppingReason.ERROR_THRESHOLD
        
        # Check confidence threshold (if we have execution results)
        if execution_results and self._should_stop_on_confidence():
            return False, StoppingReason.CONFIDENCE_THRESHOLD
            
        # Check diminishing returns
        if self._detect_diminishing_returns():
            return False, StoppingReason.DIMINISHING_RETURNS
            
        return True, None
        
    def update_iteration_metrics(self, 
                               execution_results: Dict[str, Any],
                               iteration_time: float) -> None:
        """Update metrics after each reasoning iteration."""
        self.metrics.iteration += 1
        self.metrics.execution_times.append(iteration_time)
        
        # Update tool execution counts
        if execution_results:
            tools_executed = execution_results.get("total_executed", 0)
            successful_count = execution_results.get("successful_count", 0)
            failed_count = execution_results.get("failed_count", 0)
            
            self.metrics.total_tools_executed += tools_executed
            self.metrics.successful_tools += successful_count
            self.metrics.failed_tools += failed_count
            
            # Track consecutive errors
            if failed_count > 0 and successful_count == 0:
                self.consecutive_errors += 1
            else:
                self.consecutive_errors = 0
                
            # Calculate confidence score based on success rate and result quality
            if tools_executed > 0:
                success_rate = successful_count / tools_executed
                confidence = self._calculate_confidence_score(execution_results, success_rate)
                self.metrics.confidence_scores.append(confidence)
                
        # Store iteration summary
        self.iteration_history.append({
            "iteration": self.metrics.iteration,
            "time": iteration_time,
            "tools_executed": execution_results.get("total_executed", 0) if execution_results else 0,
            "success_rate": (execution_results.get("successful_count", 0) / 
                           max(1, execution_results.get("total_executed", 1))) if execution_results else 0,
            "confidence": self.metrics.confidence_scores[-1] if self.metrics.confidence_scores else 0.0
        })
        
    def _calculate_confidence_score(self, execution_results: Dict[str, Any], success_rate: float) -> float:
        """Calculate confidence score based on execution results and success rate."""
        base_confidence = success_rate * 0.7  # 70% weight on success rate
        
        # Add quality factor based on result richness
        quality_factor = 0.0
        if execution_results.get("results"):
            # More tools executed successfully = higher confidence
            quality_factor += min(0.2, len(execution_results["results"]) * 0.05)
            
            # Check for substantial results (longer content = higher quality)
            for result in execution_results["results"]:
                if result.get("result") and len(str(result["result"])) > 50:
                    quality_factor += 0.05
                    
        # Add consistency factor (similar results across tools)
        consistency_factor = 0.1  # Default consistency bonus
        
        return min(1.0, base_confidence + quality_factor + consistency_factor)
        
    def _should_stop_on_confidence(self) -> bool:
        """Check if confidence threshold is met."""
        if len(self.metrics.confidence_scores) < self.criteria.min_confidence_samples:
            return False
            
        # Check if recent confidence scores are consistently high
        recent_scores = self.metrics.confidence_scores[-self.criteria.min_confidence_samples:]
        return all(score >= self.criteria.confidence_threshold for score in recent_scores)
        
    def _detect_diminishing_returns(self) -> bool:
        """Detect if reasoning is showing diminishing returns."""
        if len(self.iteration_history) < self.criteria.stagnation_iterations + 1:
            return False
            
        # Check if confidence improvements are below threshold
        recent_iterations = self.iteration_history[-self.criteria.stagnation_iterations:]
        if not recent_iterations:
            return False
            
        # Calculate improvement trend
        confidences = [it["confidence"] for it in recent_iterations]
        if len(confidences) < 2:
            return False
            
        # Check if improvement is minimal
        max_improvement = max(confidences) - min(confidences)
        return max_improvement < self.criteria.improvement_threshold
        
    def get_adaptive_max_iterations(self, query_complexity: float = 0.5) -> int:
        """Calculate adaptive max iterations based on query complexity."""
        base_iterations = self.criteria.max_iterations
        
        # Simple heuristic: more complex queries get more iterations
        if query_complexity > 0.8:
            return min(base_iterations + 2, 8)
        elif query_complexity > 0.6:
            return min(base_iterations + 1, 6)
        elif query_complexity < 0.3:
            return max(base_iterations - 1, 2)
            
        return base_iterations
        
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of reasoning session."""
        current_time = time.time()
        total_time = current_time - self.metrics.start_time
        
        return {
            "total_iterations": self.metrics.iteration,
            "total_time": total_time,
            "total_tools_executed": self.metrics.total_tools_executed,
            "success_rate": (self.metrics.successful_tools / 
                           max(1, self.metrics.total_tools_executed)),
            "avg_confidence": (sum(self.metrics.confidence_scores) / 
                             len(self.metrics.confidence_scores)) if self.metrics.confidence_scores else 0.0,
            "avg_iteration_time": (sum(self.metrics.execution_times) / 
                                 len(self.metrics.execution_times)) if self.metrics.execution_times else 0.0,
            "consecutive_errors": self.consecutive_errors,
            "iteration_history": self.iteration_history
        }
        
    def get_trace_log(self) -> List[Dict[str, Any]]:
        """Get detailed trace log for introspection."""
        return [
            {
                "timestamp": self.metrics.start_time,
                "event": "reasoning_started",
                "criteria": {
                    "confidence_threshold": self.criteria.confidence_threshold,
                    "max_reasoning_time": self.criteria.max_reasoning_time,
                    "max_iterations": self.criteria.max_iterations,
                    "max_total_tools": self.criteria.max_total_tools
                }
            },
            *[
                {
                    "timestamp": self.metrics.start_time + sum(self.metrics.execution_times[:i+1]),
                    "event": "iteration_completed",
                    "iteration": iteration["iteration"],
                    "duration": iteration["time"],
                    "tools_executed": iteration["tools_executed"],
                    "success_rate": iteration["success_rate"],
                    "confidence": iteration["confidence"]
                }
                for i, iteration in enumerate(self.iteration_history)
            ]
        ]