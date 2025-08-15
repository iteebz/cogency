"""Google Gemini provider."""

import os
from typing import List, Dict, Any


async def generate(prompt: str = None, messages: List[Dict] = None, model: str = "gemini-2.5-flash-lite") -> str:
    """Generate response using Google Gemini."""
    
    try:
        import google.genai as genai
    except ImportError:
        raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    # Convert messages to Gemini format
    if messages:
        gemini_messages = []
        system_instruction = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction += msg["content"] + "\n\n"
            elif msg["role"] == "user":
                gemini_messages.append(genai.types.Content(
                    role="user",
                    parts=[genai.types.Part.from_text(msg["content"])]
                ))
            elif msg["role"] == "assistant":
                gemini_messages.append(genai.types.Content(
                    role="model", 
                    parts=[genai.types.Part.from_text(msg["content"])]
                ))
        
        # Create config with system instruction if present
        config = {"model": model}
        if system_instruction.strip():
            config["system_instruction"] = system_instruction.strip()
        
        response = client.models.generate_content(
            config=config,
            contents=gemini_messages
        )
        
        return response.candidates[0].content.parts[0].text
        
    elif prompt:
        # Handle string prompt directly
        response = client.models.generate_content(
            config={"model": model},
            contents=[genai.types.Content(
                role="user",
                parts=[genai.types.Part.from_text(prompt)]
            )]
        )
        return response.candidates[0].content.parts[0].text
    
    else:
        return "No prompt or messages provided."