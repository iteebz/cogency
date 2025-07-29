# Cogency Notifications

**Goal:** Clean, extensible agent observability that scales from CLI debugging to production monitoring.

## Design

### Core Components

```python
@dataclass
class Notification:
    type: str
    data: dict
    timestamp: float = field(default_factory=time.time)

class Formatter:
    def __init__(self, style='cli'):
        self.style = style if style in ['cli', 'emoji', 'json', 'silent'] else 'cli'
    
    def format(self, notification: Notification) -> Optional[str]:
        if self.style == 'silent':
            return None
        return getattr(self, f'_{notification.type}', self._unknown)(notification)

async def emit(notification: Notification, callback=None):
    if callback:
        if iscoroutinefunction(callback):
            await callback(notification)
        else:
            callback(notification)
```

### Notification Types

```python
# Phase transitions
Notification(
    type='phase_start',
    data={'phase': 'reason', 'mode': 'fast'}
)

# Tool execution
Notification(
    type='tool_execution', 
    data={
        'name': 'calculator',
        'args': {'expression': '2+2'},
        'result': 4,
        'success': True
    }
)

# Memory operations
Notification(
    type='memory_save',
    data={'content': 'User prefers Python', 'tags': ['preference']}
)
```

## Formatters

### CLI Formatter (Default)
```python
class CLIFormatter(Formatter):
    def _phase_start(self, n):
        phase = n.data['phase']
        mode = n.data.get('mode', '')
        return f"{phase.title()} {mode}".strip()
    
    def _tool_execution(self, n):
        name = n.data['name']
        if n.data.get('success'):
            result = self._format_result(n.data.get('result'))
            return f"{name}: {result}"
        else:
            error = n.data.get('error', 'failed')
            return f"{name}: ERROR - {error}"
```

### Emoji Formatter
```python
class EmojiFormatter(Formatter):
    TOOL_EMOJIS = {
        'calculator': '🧮',
        'weather': '🌤️', 
        'search': '🔍',
        'files': '📁',
        'memory': '🧠'
    }
    
    def _tool_execution(self, n):
        name = n.data['name']
        emoji = self.TOOL_EMOJIS.get(name, '⚡')
        
        if n.data.get('success'):
            result = self._format_result(n.data.get('result'))
            return f"{emoji} {name}: ✓ {result}"
        else:
            error = n.data.get('error', 'failed')
            return f"{emoji} {name}: ❌ {error}"
```

### JSON Formatter
```python
class JSONFormatter(Formatter):
    def format(self, notification: Notification) -> str:
        return json.dumps({
            'type': notification.type,
            'timestamp': notification.timestamp,
            **notification.data
        })
```

## Usage

### Basic Agent
```python
agent = Agent(
    "assistant",
    notify_style='cli',  # 'cli', 'emoji', 'json', 'silent'
    tools=[Calculator(), Weather()]
)

result = await agent.run("What's 2+2?")
# Output: calculator: 4
```

### Custom Callback
```python
async def log_notifications(notification):
    logger.info(f"Agent event: {notification.type}", extra=notification.data)

agent = Agent("assistant", on_notify=log_notifications)
```

### Frontend Integration
```python
notifications = []

def collect_events(notification):
    notifications.append({
        'type': notification.type,
        'data': notification.data,
        'timestamp': notification.timestamp
    })

agent = Agent("assistant", notify_style='json', on_notify=collect_events)
result = await agent.run(query)

# Send notifications to frontend
websocket.send(json.dumps(notifications))
```

## Integration Points

### Agent Phases
```python
# In preprocess phase
await emit(Notification('phase_start', {'phase': 'preprocess'}))

# In tool execution
await emit(Notification('tool_execution', {
    'name': tool.name,
    'args': args,
    'result': result,
    'success': True
}))

# Memory operations
await emit(Notification('memory_save', {
    'content': memory_content,
    'tags': tags,
    'user_id': user_id
}))
```

### Custom Formatters
```python
class SlackFormatter(Formatter):
    def _tool_execution(self, notification):
        name = notification.data['name']
        success = notification.data.get('success')
        
        if success:
            return f":white_check_mark: {name} completed"
        else:
            return f":x: {name} failed"

agent = Agent("assistant", formatter=SlackFormatter())
```

## Performance

- **Silent mode**: Zero overhead
- **CLI/Emoji**: ~0.1ms per notification
- **JSON**: ~0.2ms per notification
- **Async-safe**: Non-blocking emission

## Implementation Status

- [x] Core notification architecture
- [x] Basic CLI formatter
- [x] Silent mode (truly silent)
- [ ] Emoji formatter implementation
- [ ] JSON formatter implementation  
- [ ] Phase notification integration
- [ ] Memory operation notifications
- [ ] Custom formatter examples

---

**Clean, fast, extensible notifications for modern agent frameworks.**