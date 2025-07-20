"""Consolidated response handling - identity, shaping, and formatting."""
import json
from typing import Dict, Any, Optional, Union
from cogency.llm import BaseLLM


def compose_system_prompt(opts: Dict[str, Any]) -> str:
    """Compose system prompt from agent options."""
    if opts.get('system_prompt'):
        return opts['system_prompt']
    
    parts = [f"You are {opts.get('personality', 'a helpful AI assistant')}."]
    
    if opts.get('tone') or opts.get('style'):
        style_parts = [
            f"{k}: {v}" for k, v in [
                ("tone", opts.get('tone')), 
                ("style", opts.get('style'))
            ] if v
        ]
        parts.append(f"Communicate with {', '.join(style_parts)}.")
    
    parts.append("Always be helpful, accurate, and thoughtful in your responses.")
    return " ".join(parts)


async def shape_response(
    raw_response: str,
    llm: BaseLLM,
    config: Optional[Dict[str, Any]] = None
) -> Union[str, Dict[str, Any]]:
    """Shape response according to config. Returns raw response if no config."""
    if not config:
        return raw_response

    # Build shaping prompt from config
    prompt_parts = ["Transform the following response according to these specifications:"]

    # Format transformation
    if "format" in config:
        format_type = config["format"]
        if format_type == "markdown":
            prompt_parts.append("- Format as clean markdown")
        elif format_type == "html":
            prompt_parts.append("- Format as semantic HTML")

    # Tone and style
    if "tone" in config:
        prompt_parts.append(f"- Use {config['tone']} tone")
    if "style" in config:
        prompt_parts.append(f"- Apply {config['style']} style")
    if "personality" in config:
        prompt_parts.append(f"- Personality: {config['personality']}")

    # Constraints and transformations
    for key in ["constraints", "transformations"]:
        if key in config:
            for item in config[key]:
                prompt_parts.append(f"- {item.replace('-', ' ').title()}")

    shaping_prompt = "\n".join(prompt_parts)
    messages = [
        {"role": "system", "content": shaping_prompt},
        {"role": "user", "content": f"Transform this response:\n\n{raw_response}"}
    ]

    return await llm.invoke(messages)


# Prebuilt shaping profiles for common use cases
SHAPING_PROFILES = {
    "markdown_clean": {
        "format": "markdown",
        "tone": "clear-concise",
        "style": "technical-documentation"
    },
    "conversational": {
        "tone": "friendly-helpful",
        "style": "natural-dialogue",
        "constraints": ["use-contractions", "ask-clarifying-questions"]
    }
}