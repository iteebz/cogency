"""Integration hooks for loop detection in reasoning nodes."""

import time
from typing import Dict, List, Optional, Any
from .loop_detection import LoopDetector, LoopType, LoopDetectionConfig
from cogency.common.types import ExecutionTrace, AgentState


class ReasoningLoopGuard:
    """Integrates loop detection into reasoning workflows."""
    
    def __init__(self, config: LoopDetectionConfig = None):
        self.detector = LoopDetector(config)
        self.session_active = False
        self.complexity_factor = 1.0
        self.last_warning_time = 0
        self.warning_cooldown = 5.0  # seconds
    
    def start_reasoning_session(self, query: str, tools: List = None):
        """Start new reasoning session with loop detection."""
        self.detector.reset()
        self.session_active = True
        
        # Estimate complexity for adaptive thresholds
        self.complexity_factor = self._estimate_complexity(query, tools)
        
        return {
            "session_id": id(self),
            "complexity_factor": self.complexity_factor,
            "started_at": time.time()
        }
    
    def check_reasoning_step(self, state: AgentState, iteration: int, 
                           llm_response: str, tool_calls: List[str] = None,
                           execution_results: Dict = None) -> Dict[str, Any]:
        """Check for loops after reasoning step."""
        if not self.session_active:
            return {"safe": True, "loops": []}
        
        # Add to detector
        self.detector.add_reasoning_step(
            iteration=iteration,
            llm_response=llm_response,
            tool_calls=tool_calls,
            execution_results=execution_results
        )
        
        # Add state change
        trace = state.get("trace")
        if trace:
            self.detector.add_state_change(state, trace)
        
        # Check for loops
        loops = self.detector.check_for_loops(
            current_iteration=iteration,
            complexity_factor=self.complexity_factor
        )
        
        # Determine safety
        dangerous_loops = [
            loop for loop in loops
            if loop.loop_type in [LoopType.REASONING_CYCLE, LoopType.STATE_OSCILLATION]
            and loop.confidence > 0.8
        ]
        
        is_safe = len(dangerous_loops) == 0
        
        # Add warning to trace if loops detected
        if dangerous_loops and trace:
            self._add_loop_warning_to_trace(trace, dangerous_loops)
        
        return {
            "safe": is_safe,
            "loops": loops,
            "dangerous_loops": dangerous_loops,
            "should_stop": len(dangerous_loops) > 0,
            "loop_summary": self.detector.get_loop_summary()
        }
    
    def check_tool_execution(self, tool_name: str, args: Dict, 
                           result: Any, success: bool) -> Dict[str, Any]:
        """Check for tool execution loops."""
        if not self.session_active:
            return {"safe": True, "loops": []}
        
        # Add to detector
        self.detector.add_tool_execution(tool_name, args, result, success)
        
        # Check for tool loops
        loops = self.detector.check_for_loops(complexity_factor=self.complexity_factor)
        
        tool_loops = [
            loop for loop in loops
            if loop.loop_type == LoopType.TOOL_EXECUTION_CYCLE
            and loop.signature == tool_name
        ]
        
        is_safe = len(tool_loops) == 0
        
        return {
            "safe": is_safe,
            "loops": tool_loops,
            "should_stop": len(tool_loops) > 0,
            "tool_retry_count": len(self.detector.tool_signatures.get(tool_name, []))
        }
    
    def check_decision_pattern(self, decision_type: str, details: Dict) -> Dict[str, Any]:
        """Check for decision flip patterns."""
        if not self.session_active:
            return {"safe": True, "loops": []}
        
        # Add to detector
        self.detector.add_decision(decision_type, details)
        
        # Check for decision loops
        loops = self.detector.check_for_loops(complexity_factor=self.complexity_factor)
        
        decision_loops = [
            loop for loop in loops
            if loop.loop_type == LoopType.DECISION_FLIP
        ]
        
        is_safe = len(decision_loops) == 0
        
        return {
            "safe": is_safe,
            "loops": decision_loops,
            "should_stop": len(decision_loops) > 0
        }
    
    def end_reasoning_session(self) -> Dict[str, Any]:
        """End reasoning session and return final summary."""
        if not self.session_active:
            return {"session_active": False}
        
        self.session_active = False
        
        final_summary = self.detector.get_loop_summary()
        final_summary["session_ended_at"] = time.time()
        
        return final_summary
    
    def get_emergency_stop_recommendation(self) -> Dict[str, Any]:
        """Get emergency stop recommendation based on current loops."""
        if not self.session_active:
            return {"recommend_stop": False, "reason": "No active session"}
        
        loops = self.detector.check_for_loops(complexity_factor=self.complexity_factor)
        
        # High-confidence dangerous loops
        critical_loops = [
            loop for loop in loops
            if loop.confidence > 0.9 and loop.loop_type in [
                LoopType.REASONING_CYCLE,
                LoopType.STATE_OSCILLATION,
                LoopType.TOOL_EXECUTION_CYCLE
            ]
        ]
        
        if critical_loops:
            return {
                "recommend_stop": True,
                "reason": "Critical loop detected",
                "critical_loops": critical_loops,
                "confidence": max(loop.confidence for loop in critical_loops)
            }
        
        # Too many loops of any type
        if len(loops) > 5:
            return {
                "recommend_stop": True,
                "reason": "Too many concurrent loops",
                "loop_count": len(loops),
                "loop_types": [loop.loop_type.value for loop in loops]
            }
        
        return {"recommend_stop": False, "reason": "No critical loops detected"}
    
    def _estimate_complexity(self, query: str, tools: List = None) -> float:
        """Estimate query complexity for adaptive thresholds."""
        complexity = 0.0
        
        # Length factor
        complexity += min(0.3, len(query) / 200)
        
        # Keyword complexity
        complex_keywords = ['analyze', 'compare', 'evaluate', 'comprehensive', 'detailed']
        simple_keywords = ['what', 'when', 'where', 'define']
        
        for keyword in complex_keywords:
            if keyword in query.lower():
                complexity += 0.1
        
        for keyword in simple_keywords:
            if keyword in query.lower():
                complexity -= 0.05
        
        # Tool count factor
        if tools:
            complexity += min(0.2, len(tools) / 10)
        
        return max(0.1, min(1.0, complexity))
    
    def _add_loop_warning_to_trace(self, trace: ExecutionTrace, loops: List):
        """Add loop warning to execution trace."""
        current_time = time.time()
        
        # Rate limit warnings
        if current_time - self.last_warning_time < self.warning_cooldown:
            return
        
        self.last_warning_time = current_time
        
        loop_types = [loop.loop_type.value for loop in loops]
        max_confidence = max(loop.confidence for loop in loops)
        
        warning_msg = f"Loop detected: {', '.join(loop_types)} (confidence: {max_confidence:.2f})"
        
        trace.add(
            "loop_guard",
            warning_msg,
            data={"loops": [{"type": loop.loop_type.value, "confidence": loop.confidence} for loop in loops]},
            explanation="Loop detection system identified potential infinite reasoning patterns"
        )


# Decorator for automatic loop detection
def with_loop_detection(config: LoopDetectionConfig = None):
    """Decorator to add loop detection to reasoning functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract state from args
            state = args[0] if args else kwargs.get('state')
            
            if not state or not isinstance(state, dict):
                return await func(*args, **kwargs)
            
            # Create loop guard
            guard = ReasoningLoopGuard(config)
            
            # Start session
            context = state.get("context", {})
            query = getattr(context, 'current_input', '') if hasattr(context, 'current_input') else context.get('current_input', '')
            tools = state.get("selected_tools", [])
            
            guard.start_reasoning_session(query, tools)
            
            try:
                # Execute original function
                result = await func(*args, **kwargs)
                
                # Check final state
                final_check = guard.get_emergency_stop_recommendation()
                
                if final_check["recommend_stop"]:
                    # Add warning to result
                    if "trace" in result:
                        result["trace"].add(
                            "loop_guard",
                            f"Session ended with loop concerns: {final_check['reason']}",
                            data=final_check
                        )
                
                return result
                
            finally:
                guard.end_reasoning_session()
        
        return wrapper
    return decorator