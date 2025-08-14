"""Working context namespace - task-scoped workspace.

Provides 4-field canonical workspace for natural LLM reasoning flows.
Resolves the 7-field vs 4-field inconsistency by implementing canonical 4-field model.
"""

from typing import Optional, Any


class WorkingContext:
    """Working domain context - task-scoped cognitive workspace."""
    
    def __init__(self, state: Any):
        """Initialize working context.
        
        Args:
            state: Current agent state containing workspace
        """
        self.state = state
    
    async def build(self) -> Optional[str]:
        """Build working context from canonical 4-field workspace.
        
        Uses canonical 4-field model from state.md documentation:
        - objective: "What we're trying to achieve"
        - understanding: "What we've learned and know"  
        - approach: "How we're tackling this systematically"
        - discoveries: "Key insights, patterns, breakthroughs"
        
        Maps current 7-field implementation to canonical 4-field model:
        - objective -> objective (direct)
        - assessment + observations -> understanding (synthesized)
        - approach -> approach (direct)
        - insights + discoveries -> discoveries (synthesized)
        
        Returns:
            Working context string or None
        """
        if not self.state.workspace:
            return None
            
        workspace = self.state.workspace
        parts = []
        
        # Canonical field 1: objective (direct mapping)
        if workspace.objective:
            parts.append(f"OBJECTIVE: {workspace.objective}")
        
        # Canonical field 2: understanding (synthesized from assessment + observations)
        understanding = self._build_understanding(workspace)
        if understanding:
            parts.append(f"UNDERSTANDING: {understanding}")
            
        # Canonical field 3: approach (direct mapping)
        if workspace.approach:
            parts.append(f"APPROACH: {workspace.approach}")
            
        # Canonical field 4: discoveries (synthesized from insights + observations)
        discoveries = self._build_discoveries(workspace)
        if discoveries:
            parts.append(f"DISCOVERIES: {discoveries}")
            
        # Tool execution history - preserved from legacy context() method
        tool_history = self._build_tool_history()
        if tool_history:
            parts.append(tool_history)
        
        return "\n".join(parts) if parts else None
    
    def _build_understanding(self, workspace: Any) -> str:
        """Build understanding field from assessment + observations.
        
        Synthesizes current 7-field assessment and observations into 
        canonical understanding field.
        """
        parts = []
        
        if hasattr(workspace, 'assessment') and workspace.assessment:
            parts.append(workspace.assessment)
            
        if hasattr(workspace, 'observations') and workspace.observations:
            # Last 3 observations for context efficiency
            recent_observations = workspace.observations[-3:]
            if recent_observations:
                parts.append(f"Observed: {'; '.join(recent_observations)}")
                
        return "; ".join(parts) if parts else ""
    
    def _build_discoveries(self, workspace: Any) -> str:
        """Build discoveries field from insights + key observations.
        
        Synthesizes current 7-field insights and key observations into
        canonical discoveries field.
        """
        parts = []
        
        if hasattr(workspace, 'insights') and workspace.insights:
            # Last 3 insights for context efficiency  
            recent_insights = workspace.insights[-3:]
            if recent_insights:
                parts.append(f"Insights: {'; '.join(recent_insights)}")
        
        # Include any breakthrough observations (heuristic: longer observations)
        if hasattr(workspace, 'observations') and workspace.observations:
            breakthrough_observations = [
                obs for obs in workspace.observations[-3:] 
                if len(obs) > 50  # Heuristic for substantial observations
            ]
            if breakthrough_observations:
                parts.append(f"Key findings: {'; '.join(breakthrough_observations)}")
                
        return "; ".join(parts) if parts else ""
    
    def _build_tool_history(self) -> Optional[str]:
        """Build tool execution history - preserved from legacy State.context().
        
        Canonical feedback format with failure analysis.
        """
        if not (
            self.state.execution
            and hasattr(self.state.execution, "completed_calls")
            and self.state.execution.completed_calls
        ):
            return None
            
        parts = ["TOOL EXECUTION HISTORY:"]
        
        for call in self.state.execution.completed_calls[-3:]:  # Last 3 results
            tool_name = call.get("tool", "unknown")
            success = call.get("success", False)
            result = call.get("result", {})

            # Extract meaningful result summary - handle both dict and Result objects
            summary = "completed"  # Default fallback
            if hasattr(result, "get") and isinstance(result, dict):
                if result.get("result"):
                    summary = result["result"]  # e.g., "Created file: hello.py"
                elif result.get("message"):
                    summary = result["message"]
            elif hasattr(result, "success") and hasattr(result, "unwrap"):
                # Handle Result objects from resilient_result
                if result.success:
                    summary = str(result.unwrap())
                else:
                    # Extract failure reason for intelligence
                    summary = str(result.error)
            elif isinstance(result, str):
                summary = result
            elif result:
                summary = str(result)

            status = "✅ SUCCESS" if success else "❌ FAILED"
            parts.append(f"- {tool_name}: {status} - {summary}")

            # Add conflict resolution hints for failures
            if not success and "already exists" in summary.lower():
                parts.append(
                    "  💡 HINT: File conflict detected - consider unique filename or overwrite"
                )
            elif not success and "permission" in summary.lower():
                parts.append(
                    "  💡 HINT: Permission issue - try alternative path or ask for clarification"
                )
            elif not success and "not found" in summary.lower():
                parts.append(
                    "  💡 HINT: Resource not found - verify path or create missing dependencies"
                )
        
        return "\n".join(parts)