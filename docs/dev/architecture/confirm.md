# Confirmation Architecture Specification

**Status:** Approved (CR-2025-001)  
**Implementation:** Event-driven system capability  

## Overview

Confirmation is implemented as a system-level capability triggered by agent intent signals, not as a tool agents call. This preserves natural dialogue flow while enforcing deterministic safety boundaries.

## Architecture

### Agent Layer: Natural Language Signaling

Agents communicate confirmation needs through tagged dialogue:

```python
# Agent expresses uncertainty/risk through natural conversation
agent_response = "I'm about to delete these 500 user accounts. Should I proceed?"

# System detects intent metadata automatically
intent_metadata = {
    "confirmation_required": True,
    "risk_level": "critical", 
    "action_type": "batch_delete",
    "scope": {"records": 500, "type": "user_accounts"}
}
```

**No tool calls required.** Agents use conversational patterns to signal confirmation needs.

### System Layer: Automatic Detection & Enforcement

The routing layer monitors for confirmation intents and:

1. **HALT**: Pause agent execution pending user response
2. **RENDER**: Present structured UI (buttons, not free text)  
3. **RESOLVE**: Convert user input to binary decision
4. **RESUME**: Return deterministic boolean to agent

### Risk Heuristics

System triggers confirmation based on:

- **Irreversibility**: No simple undo mechanism exists
- **Magnitude**: Large-scale operations (>100 records, >$1000, etc.)
- **Domain criticality**: Production vs sandbox systems
- **Agent uncertainty**: Explicit uncertainty expressions

## Implementation Details

### Intent Detection Patterns

```python
# High-risk patterns that trigger confirmation
CONFIRMATION_PATTERNS = [
    r"delete.*\d+.*(?:records|files|users)",
    r"(?:rm|remove).*-r.*",
    r"drop.*(?:table|database)",
    r"should I proceed",
    r"this will (?:delete|remove|overwrite)",
]

# Risk assessment
def assess_risk(command: str, context: dict) -> RiskLevel:
    if any(pattern in command.lower() for pattern in HIGH_RISK_COMMANDS):
        return RiskLevel.CRITICAL
    if context.get("production", False):
        return RiskLevel.HIGH
    return RiskLevel.LOW
```

### UI Specification

```typescript
interface ConfirmationUI {
    message: string;           // Agent's natural language request
    action: ActionDetail;      // Structured action description
    risk_level: RiskLevel;     // Visual styling cue
    show_details: boolean;     // Expandable action inspection
    buttons: ["Proceed", "Cancel"];  // Binary choice only
}
```

### Event Logging

```python
@dataclass
class ConfirmationEvent:
    timestamp: datetime
    agent_reasoning: str       # Full reasoning trace
    proposed_action: dict      # Exact action payload
    risk_assessment: RiskLevel
    user_response: bool
    final_action: Optional[dict]  # What actually executed
```

## Tool Integration

### Shell Tool Example

```python
async def shell_execute(command: str) -> Result:
    risk = assess_risk(command, context)
    
    if risk >= RiskLevel.HIGH:
        # System automatically handles confirmation UI
        confirmed = await system.request_confirmation(
            message=f"Execute: {command}",
            risk_level=risk,
            action_detail={"command": command, "type": "shell"}
        )
        
        if not confirmed:
            return Result.fail("User cancelled operation")
    
    # Proceed with execution
    return await execute_command(command)
```

## Benefits

- **No tool ceremony**: Agents use natural dialogue
- **Deterministic safety**: System enforces confirmation boundaries  
- **Clean architecture**: Separation of communication and control
- **Intelligent friction**: Only when genuinely needed

## Future Considerations

1. **Agent Training**: Fine-tune models to emit correct intent signals
2. **UI Patterns**: Standardize confirmation interface components
3. **Risk Tuning**: Adjust heuristics based on usage patterns
4. **Audit Integration**: Connect event logs to compliance systems

## Migration Path

1. Remove `ask` tool from tool registry
2. Implement intent detection in routing layer
3. Add confirmation UI components
4. Update existing tools to use system confirmation
5. Train agents on new confirmation patterns

This architecture eliminates confirmation tool complexity while maintaining safety through intelligent system-level enforcement.