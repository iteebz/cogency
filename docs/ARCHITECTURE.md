# Architecture

**Key innovations:** WebSocket streaming, delimiter protocol, dual-mode execution, stateless orchestration

## Context Replay Elimination

**Traditional:** Full context replay every tool call
```python
agent.run() → [Messages 1-50] → Tool → [Messages 1-51] → Tool
# Token cost: Linear growth with conversation length
```

**Cogency:** Bidirectional stream maintains context  
```python
agent() → Stream pauses → Tool executes → Stream resumes
# Token cost: Constant regardless of conversation length
```

## Stateless Orchestration

**Agent orchestration:** Pure functional execution
**State boundaries:** Context assembly and WebSocket sessions

```python
agent = Agent()  # Configuration closure
result = await agent(query)  # Stateless execution
```

Context assembled on-demand from storage:
- **Orchestration layer:** Pure functions
- **Context assembly:** State management wrapper  
- **Resume mode:** WebSocket state machine

## Execution Modes

**Resume:** WebSocket bidirectional streaming
- Single persistent connection
- Context injection without replay
- Constant token usage

**Replay:** HTTP request per tool cycle  
- Fresh request after each tool call
- Context grows with conversation
- Universal provider compatibility

**Auto:** WebSocket with HTTP fallback
- Resume when available, replay otherwise
- Production recommended

## Context Assembly

Dynamic context from:
- System prompt + tool registry
- User profile (if available)  
- Conversation history
- Current query

**Resume mode:** Inject without context growth
**Replay mode:** Append to message history

## Provider Interface

```python
# All providers implement
async def stream(self, messages) -> AsyncGenerator[str, None]

# WebSocket providers add
async def connect(self, messages) -> session
async def send(self, session, content) -> bool
async def receive(self, session) -> AsyncGenerator[str, None] 
async def close(self, session) -> bool
```

## Provider Support

| Provider | Resume (WebSocket) | Replay (HTTP) |
|----------|-------------------|---------------|
| OpenAI | Realtime API | All models |
| Gemini | Live API | All models |
| Anthropic | None | All models |

## Performance Characteristics

**Token efficiency** (theoretical):
- Resume: Constant context size
- Replay: Linear context growth
- Estimated 6x improvement for multi-step tasks

**Latency:**
- Resume: Sub-second tool injection
- Replay: Full request cycle per tool