"""Anthropic provider."""

import os
from typing import List, Dict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def generate(prompt: str = None, messages: List[Dict] = None, model: str = "claude-sonnet-4-20250514") -> str:
    """Generate response using Anthropic Claude."""
    
    try:
        import anthropic
    except ImportError:
        return "Please install anthropic: pip install anthropic"
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Please set ANTHROPIC_API_KEY environment variable."
    
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    # Convert messages to Anthropic format
    if messages:
        anthropic_messages = []
        system_content = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n\n"
            elif msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Create message with system prompt if present
        kwargs = {"model": model, "messages": anthropic_messages, "max_tokens": 1000}
        if system_content.strip():
            kwargs["system"] = system_content.strip()
        
        response = await client.messages.create(**kwargs)
        return response.content[0].text
        
    elif prompt:
        # Handle string prompt directly
        response = await client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.content[0].text
    
    else:
        return "No prompt or messages provided."