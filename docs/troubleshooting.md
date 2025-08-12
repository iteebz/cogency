# Troubleshooting

## Installation

```bash
pip install cogency

# If problems:
pip install --upgrade pip
pip install -v cogency
```

## API Keys

```bash
# Set any provider
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
export MISTRAL_API_KEY=...
export GROQ_API_KEY=...
export NOMIC_API_KEY=...

# Or .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

## Common Issues

**"No API key found"**
- Set environment variable for any provider
- Auto-detects available keys

**"Agent execution failed"**
- Check API key validity
- Verify internet connection
- Try different provider: `Agent("assistant", llm=Anthropic())`

**"Tool execution failed"**
- Check file permissions for Files tool
- Verify commands exist for Shell tool
- Check internet connectivity for Search/Scrape tools

**"Memory not persisting"**
- Verify write permissions to `.cogency/` directory
- Check disk space availability

**"Slow responses"**
- Use `mode="fast"` for simple queries
- Reduce `max_iterations` for quicker responses
- Disable notifications with `notify=False`

**"Too many iterations"**
- Increase `max_iterations` for complex tasks
- Use `mode="deep"` for thorough analysis

## Debug Mode

```python
# Enable detailed logging
agent = Agent("assistant", handlers=[debug_handler])

# Or check logs directory
ls .cogency/logs/
```

## Provider-Specific Issues

**OpenAI:**
- Verify API key format starts with `sk-`
- Check quota and billing status

**Anthropic:**
- Verify API key format starts with `sk-ant-`
- Check usage limits

**Local providers (Ollama):**
- Ensure Ollama is running: `ollama serve`
- Set base URL: `export OPENAI_BASE_URL="http://localhost:11434/v1"`

## Performance

**Memory usage:**
- Disable memory for stateless usage: `memory=False`
- Reduce tool count for minimal overhead

**Response time:**
- Use `mode="fast"` for simple queries
- Reduce `max_iterations` for time limits

---

*Troubleshooting for Cogency v1.2.2*