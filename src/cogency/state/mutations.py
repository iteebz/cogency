"""State mutations - CANONICAL Three-Horizon Split-State Model pure functions."""

from datetime import datetime
from typing import Any, Dict, List

from resilient_result import unwrap

from .agent import State
from .autosave import autosave

# CANONICAL: Horizon 3 Operations (ExecutionState - runtime-only, never persisted)


def add_message(state: State, role: str, content: str) -> None:
    """Add message to Horizon 3 - ExecutionState (runtime-only)."""
    state.execution.messages.append(
        {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
    )
    autosave(state)  # Saves Horizon 1 + 2, NOT Horizon 3


def set_tool_calls(state: State, calls: List[Dict[str, Any]]) -> None:
    """Set pending tool calls in Horizon 3 - ExecutionState (runtime-only)."""
    validated_calls = []
    for call in calls:
        if isinstance(call, dict) and "name" in call:
            validated_call = {"name": str(call["name"]), "args": call.get("args", {})}
            if "id" in call:
                validated_call["id"] = call["id"]
            validated_calls.append(validated_call)

    if state.execution.pending_calls != validated_calls:
        state.execution.pending_calls = validated_calls
        autosave(state)  # Saves Horizon 1 + 2, NOT Horizon 3


def finish_tools(state: State, results: List[Dict[str, Any]]) -> None:
    """Process completed tool results in Horizon 3 - ExecutionState (runtime-only)."""
    state.execution.completed_calls.extend(results)
    state.execution.pending_calls.clear()
    state.execution.iterations_without_tools = 0

    # Add tool results to conversation
    if results:
        tool_summary = []
        for result in results:
            tool_name = result.get("name", "unknown")
            result_obj = result.get("result")

            if result_obj is None:
                tool_summary.append(f"Tool '{tool_name}' failed: No result")
                continue

            try:
                unwrapped_result = unwrap(result_obj)
                if isinstance(unwrapped_result, dict) and "stdout" in unwrapped_result:
                    output = unwrapped_result["stdout"].strip()
                    if output:
                        tool_summary.append(f"Tool '{tool_name}': {output}")
                    else:
                        tool_summary.append(f"Tool '{tool_name}': success")
                else:
                    tool_summary.append(f"Tool '{tool_name}': success")
            except Exception as e:
                error_msg = str(e) if str(e) else "Unknown error"
                tool_summary.append(f"Tool '{tool_name}' failed: {error_msg}")

        if tool_summary:
            add_message(state, "system", "Tool results:\n" + "\n".join(tool_summary))
    else:
        autosave(state)


def advance_iteration(state: State) -> None:
    """Advance Horizon 3 - ExecutionState iteration (runtime-only)."""
    state.execution.iteration += 1
    autosave(state)  # Saves Horizon 1 + 2, NOT Horizon 3


def should_continue(state: State) -> bool:
    """Check if execution should continue - Horizon 3 logic."""
    return (
        state.execution.iteration < state.execution.max_iterations
        and not state.execution.response
        and not state.execution.stop_reason
        and bool(state.execution.pending_calls)
    )


# CANONICAL: Horizon 2 Operations (Workspace - task-scoped persistence)


def learn_insight(state: State, insight: str) -> None:
    """Add insight to Horizon 2 - Workspace (task-scoped, persisted)."""
    if insight and insight.strip() and insight not in state.workspace.insights:
        state.workspace.insights.append(insight.strip())
        # Bounded growth prevention
        if len(state.workspace.insights) > 10:
            state.workspace.insights = state.workspace.insights[-10:]
        autosave(state)


def update_workspace_facts(state: State, key: str, value: Any) -> None:
    """Update structured knowledge in Horizon 2 - Workspace (task-scoped, persisted)."""
    if key and key.strip():
        old_value = state.workspace.facts.get(key)
        if old_value != value:
            state.workspace.facts[key] = value
            # Bounded growth prevention
            if len(state.workspace.facts) > 20:
                oldest_keys = list(state.workspace.facts.keys())[:-20]
                for old_key in oldest_keys:
                    del state.workspace.facts[old_key]
            autosave(state)


def record_thinking(state: State, thinking: str, tool_calls: List[Dict[str, Any]]) -> None:
    """Record reasoning step in Horizon 2 - Workspace (task-scoped, persisted)."""
    thought = {
        "thinking": thinking,
        "tool_calls": tool_calls,
        "timestamp": datetime.now().isoformat(),
    }
    state.workspace.thoughts.append(thought)
    # Bounded growth prevention
    if len(state.workspace.thoughts) > 5:
        state.workspace.thoughts = state.workspace.thoughts[-5:]
    autosave(state)


def update_workspace_assessment(state: State, assessment: str) -> None:
    """Update task assessment in Horizon 2 - Workspace (task-scoped, persisted)."""
    if assessment and state.workspace.assessment != assessment:
        state.workspace.assessment = assessment
        autosave(state)


def update_workspace_approach(state: State, approach: str) -> None:
    """Update task approach in Horizon 2 - Workspace (task-scoped, persisted)."""
    if approach and state.workspace.approach != approach:
        state.workspace.approach = approach
        autosave(state)


def add_observation(state: State, observation: str) -> None:
    """Add observation to Horizon 2 - Workspace (task-scoped, persisted)."""
    if observation and observation.strip() and observation not in state.workspace.observations:
        state.workspace.observations.append(observation.strip())
        # Bounded growth prevention
        if len(state.workspace.observations) > 15:
            state.workspace.observations = state.workspace.observations[-15:]
        autosave(state)


# CANONICAL: Horizon 1 Operations (UserProfile - persistent across sessions)


def update_user_preference(state: State, key: str, value: Any) -> None:
    """Update user preference in Horizon 1 - UserProfile (permanent, persisted)."""
    if key and key.strip():
        old_value = state.profile.preferences.get(key)
        if old_value != value:
            state.profile.preferences[key] = value
            state.profile.last_updated = datetime.now()
            autosave(state)


def add_user_goal(state: State, goal: str) -> None:
    """Add goal to Horizon 1 - UserProfile (permanent, persisted)."""
    if goal and goal.strip() and goal not in state.profile.goals:
        state.profile.goals.append(goal.strip())
        # Bounded growth prevention
        if len(state.profile.goals) > 10:
            state.profile.goals = state.profile.goals[-10:]
        state.profile.last_updated = datetime.now()
        autosave(state)


def add_user_expertise(state: State, expertise: str) -> None:
    """Add expertise to Horizon 1 - UserProfile (permanent, persisted)."""
    if expertise and expertise.strip() and expertise not in state.profile.expertise_areas:
        state.profile.expertise_areas.append(expertise.strip())
        # Bounded growth prevention
        if len(state.profile.expertise_areas) > 15:
            state.profile.expertise_areas = state.profile.expertise_areas[-15:]
        state.profile.last_updated = datetime.now()
        autosave(state)


def update_communication_style(state: State, style: str) -> None:
    """Update communication style in Horizon 1 - UserProfile (permanent, persisted)."""
    if style and state.profile.communication_style != style:
        state.profile.communication_style = style
        state.profile.last_updated = datetime.now()
        autosave(state)


def update_user_project(state: State, project_name: str, description: str) -> None:
    """Update project in Horizon 1 - UserProfile (permanent, persisted)."""
    if project_name and project_name.strip():
        old_desc = state.profile.projects.get(project_name)
        if old_desc != description:
            state.profile.projects[project_name] = description
            # Bounded growth prevention
            if len(state.profile.projects) > 10:
                oldest_keys = list(state.profile.projects.keys())[:-10]
                for old_key in oldest_keys:
                    del state.profile.projects[old_key]
            state.profile.last_updated = datetime.now()
            autosave(state)


# CANONICAL: Cross-Horizon Operations


def update_from_reasoning(state: State, reasoning_data: Dict[str, Any]) -> None:
    """Update state from LLM reasoning response - dispatches to appropriate horizons."""
    if isinstance(reasoning_data, list):
        if reasoning_data and isinstance(reasoning_data[0], dict):
            reasoning_data = reasoning_data[0]
        else:
            return

    # Record thinking in Horizon 2 (Workspace)
    thinking = reasoning_data.get("thinking", "")
    tool_calls = reasoning_data.get("tool_calls", [])
    if thinking:
        record_thinking(state, thinking, tool_calls)

    # Set tool calls in Horizon 3 (ExecutionState)
    if tool_calls:
        set_tool_calls(state, tool_calls)

    changed = False

    # Update workspace from reasoning (Horizon 2)
    workspace_updates = reasoning_data.get("workspace_update", {})
    if workspace_updates and "objective" in workspace_updates:
        if state.workspace.objective != workspace_updates["objective"]:
            state.workspace.objective = workspace_updates["objective"]
            changed = True
        if "assessment" in workspace_updates:
            update_workspace_assessment(state, workspace_updates["assessment"])
        if "approach" in workspace_updates:
            update_workspace_approach(state, workspace_updates["approach"])
        if "insights" in workspace_updates and isinstance(workspace_updates["insights"], list):
            for insight in workspace_updates["insights"]:
                learn_insight(state, insight)
        if "observations" in workspace_updates and isinstance(
            workspace_updates["observations"], list
        ):
            for observation in workspace_updates["observations"]:
                add_observation(state, observation)

    # Backward compatibility with old context_updates
    context_updates = reasoning_data.get("context_updates", {})
    if (
        context_updates
        and "insights" in context_updates
        and isinstance(context_updates["insights"], list)
    ):
        for insight in context_updates["insights"]:
            learn_insight(state, insight)

    # Handle response in Horizon 3 (ExecutionState)
    if "response" in reasoning_data:
        response_content = reasoning_data["response"]
        if (
            not tool_calls or not response_content
        ) and state.execution.response != response_content:
            state.execution.response = response_content
            changed = True

    # Handle mode switching in Horizon 3 (ExecutionState)
    mode_field = reasoning_data.get("switch_mode") or reasoning_data.get("switch_to")
    switch_why = reasoning_data.get("switch_why", "")
    if mode_field and switch_why:
        import contextlib

        from cogency.steps.reason.modes import ModeController

        with contextlib.suppress(ValueError):
            current_mode = str(state.execution.mode)
            if ModeController.should_switch(
                current_mode,
                mode_field,
                switch_why,
                state.execution.iteration,
                state.execution.max_iterations,
            ):
                ModeController.execute_switch(state, mode_field, switch_why)

    # Security assessment
    if (
        "security_assessment" in reasoning_data
        and state.security_assessment != reasoning_data["security_assessment"]
    ):
        state.security_assessment = reasoning_data["security_assessment"]
        changed = True

    # Persist only if we actually changed something
    if changed:
        autosave(state)


def get_situated_context(state: State) -> str:
    """Get user context from Horizon 1 - UserProfile for prompt injection."""
    profile = state.profile
    if not profile or not any([profile.preferences, profile.goals, profile.expertise_areas]):
        return ""

    context_parts = []
    if profile.communication_style:
        context_parts.append(f"Style: {profile.communication_style}")
    if profile.preferences:
        # Show key preferences
        pref_strs = [f"{k}: {v}" for k, v in list(profile.preferences.items())[:3]]
        context_parts.append(f"Preferences: {', '.join(pref_strs)}")
    if profile.expertise_areas:
        context_parts.append(f"Expertise: {', '.join(profile.expertise_areas[:3])}")
    if profile.projects:
        recent_projects = list(profile.projects.items())[-2:]
        context_parts.append(f"Projects: {', '.join(f'{k}: {v}' for k, v in recent_projects)}")

    return f"USER CONTEXT: {' | '.join(context_parts)}\n\n" if context_parts else ""


def compress_for_context(state: State, max_tokens: int = 1000) -> str:
    """Compress workspace from Horizon 2 for LLM context."""
    sections = []
    workspace = state.workspace

    if workspace.objective:
        sections.append(f"OBJECTIVE: {workspace.objective}")
    if workspace.assessment:
        sections.append(f"ASSESSMENT: {workspace.assessment}")
    if workspace.approach:
        sections.append(f"APPROACH: {workspace.approach}")
    if workspace.facts:
        recent_facts = list(workspace.facts.items())[-5:]
        facts_str = "; ".join(f"{k}: {v}" for k, v in recent_facts)
        sections.append(f"FACTS: {facts_str}")
    if workspace.insights:
        recent_insights = workspace.insights[-3:]
        sections.append(f"INSIGHTS: {'; '.join(recent_insights)}")
    if workspace.observations:
        recent_obs = workspace.observations[-3:]
        sections.append(f"OBSERVATIONS: {'; '.join(recent_obs)}")
    if workspace.thoughts:
        last_thought = workspace.thoughts[-1]
        sections.append(f"LAST THINKING: {last_thought['thinking'][:200]}")

    result = "\n".join(sections)
    return result[:max_tokens] if len(result) > max_tokens else result
