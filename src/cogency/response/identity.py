"""Identity and system prompt composition for consistent agent personality."""
from typing import Dict, Any, Optional


def compose_system_prompt(opts: Dict[str, Any]) -> str:
    """Compose system prompt from agent options.
    
    Handles:
    - Custom system prompts
    - Personality injection
    - Tone and style directives
    - Default helpful assistant fallback
    
    Args:
        opts: Agent configuration options
        
    Returns:
        Composed system prompt string
    """
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


def get_identity_context(opts: Dict[str, Any]) -> Dict[str, Any]:
    """Extract identity-related context from agent options.
    
    Returns:
        Dict containing personality, tone, style for response shaping
    """
    return {
        k: v for k, v in {
            "personality": opts.get("personality"),
            "tone": opts.get("tone"), 
            "style": opts.get("style")
        }.items() if v is not None
    }