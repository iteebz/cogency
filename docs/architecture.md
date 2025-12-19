# Architecture

## Pipeline

**Tokens → Parser → Accumulator → Executor → Results**

### Parser (Lexical Layer)
- **Function**: XML marker and JSON extraction from token stream
- **Input**: Token stream from LLM
- **Output**: Semantic events with type labels
- **Strategy**: Detect `<think>`, `<execute>`, `<results>` markers across token boundaries

See [execution.md](execution.md) for the complete protocol specification.

```python
# Input token stream:
"<execute>\n[" → buffered
'{"name":"read"' → buffered
',"args":{"file":"test.py"}}' → buffered
"]</execute>" → complete, parse and emit call events

# Output events:
{"type": "call", "content": '{"name": "read", "args": {"file": "test.py"}}'}
{"type": "execute"}
```

### Accumulator (Semantic Layer)
- **Function**: Event assembly with streaming control and tool execution
- **Input**: Parser events stream  
- **Output**: Complete semantic units + tool results
- **Streaming Modes**: 
  - `stream="token"`: Stream individual parser events immediately (real-time)
  - `stream="event"`: Accumulate and batch complete semantic units (coherent thoughts)
  - `stream=None`: Non-streaming, use LLM.generate() for complete response

```python
# stream="token": Individual events as generated
{"type": "think", "content": "I need", "timestamp": 1.0}
{"type": "think", "content": " to analyze", "timestamp": 1.1} 
{"type": "think", "content": " this", "timestamp": 1.2}

# stream="event": Complete accumulated unit
{"type": "think", "content": "I need to analyze this", "timestamp": 1.0}
```

### Executor (Tool Layer)  
- **Function**: Tool invocation and result handling
- **Input**: Structured call data from accumulator
- **Output**: Tool execution results
- **Strategy**: Parallel batch execution via asyncio.gather
- **Tools**: read, write, edit, list, find, replace, search, scrape, recall, shell

## Execution Modes

### Resume (WebSocket)

Session persists server-side. Tool results injected into same stream.

```
Connect → Stream → Pause → Execute → Inject Results → Resume → Stream
```

- Constant token usage per iteration
- Sub-second tool injection
- Providers: OpenAI Realtime API, Gemini Live API

### Replay (HTTP)

Fresh request per iteration. Context rebuilt from storage.

```
Request → Response → Execute → Request (with history) → Response
```

- Context grows with conversation
- Universal provider compatibility
- Providers: All (OpenAI, Anthropic, Gemini)

### Auto (Default)

WebSocket when available, HTTP fallback. Production recommended.

## Token Efficiency

| Turns | Replay O(n²) | Resume O(n) | Savings |
|-------|--------------|-------------|---------|
| 8 | 31,200 | 6,000 | 5.2x |
| 16 | 100,800 | 10,800 | 9.3x |
| 32 | 355,200 | 20,400 | 17.4x |

Resume efficiency grows linearly with conversation depth.

## Stateless Design

Agent and context assembly are pure functions. All state externalized to storage.

```python
agent = Agent(llm="openai")  # Configuration only
async for event in agent(query):  # Rebuilds context from storage
    process(event)
```

**Persist-then-rebuild:**
1. Parser emits events from token stream
2. Accumulator persists every event immediately
3. Context assembly rebuilds from storage each iteration
4. Single source of truth eliminates stale state bugs

## Context Assembly

Two-layer architecture separates storage from protocol.

**Storage:** Clean events without delimiters
```python
{"type": "think", "content": "checking logs"}
{"type": "call", "content": '{"name": "read", ...}'}
{"type": "result", "content": '{"outcome": "Success", ...}'}
```

**Assembly:** Proper messages with synthesized delimiters
```python
{"role": "system", "content": "PROTOCOL + TOOLS + PROFILE"}
{"role": "user", "content": "debug this"}
{"role": "assistant", "content": "<think>checking logs</think>\n\n<execute>[...]</execute>"}
{"role": "user", "content": "<results>[...]</results>"}
```

**Context components:**
- System message: Protocol + tools + profile (if enabled)
- Conversation messages: User/assistant turns from storage
- Notifications: Optional system messages injected between iterations (if notification source provided)
- Execution format: XML markers with JSON arrays synthesized during assembly
- Tool results: Injected as user messages (required by Realtime/Live APIs)

**Cost and memory control:**
- `history_window=None` - Full conversation history (default). Database loads all events.
- `history_window=20` - Last 20 messages. Database loads only last 40 events (multiplied by 2 to account for granular call batching).

When `history_window` is set, storage loads only that bounded set. Prevents token cost and context overflow in long conversations. Load is O(history_window), not O(total_conversation_length).

**Resume mode:** Context sent once at connection, no replay
**Replay mode:** Context rebuilt from storage each iteration (bounded by history_window)

## Provider Interface

```python
# All providers implement
async def stream(self, messages) -> AsyncGenerator[str, None]
async def generate(self, messages) -> str

# WebSocket providers add
async def connect(self, messages) -> LLM  # Returns session-enabled instance
async def send(self, content) -> AsyncGenerator[str, None]  # Session method
async def close(self) -> None
```

| Provider | Resume (WebSocket) | Replay (HTTP) |
|----------|-------------------|---------------|
| OpenAI | Realtime API | All models |
| Gemini | Live API | All models |
| Anthropic | None | All models |

## Performance

**Token usage:**
- Resume: Constant per iteration (session state maintained)
- Replay: Grows with conversation (context rebuilt each time)
- Mathematical analysis in [proof.md](proof.md)

**Latency:**
- Resume: Sub-second tool injection
- Replay: Full request cycle per iteration

## Security Architecture

### Semantic Security Layer
- **Function**: LLM reasoning detects malicious intent and prompt attacks
- **Strategy**: Uses natural language understanding vs pattern matching
- **Coverage**: Prompt injection, jailbreaking, system access attempts
- **Implementation**: Integrated in system prompt reasoning (`context/system.py`)

### Tool Security Layer  
- **Function**: Input validation and resource limits at execution boundary
- **Strategy**: Path safety, command sanitization, resource constraints
- **Coverage**: File access, command execution, network operations
- **Implementation**: Per-tool validation in `core/security.py`

Defense in depth: Semantic reasoning catches intent, execution validation catches mistakes.
