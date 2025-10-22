# Cogency Evals Context

## Quick Reference

```bash
poetry run evals coding --llm openai --mode resume --samples 2 --seed 42
poetry run evals --llm openai --mode resume --samples 2  # All categories
```

Modes: `replay` (HTTP), `resume` (WebSocket realtime)  
Categories: `reasoning`, `conversation`, `continuity`, `coding`, `research`, `security`, `integrity`

## Session 4: Delimiter Protocol Investigation

### Findings

Both gpt-4o-mini (HTTP) and gpt-4o-mini-realtime (WebSocket) receive identical system instructions with full protocol specification. **They behave completely differently.**

#### HTTP Replay Mode (responses.create API) ✅
- **Output**: Text with proper `§think:`, `§call:`, `§respond:`, `§execute`, `§end` delimiters
- **Parser**: Correctly extracts delimiters → creates think/call/respond/execute/result/end events
- **Events generated**: 16 events from single test (full workflow with 3 tool calls)
- **Tokens**: [35029, 8799] properly extracted
- **Workflow**: Think → Call → Execute → Result → Respond cycle repeats, ends with §end

Example output:
```
§think: To build a REST API, I'll need to create three files...

§call: {"name": "write", "args": {"file": "models.py", "content": "..."}}

§execute

§respond: Now that models.py is set up...

§call: {"name": "write", "args": {"file": "app.py", ...}}
```

#### WebSocket Resume Mode (realtime API) ❌
- **Output**: JSON without delimiters: `{"path": "."}`
- **Parser**: No delimiters found → defaults to "respond" type
- **Events generated**: 2 events, truncated (only USER + RESPOND)
- **Tokens**: [0, 0] (no §execute events to trigger metrics)
- **Workflow**: Single incomplete response, immediate exit

### Root Cause: Model Training Difference

**Hypothesis**: gpt-4o-mini-realtime is fine-tuned for real-time conversation and trained to ignore custom delimiter protocols.

**Evidence**:
- Identical system prompt sent to both endpoints (verified via logging)
- Parser is identical (works correctly in both cases when delimiters present)
- **Only difference**: LLM output format
- Realtime outputs raw JSON (looks like attempted built-in function calling, not protocol)

**Not a code bug** - the instructions reach the model, the model just ignores them.

### Practical Implications
- **Use HTTP replay mode** for proper testing (full protocol adherence, token counting works)
- **WebSocket resume mode unusable** with current gpt-4o-mini-realtime variant
- Alternative: Test with different LLM provider that respects instruction-based protocols

## Fixes Applied

**runner.py:177,188** - Changed `type=="metrics"` to `type=="metric"` (singular)  
**openai.py:127** - Verified `"output_modalities": ["text"]` (was correct)  
**openai.py:123** - Added debug logging for session instructions
