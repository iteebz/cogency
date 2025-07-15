"""Infinite loop detection system for cognitive reasoning patterns."""

import time
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from cogency.types import ExecutionTrace


class LoopType(Enum):
    """Types of loops that can be detected."""
    REASONING_CYCLE = "reasoning_cycle"
    TOOL_EXECUTION_CYCLE = "tool_execution_cycle"
    STATE_OSCILLATION = "state_oscillation"
    CONTEXT_REPETITION = "context_repetition"
    DECISION_FLIP = "decision_flip"


@dataclass
class LoopPattern:
    """Represents a detected loop pattern."""
    loop_type: LoopType
    cycle_length: int
    repetition_count: int
    first_occurrence: float
    last_occurrence: float
    confidence: float
    signature: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class LoopDetectionConfig:
    """Configuration for loop detection thresholds."""
    max_identical_states: int = 3
    max_tool_retries: int = 3
    max_reasoning_cycles: int = 5
    decision_flip_threshold: int = 2
    time_window_seconds: float = 30.0
    similarity_threshold: float = 0.85
    
    # Adaptive thresholds based on query complexity
    complexity_multiplier: float = 1.5
    max_adaptive_iterations: int = 8


class LoopDetector:
    """Detects infinite loops and circular reasoning patterns."""
    
    def __init__(self, config: LoopDetectionConfig = None):
        self.config = config or LoopDetectionConfig()
        
        # State tracking
        self.state_history: deque = deque(maxlen=50)
        self.tool_execution_history: deque = deque(maxlen=100)
        self.reasoning_history: deque = deque(maxlen=100)
        self.decision_history: deque = deque(maxlen=20)
        
        # Loop detection caches
        self.detected_loops: List[LoopPattern] = []
        self.state_signatures: Dict[str, List[float]] = defaultdict(list)
        self.tool_signatures: Dict[str, List[float]] = defaultdict(list)
        
        # Timing
        self.start_time: float = time.time()
        self.last_check_time: float = self.start_time
        
    def reset(self):
        """Reset detector for new reasoning session."""
        self.state_history.clear()
        self.tool_execution_history.clear()
        self.reasoning_history.clear()
        self.decision_history.clear()
        self.detected_loops.clear()
        self.state_signatures.clear()
        self.tool_signatures.clear()
        self.start_time = time.time()
        self.last_check_time = self.start_time
    
    def add_reasoning_step(self, iteration: int, llm_response: str, 
                          tool_calls: Optional[List[str]] = None,
                          execution_results: Optional[Dict] = None):
        """Add a reasoning step for loop detection."""
        timestamp = time.time()
        
        # Create reasoning signature
        reasoning_sig = self._create_reasoning_signature(
            iteration, llm_response, tool_calls, execution_results
        )
        
        self.reasoning_history.append({
            "timestamp": timestamp,
            "iteration": iteration,
            "signature": reasoning_sig,
            "llm_response": llm_response[:200],  # Truncate for memory
            "tool_calls": tool_calls or [],
            "execution_results": execution_results or {}
        })
        
        # Check for reasoning cycles
        self._check_reasoning_cycles()
    
    def add_tool_execution(self, tool_name: str, args: Dict, 
                          result: Any, success: bool):
        """Add tool execution for loop detection."""
        timestamp = time.time()
        
        # Create tool signature
        tool_sig = self._create_tool_signature(tool_name, args, result, success)
        
        self.tool_execution_history.append({
            "timestamp": timestamp,
            "tool_name": tool_name,
            "signature": tool_sig,
            "args": args,
            "success": success,
            "result_summary": str(result)[:100] if result else None
        })
        
        # Track tool-specific patterns
        self.tool_signatures[tool_name].append(timestamp)
        
        # Check for tool execution cycles
        self._check_tool_cycles()
    
    def add_state_change(self, state: Dict, trace: ExecutionTrace):
        """Add state change for loop detection."""
        timestamp = time.time()
        
        # Create state signature from key components
        state_sig = self._create_state_signature(state, trace)
        
        # Handle Context object vs dict for state history
        context = state.get("context", {})
        if hasattr(context, 'messages'):
            message_count = len(context.messages)
        else:
            message_count = len(context.get("messages", []))
        
        self.state_history.append({
            "timestamp": timestamp,
            "signature": state_sig,
            "trace_length": len(trace.entries),
            "context_messages": message_count,
            "last_node": trace.entries[-1]["node"] if trace.entries else None
        })
        
        # Track state signatures
        self.state_signatures[state_sig].append(timestamp)
        
        # Check for state oscillation
        self._check_state_oscillation()
    
    def add_decision(self, decision_type: str, details: Dict):
        """Add decision for flip detection."""
        timestamp = time.time()
        
        decision_sig = self._create_decision_signature(decision_type, details)
        
        self.decision_history.append({
            "timestamp": timestamp,
            "type": decision_type,
            "signature": decision_sig,
            "details": details
        })
        
        # Check for decision flips
        self._check_decision_flips()
    
    def check_for_loops(self, current_iteration: int = None, 
                       complexity_factor: float = 1.0) -> List[LoopPattern]:
        """Comprehensive loop check with adaptive thresholds."""
        self.last_check_time = time.time()
        
        # Adjust thresholds based on complexity
        adjusted_config = self._adjust_thresholds_for_complexity(complexity_factor)
        
        # Run all detection methods
        self._check_reasoning_cycles(adjusted_config)
        self._check_tool_cycles(adjusted_config)
        self._check_state_oscillation(adjusted_config)
        self._check_decision_flips(adjusted_config)
        self._check_context_repetition()
        
        # Filter recent loops
        recent_loops = [
            loop for loop in self.detected_loops
            if loop.last_occurrence > self.last_check_time - self.config.time_window_seconds
        ]
        
        return recent_loops
    
    def is_loop_detected(self, loop_types: List[LoopType] = None) -> bool:
        """Check if any loops of specified types are detected."""
        if not loop_types:
            return len(self.detected_loops) > 0
        
        return any(
            loop.loop_type in loop_types 
            for loop in self.detected_loops
        )
    
    def get_loop_summary(self) -> Dict[str, Any]:
        """Get summary of detected loops."""
        if not self.detected_loops:
            return {"loops_detected": False, "total_loops": 0}
        
        loop_counts = defaultdict(int)
        max_confidence = 0.0
        
        for loop in self.detected_loops:
            loop_counts[loop.loop_type.value] += 1
            max_confidence = max(max_confidence, loop.confidence)
        
        return {
            "loops_detected": True,
            "total_loops": len(self.detected_loops),
            "loop_types": dict(loop_counts),
            "max_confidence": max_confidence,
            "detection_time": self.last_check_time - self.start_time
        }
    
    def _create_reasoning_signature(self, iteration: int, llm_response: str, 
                                  tool_calls: Optional[List[str]], 
                                  execution_results: Optional[Dict]) -> str:
        """Create signature for reasoning step."""
        # Combine key elements for signature
        elements = [
            f"iter_{iteration}",
            self._normalize_text(llm_response),
            "_".join(sorted(tool_calls or [])),
            str(execution_results.get("success", False) if execution_results else False)
        ]
        
        combined = "|".join(elements)
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _create_tool_signature(self, tool_name: str, args: Dict, 
                             result: Any, success: bool) -> str:
        """Create signature for tool execution."""
        # Normalize args for consistent hashing
        normalized_args = self._normalize_dict(args)
        
        elements = [
            tool_name,
            str(normalized_args),
            str(success)
        ]
        
        combined = "|".join(elements)
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _create_state_signature(self, state: Dict, trace: ExecutionTrace) -> str:
        """Create signature for state."""
        # Extract key state components
        context = state.get("context", {})
        
        # Handle Context object vs dict
        if hasattr(context, 'messages'):
            message_count = len(context.messages)
            current_input = context.current_input[:100] if context.current_input else ""
        else:
            message_count = len(context.get("messages", []))
            current_input = context.get("current_input", "")[:100]
        
        elements = [
            str(len(trace.entries)),
            str(message_count),
            current_input,
            trace.entries[-1]["node"] if trace.entries else "empty"
        ]
        
        combined = "|".join(elements)
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _create_decision_signature(self, decision_type: str, details: Dict) -> str:
        """Create signature for decision."""
        normalized_details = self._normalize_dict(details)
        
        combined = f"{decision_type}|{normalized_details}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _check_reasoning_cycles(self, config: LoopDetectionConfig = None):
        """Check for reasoning cycles."""
        config = config or self.config
        
        if len(self.reasoning_history) < 3:
            return
        
        # Look for repeated reasoning signatures
        signatures = [entry["signature"] for entry in self.reasoning_history]
        cycles = self._find_cycles(signatures)
        
        for cycle_length, repetitions in cycles.items():
            if repetitions >= config.max_reasoning_cycles:
                loop_pattern = LoopPattern(
                    loop_type=LoopType.REASONING_CYCLE,
                    cycle_length=cycle_length,
                    repetition_count=repetitions,
                    first_occurrence=self.reasoning_history[0]["timestamp"],
                    last_occurrence=self.reasoning_history[-1]["timestamp"],
                    confidence=min(1.0, repetitions / config.max_reasoning_cycles),
                    signature=signatures[-cycle_length:][0],
                    evidence=[f"Repeated reasoning pattern with {repetitions} cycles"]
                )
                
                self.detected_loops.append(loop_pattern)
    
    def _check_tool_cycles(self, config: LoopDetectionConfig = None):
        """Check for tool execution cycles."""
        config = config or self.config
        
        # Check each tool individually
        for tool_name, timestamps in self.tool_signatures.items():
            if len(timestamps) >= config.max_tool_retries:
                # Check if executions are too frequent
                recent_executions = [
                    t for t in timestamps 
                    if t > time.time() - config.time_window_seconds
                ]
                
                if len(recent_executions) >= config.max_tool_retries:
                    loop_pattern = LoopPattern(
                        loop_type=LoopType.TOOL_EXECUTION_CYCLE,
                        cycle_length=1,
                        repetition_count=len(recent_executions),
                        first_occurrence=recent_executions[0],
                        last_occurrence=recent_executions[-1],
                        confidence=min(1.0, len(recent_executions) / config.max_tool_retries),
                        signature=tool_name,
                        evidence=[f"Tool '{tool_name}' executed {len(recent_executions)} times"]
                    )
                    
                    self.detected_loops.append(loop_pattern)
    
    def _check_state_oscillation(self, config: LoopDetectionConfig = None):
        """Check for state oscillation."""
        config = config or self.config
        
        # Look for repeated state signatures
        for signature, timestamps in self.state_signatures.items():
            if len(timestamps) >= config.max_identical_states:
                recent_timestamps = [
                    t for t in timestamps
                    if t > time.time() - config.time_window_seconds
                ]
                
                if len(recent_timestamps) >= config.max_identical_states:
                    loop_pattern = LoopPattern(
                        loop_type=LoopType.STATE_OSCILLATION,
                        cycle_length=1,
                        repetition_count=len(recent_timestamps),
                        first_occurrence=recent_timestamps[0],
                        last_occurrence=recent_timestamps[-1],
                        confidence=min(1.0, len(recent_timestamps) / config.max_identical_states),
                        signature=signature,
                        evidence=[f"State repeated {len(recent_timestamps)} times"]
                    )
                    
                    self.detected_loops.append(loop_pattern)
    
    def _check_decision_flips(self, config: LoopDetectionConfig = None):
        """Check for decision flips."""
        config = config or self.config
        
        if len(self.decision_history) < 4:
            return
        
        # Look for alternating decisions
        recent_decisions = list(self.decision_history)[-6:]  # Last 6 decisions
        
        if len(recent_decisions) >= 4:
            # Check for A-B-A-B pattern
            signatures = [d["signature"] for d in recent_decisions]
            
            flip_count = 0
            for i in range(len(signatures) - 1):
                if signatures[i] != signatures[i + 1]:
                    flip_count += 1
            
            if flip_count >= config.decision_flip_threshold * 2:
                loop_pattern = LoopPattern(
                    loop_type=LoopType.DECISION_FLIP,
                    cycle_length=2,
                    repetition_count=flip_count // 2,
                    first_occurrence=recent_decisions[0]["timestamp"],
                    last_occurrence=recent_decisions[-1]["timestamp"],
                    confidence=min(1.0, flip_count / (config.decision_flip_threshold * 2)),
                    signature="_".join(signatures[:2]),
                    evidence=[f"Decision flipped {flip_count} times"]
                )
                
                self.detected_loops.append(loop_pattern)
    
    def _check_context_repetition(self):
        """Check for context repetition patterns."""
        if len(self.reasoning_history) < 5:
            return
        
        # Look for repeated context patterns in LLM responses
        responses = [entry["llm_response"] for entry in self.reasoning_history]
        
        # Simple similarity check
        for i in range(len(responses) - 2):
            for j in range(i + 2, len(responses)):
                similarity = self._calculate_similarity(responses[i], responses[j])
                
                if similarity > self.config.similarity_threshold:
                    loop_pattern = LoopPattern(
                        loop_type=LoopType.CONTEXT_REPETITION,
                        cycle_length=j - i,
                        repetition_count=2,
                        first_occurrence=self.reasoning_history[i]["timestamp"],
                        last_occurrence=self.reasoning_history[j]["timestamp"],
                        confidence=similarity,
                        signature=f"context_repeat_{i}_{j}",
                        evidence=[f"Context similarity: {similarity:.2f}"]
                    )
                    
                    self.detected_loops.append(loop_pattern)
                    break
    
    def _find_cycles(self, sequence: List[str]) -> Dict[int, int]:
        """Find cycles in a sequence."""
        cycles = {}
        
        for cycle_length in range(1, len(sequence) // 2 + 1):
            repetitions = 0
            
            for i in range(len(sequence) - cycle_length):
                if sequence[i:i + cycle_length] == sequence[i + cycle_length:i + 2 * cycle_length]:
                    repetitions += 1
            
            if repetitions > 0:
                cycles[cycle_length] = repetitions
        
        return cycles
    
    def _adjust_thresholds_for_complexity(self, complexity_factor: float) -> LoopDetectionConfig:
        """Adjust thresholds based on query complexity."""
        adjusted_config = LoopDetectionConfig()
        
        # Increase thresholds for complex queries
        if complexity_factor > 0.7:
            adjusted_config.max_reasoning_cycles = int(
                self.config.max_reasoning_cycles * self.config.complexity_multiplier
            )
            adjusted_config.max_tool_retries = int(
                self.config.max_tool_retries * self.config.complexity_multiplier
            )
        
        return adjusted_config
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent comparison."""
        return text.lower().strip()[:200]  # Truncate and normalize
    
    def _normalize_dict(self, d: Dict) -> str:
        """Normalize dictionary for consistent hashing."""
        if not d:
            return "{}"
        
        # Sort keys and create consistent string representation
        sorted_items = sorted(d.items())
        return str(sorted_items)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        # Simple token-based similarity
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0