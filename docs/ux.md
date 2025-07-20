# Agent UX Specification

## Core Principles
1. **Only show non-obvious reasoning** - Skip "I need weather tool for weather"
2. **Collapse redundant steps** - Dense, scannable output
3. **Make it scannable at a glance** - Visual hierarchy through emojis
4. **Human-readable parameters** - `weather(Tokyo)` not `weather(city=Tokyo, units=celsius)`
5. **Progressive disclosure** - Simple cases stay simple, complexity only when needed

## Visual Grammar

### Message Types
- `👤` Human input
- `🤖` Agent final response  
- `🧠` Non-obvious reasoning (rare but important)
- `💾` Memory operations
- `❌` Errors

### Tool-Specific Emojis
- `🌤️` weather
- `🧮` calculator  
- `🔍` web_search
- `📁` file operations
- `⏰` time/date
- `🌐` http requests
- `💻` shell/code
- `🧠` memory/recall
- `🛠️` fallback for unmapped tools

### Format Rules
- **No ceremony spacing** - Each line has purpose
- **New space = new message** in conversation chain
- **Human-readable params**: `calculator($120 × 3)` not raw JSON
- **Contextual results**: `→ 25°C sunny` not full API response
- **No spacing** between emoji and text
- **One space** after arrows

## Examples

### Simple Cases (No ceremony)
```
👤 What's 2+2?
🤖 4

👤 Weather in Tokyo?
🌤️ weather(Tokyo) → 25°C sunny
🤖 It's 25°C and sunny in Tokyo.
```

### Memory Cases  
```
👤 Remember I like pizza and work at Google
💾 User likes pizza, works at Google
🤖 Got it! I'll remember you like pizza and work at Google.

👤 What do you know about me?
🧠 You like pizza and work at Google.
🤖 Based on what you've told me: you like pizza and work at Google.
```

### Multi-tool Cases
```
👤 Weather in London and calculate trip cost: $450 flight + $120/night × 3 nights
🌤️ weather(London) → 18°C light rain
🧮 calculator($120 × 3) → $360
🧮 calculator($360 + $450) → $810
🤖 London: 18°C with light rain. Trip cost: $810 ($450 flight + $360 hotels).
```

### Non-obvious Reasoning (rare but important)
```
👤 Find Python jobs in Tokyo that pay over $100k
🔍 web_search(Python jobs Tokyo salary) → 12 results found
🧠 Need to filter by salary - most listings don't show pay upfront
🔍 web_search(Python developer salary Tokyo USD) → Average $85k-$120k
🧠 Search results show salary ranges, need specific openings
🔍 web_search(Python jobs Tokyo $100k+ remote) → 3 high-paying positions
🤖 Found 3 Python positions in Tokyo over $100k: [details...]
```

### Error Handling
```
👤 Weather in Atlantis
🌤️ weather(Atlantis) → ❌ City not found
🤖 I couldn't find weather for Atlantis - it's not a real location. Did you mean Atlanta?
```

## Implementation Notes

**Tool emoji mapping** should be maintained in a simple dictionary with 🛠️ as fallback.

**Parameter formatting** should extract meaningful values:
- File paths: show filename not full path
- URLs: show domain not full URL  
- Large numbers: format with commas/currency
- Long strings: truncate with ellipsis

**Result formatting** should be contextual:
- Weather: temperature + condition
- Calculator: just the number
- Search: result count or key finding
- Files: success confirmation or error

**Reasoning display** only when the next step isn't obvious from context. Skip obvious transitions like "Now I'll use the calculator tool to calculate X."

This creates a **visual protocol** where each emoji type has semantic meaning, making agent behavior instantly scannable and understandable.