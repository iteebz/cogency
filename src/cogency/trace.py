"""BEAUTIFUL tracing with ZERO ceremony."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


@dataclass
class TraceStep:
    """Single execution step - BEAUTIFUL and simple."""
    node: str
    input: str
    output: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"🔸 {self.node.upper()} [{time_str}] {self.duration_ms:.0f}ms\n   📥 {self.input}\n   📤 {self.output}\n"


@dataclass 
class ExecutionTrace:
    """Complete execution trace with BEAUTIFUL output."""
    steps: List[TraceStep] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    
    def add(self, node: str, input_data: Any, output_data: Any, duration_ms: float):
        """Add step with INTELLIGENT summarization - filter bullshit."""
        # Smart input summary
        if hasattr(input_data, 'current_input'):
            input_str = f"'{input_data.current_input[:50]}...'" if len(input_data.current_input) > 50 else f"'{input_data.current_input}'"
        else:
            input_str = str(input_data)[:60] + "..." if len(str(input_data)) > 60 else str(input_data)
        
        # Smart output summary - FILTER EXECUTION BULLSHIT
        if isinstance(output_data, dict):
            if "result" in output_data:
                output_str = f"Result: {output_data['result']}"
            elif "temperature" in str(output_data):
                output_str = "Weather data retrieved"
            elif "time" in str(output_data):
                output_str = "Time data retrieved"
            elif "error" in output_data:
                output_str = f"Error: {output_data['error']}"
            else:
                output_str = str(output_data)[:60] + "..." if len(str(output_data)) > 60 else str(output_data)
        else:
            output_str = str(output_data)[:60] + "..." if len(str(output_data)) > 60 else str(output_data)
        
        self.steps.append(TraceStep(node, input_str, output_str, duration_ms))
    
    def __str__(self) -> str:
        if not self.steps:
            return "🔍 No steps recorded"
            
        total_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        output = f"\n🚀 EXECUTION TRACE ({total_ms:.0f}ms total)\n" + "="*50 + "\n"
        
        for step in self.steps:
            output += str(step)
            
        return output + "="*50 + f"\n✅ Complete in {total_ms:.0f}ms\n"


def trace_node(func):
    """Simple trace decorator - 6 lines of actual logic."""
    async def wrapper(*args, **kwargs):
        state = args[0] if args else None
        if not (isinstance(state, dict) and state.get("execution_trace")):
            return await func(*args, **kwargs)
            
        start = datetime.now()
        result = await func(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        state["execution_trace"].add(func.__name__, "executed", "completed", duration)
        return result
    
    return wrapper