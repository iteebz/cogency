# State System Implementation

**Technical implementation guide for Cogency's v1.0.0 state system.**

## Overview

The state system implements a three-layer architecture:

1. **Execution State** - Loop control and tool orchestration
2. **Reasoning Context** - Structured cognitive state  
3. **Situated Memory** - Persistent user understanding

## Implementation Details

### Execution Flow

```python
# 1. Agent Initialization
state = AgentState(query="user query", user_id="alice", user_profile=loaded_profile)

# 2. Reasoning Loop
while state.execution.should_continue():
    # Generate reasoning prompt with situated context
    prompt = reasoning_context(state, tools)
    
    # LLM reasoning with context injection
    reasoning_result = await llm.run(prompt)
    
    # Update state from reasoning
    state.update_from_reasoning(reasoning_result)
    
    # Execute tools
    if state.execution.pending_calls:
        tool_results = await execute_tools(state.execution.pending_calls)
        state.execution.finish_tools(tool_results)
    
    state.execution.advance_iteration()

# 3. Memory Update
interaction_data = {
    "query": state.execution.query,
    "response": state.execution.response,
    "success": bool(state.execution.response),
    "mode_used": state.execution.mode,
    "iterations": state.execution.iteration
}

updated_profile = await synthesizer.update_impression(state.execution.user_id, interaction_data)
```

### State Updates

**From LLM Reasoning:**
```python
def update_from_reasoning(self, reasoning_data: Dict[str, Any]) -> None:
    # Record thinking
    thinking = reasoning_data.get("thinking", "")
    tool_calls = reasoning_data.get("tool_calls", [])
    
    if thinking:
        self.reasoning.record_thinking(thinking, tool_calls)
    
    # Set tool calls for execution
    if tool_calls:
        self.execution.set_tool_calls(tool_calls)
    
    # Update reasoning context
    context_updates = reasoning_data.get("context_updates", {})
    if context_updates:
        if "goal" in context_updates:
            self.reasoning.goal = context_updates["goal"]
        if "strategy" in context_updates:
            self.reasoning.strategy = context_updates["strategy"]
        if "insights" in context_updates:
            for insight in context_updates["insights"]:
                self.reasoning.learn(insight)
    
    # Handle direct response
    if "response" in reasoning_data:
        self.execution.response = reasoning_data["response"]
```

### Memory Synthesis

**Insight Extraction:**
```python
async def extract_insights(llm, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    query = interaction_data.get("query", "")
    response = interaction_data.get("response", "")
    success = interaction_data.get("success", True)
    
    prompt = f"""Extract user insights from this interaction:
    User Query: {query}
    Agent Response: {response}
    Success: {success}
    
    Return JSON with insights about preferences, goals, expertise, etc."""
    
    result = await llm.run([{"role": "user", "content": prompt}])
    if result.success:
        parsed = _parse_json(result.data)
        return parsed.data if parsed.success else {}
    return {}
```

**Profile Synthesis:**
```python
async def _synthesize_profile(self, profile: UserProfile, recent_interaction: Dict[str, Any]) -> UserProfile:
    current_context = compress(profile)
    
    prompt = f"""Synthesize evolved user profile:
    
    CURRENT PROFILE:
    {current_context}
    
    RECENT INTERACTION:
    Query: {recent_interaction.get('query', '')}
    Success: {recent_interaction.get('success', True)}
    
    Create refined profile that consolidates understanding over time..."""
    
    result = await self.llm.run([{"role": "user", "content": prompt}])
    if result.success:
        parsed = _parse_json(result.data)
        if parsed.success:
            self._apply_synthesis_to_profile(profile, parsed.data)
            profile.synthesis_version += 1
    
    return profile
```

### Context Compression

**Reasoning Context:**
```python
def compress_for_context(self, max_tokens: int = 1000) -> str:
    sections = []
    
    if self.goal:
        sections.append(f"GOAL: {self.goal}")
    
    if self.strategy:
        sections.append(f"STRATEGY: {self.strategy}")
    
    if self.facts:
        recent_facts = list(self.facts.items())[-5:]
        facts_str = "; ".join(f"{k}: {v}" for k, v in recent_facts)
        sections.append(f"FACTS: {facts_str}")
    
    if self.insights:
        recent_insights = self.insights[-3:]
        insights_str = "; ".join(recent_insights)
        sections.append(f"INSIGHTS: {insights_str}")
    
    if self.thoughts:
        last_thought = self.thoughts[-1]
        sections.append(f"LAST THINKING: {last_thought['thinking'][:200]}")
    
    result = "\n".join(sections)
    return result[:max_tokens] if len(result) > max_tokens else result
```

**User Profile:**
```python
def compress(profile: UserProfile, max_tokens: int = 800) -> str:
    sections = []
    
    if profile.communication_style:
        sections.append(f"COMMUNICATION: {profile.communication_style}")
    
    if profile.goals:
        goals_str = "; ".join(profile.goals[-3:])
        sections.append(f"CURRENT GOALS: {goals_str}")
    
    if profile.preferences:
        prefs_items = list(profile.preferences.items())[-5:]
        prefs_str = ", ".join(f"{k}: {v}" for k, v in prefs_items)
        sections.append(f"PREFERENCES: {prefs_str}")
    
    # ... other sections
    
    result = "\n".join(sections)
    return result[:max_tokens] if len(result) > max_tokens else result
```

### Storage Implementation

**Atomic File Operations:**
```python
async def save(self, state_key: str, state: AgentState) -> bool:
    try:
        state_path = self._get_state_path(state_key)
        temp_path = state_path.with_suffix(".tmp")
        
        # Prepare serializable state data
        state_data = {
            "state": {
                "execution": asdict(state.execution),
                "reasoning": asdict(state.reasoning),
                "user_profile": serialize_profile(state.user) if state.user else None,
            },
            "process_id": self.process_id,
        }
        
        # Atomic write: temp file + rename
        with open(temp_path, "w") as f:
            flock(f.fileno(), LOCK_EX)  # Exclusive lock
            json.dump(state_data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
            flock(f.fileno(), LOCK_UN)  # Release lock
        
        # Atomic rename
        temp_path.rename(state_path)
        return True
        
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        return False
```

### Bounded Growth Prevention

**Reasoning:**
```python
def learn(self, insight: str) -> None:
    if insight and insight.strip() and insight not in self.insights:
        self.insights.append(insight.strip())
        # Prevent unbounded growth - keep last 10
        if len(self.insights) > 10:
            self.insights = self.insights[-10:]

def record_thinking(self, thinking: str, tool_calls: List[Dict[str, Any]]) -> None:
    thought = {
        "thinking": thinking,
        "tool_calls": tool_calls,
        "timestamp": datetime.now().isoformat()
    }
    self.thoughts.append(thought)
    # Keep last 5 thoughts for context
    if len(self.thoughts) > 5:
        self.thoughts = self.thoughts[-5:]
```

**UserProfile:**
```python
def update_from_interaction(self, interaction_insights: Dict[str, Any]) -> None:
    # Add new goals (bounded)
    if "goals" in interaction_insights:
        for goal in interaction_insights["goals"]:
            if goal not in self.goals:
                self.goals.append(goal)
        if len(self.goals) > 10:
            self.goals = self.goals[-10:]
    
    # Update expertise areas
    if "expertise" in interaction_insights:
        for area in interaction_insights["expertise"]:
            if area not in self.expertise_areas:
                self.expertise_areas.append(area)
        if len(self.expertise_areas) > 15:
            self.expertise_areas = self.expertise_areas[-15:]
```

### Error Recovery

**Graceful Degradation:**
```python
async def load(self, user_id: str) -> Optional[AgentState]:
    if not self.enabled:
        return None
    
    try:
        state_key = self._state_key(user_id)
        data = await self.store.load(state_key)
        
        if not data:
            return None
        
        # Handle different data formats (backwards compatibility)
        if "state" in data:
            state_dict = data["state"]  # Legacy format
        else:
            state_dict = data  # New format
        
        # Reconstruct AgentState...
        
    except Exception as e:
        # Graceful degradation - for debugging
        print(f"Debug: Load failed with {e}")
        return None
```

**Tool Execution Fallbacks:**
```python
def should_continue(self) -> bool:
    """Determine if reasoning loop should continue."""
    return (
        self.iteration < self.max_iterations
        and not self.response
        and not self.stop_reason
        and bool(self.pending_calls)
    )
```

## Testing Strategy

**Unit Tests:**
- State transitions and updates
- Memory compression algorithms
- Serialization/deserialization
- Bounded growth enforcement

**Integration Tests:**
- End-to-end memory lifecycle
- Cross-session persistence  
- Multi-user isolation
- Error recovery scenarios

**Contract Tests:**
- API interface compliance
- Tool result format validation
- LLM response structure
- State reconstruction accuracy

---

*Implementation guide for Cogency v1.0.0 state system*