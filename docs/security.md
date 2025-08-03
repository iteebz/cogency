# Security

Three-layer defensive architecture protecting against prompt injection, command injection, and output manipulation.

## Quick Start

```python
from cogency import Agent
from cogency.security import SecurityLevel

# Default: All security layers enabled
agent = Agent("assistant", security=SecurityLevel.HIGH)
result = await agent.run("Analyze this file")  # Protected execution
```

## Architecture

### Layer 1: Input Validation
- **Location**: `src/cogency/security/input.py`
- **Purpose**: Block malicious prompts before processing
- **Patterns**: Command injection, prompt override attempts

### Layer 2: Execution Control  
- **Location**: `src/cogency/security/execution.py`
- **Purpose**: Sanitize tool arguments and shell commands
- **Patterns**: `rm -rf`, `$(whoami)`, `curl | sh`, `/etc/passwd`

### Layer 3: Output Sanitization
- **Location**: `src/cogency/security/output.py` 
- **Purpose**: Detect response hijacking and data exfiltration
- **Patterns**: "COMPROMISED", "system prompt", massive repetition

## Security Evaluation

```bash
poetry run python -m evals.main security
```

**Test Coverage**:
- Direct prompt injection (5 attack vectors)
- Shell command injection (6 injection patterns) 
- Indirect file-based injection (3 attack types)
- Context overflow resistance (3 exhaustion methods)

**Framework**: Declarative test cases with fresh agent instances per test.

## Configuration

```python
# Disable for development/testing only
agent = Agent("dev", security=SecurityLevel.NONE)

# Custom security patterns
from cogency.security import add_custom_pattern
add_custom_pattern("execution", r"dangerous_command")
```

## Implementation Notes

- **Agent Factory Pattern**: Fresh instances prevent context pollution
- **Timeout Protection**: 60s limits prevent hanging on massive inputs  
- **Minimal Overhead**: Fast mode execution, <30s per security suite
- **Zero False Positives**: Legitimate operations remain unblocked