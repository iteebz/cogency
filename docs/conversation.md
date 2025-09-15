# Conversation Context Specification

**Canonical conversation context format for HTTP streaming replay**

This document defines the canonical format for conversation context reconstruction, used specifically for HTTP streaming replay when a ReAct cycle is interrupted and needs continuation.

## Format Structure

```
=== HISTORY ===
(showing last 15 of 73 messages)

$user: How do I read the configuration file?

$respond: I'll help you read the configuration file

$call: {"name": "file_read", "args": {"file": "config.yml"}}

$result: Read config.yml

database:
  host: localhost
  port: 5432
  name: myapp

$respond: I found your database configuration settings

=== CURRENT ===

$user: What's in test.txt?

$think: The user is asking to read 'test.txt'. I should use file_read to get the contents

$call: {"name": "file_read", "args": {"file": "test.txt"}}

$result: Read test.txt

This is test file content
Line 2 of the test file
More content here

$respond: I have successfully read the file 'test.txt'
```

## Canonical Decisions

### Delimiters
- **Protocol consistency**: Use `$user:` `$respond:` `$think:` `$call:` `$result:`
- **Reinforcement**: Matches protocol delimiters (`§user:` `§respond:` etc.)
- **Learning**: Context becomes living example of protocol usage

### Structure
- **Sections**: HISTORY + CURRENT with `=== SECTION ===` separators
- **Spacing**: `\n\n` between all protocol events for visual clarity
- **Single line headers**: `=== HISTORY ===` format for clean presentation

### Content Rules

#### HISTORY Section
- **Purpose**: Past conversational context before current cycle
- **Truncation**: Show last N messages if conversation is long
- **Metrics**: Include count if truncated: `(showing last N of M messages)`
- **Content preservation**: Tools handle their own truncation at semantic boundaries
- **Thinking excluded**: No `$think:` events in history for clean conversational flow

#### CURRENT Section  
- **Purpose**: Complete current ReAct cycle for continuation
- **Completeness**: ALWAYS show full chain, never truncate
- **Starting point**: Begins with `$user:` message that triggered cycle
- **Full detail**: Include all `$think:`, `$call:`, `$result:`, `$respond:` events
- **No truncation**: Show complete tool results regardless of length

### Tool Formatting
- **Call format**: JSON exactly as protocol expects: `{"name": "tool", "args": {...}}`
- **Result format**: Use agent formatting (outcome + content) from `format_result_agent()`
- **Always paired**: Every `$call:` MUST have corresponding `$result:`
- **Error handling**: Show errors in results: `File not found` etc.

### Truncation Strategy
- **Tool responsibility**: Tools handle their own output truncation at semantic boundaries
- **Context-aware**: File tools truncate at function boundaries, search tools summarize results
- **No arbitrary limits**: Eliminates fixed character counts that break mid-sentence or mid-concept
- **Semantic preservation**: Important context retained, noise eliminated by domain experts (the tools)

## Usage Contexts

### When CURRENT Section Appears
- **HTTP streaming replay**: Mid-cycle interruption recovery
- **ReAct continuation**: When cycle was interrupted and needs completion

### When CURRENT Section Does NOT Appear  
- **New conversations**: System prompt + user message only
- **Resume mode**: System prompt + user message only
- **First iteration**: No prior cycle to continue

## Implementation Notes

- Context formatting uses `format_call_agent()` and `format_result_agent()` from `tools/format.py`
- Database stores individual events, context reconstructs into this canonical format
- HISTORY pulls from conversation history before last user message
- CURRENT pulls from conversation events after last user message
- Protocol consistency ensures LLM sees familiar syntax for continuation

**This specification is canonical for conversation context reconstruction.**