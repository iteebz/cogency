"""Response shaping system - transforms raw cognitive output into final format."""
from typing import Dict, Any, Optional
from cogency.llm import BaseLLM


class ResponseShaper:
    """Transforms raw cognitive output into desired format/tone/style."""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    
    async def shape(self, raw_response: str, config: Dict[str, Any]) -> str:
        """Shape raw response according to config."""
        if not config:
            return raw_response
            
        # Build shaping prompt from config
        shaping_prompt = self._build_shaping_prompt(config)
        
        messages = [
            {"role": "system", "content": shaping_prompt},
            {"role": "user", "content": f"Transform this response:\n\n{raw_response}"}
        ]
        
        return await self.llm.invoke(messages)
    
    def _build_shaping_prompt(self, config: Dict[str, Any]) -> str:
        """Build shaping prompt from config."""
        prompt_parts = ["Transform the following response according to these specifications:"]
        
        # Format transformation
        if "format" in config:
            format_type = config["format"]
            if format_type == "multi-aip-json":
                prompt_parts.append(self._get_aip_format_instructions())
            elif format_type == "markdown":
                prompt_parts.append("- Format as clean markdown")
            elif format_type == "html":
                prompt_parts.append("- Format as semantic HTML")
        
        # Tone and style
        if "tone" in config:
            prompt_parts.append(f"- Use {config['tone']} tone")
        
        if "style" in config:
            prompt_parts.append(f"- Apply {config['style']} style")
        
        # Constraints
        if "constraints" in config:
            for constraint in config["constraints"]:
                prompt_parts.append(f"- {constraint.replace('-', ' ').title()}")
        
        # Transformations
        if "transformations" in config:
            for transform in config["transformations"]:
                prompt_parts.append(f"- {transform.replace('-', ' ').title()}")
        
        return "\n".join(prompt_parts)
    
    def _get_aip_format_instructions(self) -> str:
        """Get AIP format instructions."""
        return """- Format as MULTI-AIP JSON - series of AIP-compliant JSON objects, each on its own line

Available interface types:
- markdown: {"type": "markdown", "content": "text"}
- blog-post: {"type": "blog-post", "data": {"title": "Title", "content": "Content", "metadata": {}}}
- card-grid: {"type": "card-grid", "data": {"cards": [{"title": "Name", "description": "Desc", "tags": [], "links": [], "metadata": {}}]}}
- code-snippet: {"type": "code-snippet", "data": {"code": "console.log('hello')", "language": "javascript"}}
- expandable-section: {"type": "expandable-section", "data": {"sections": [{"title": "Title", "content": "Content", "defaultExpanded": false}]}}
- inline-reference: {"type": "inline-reference", "data": {"references": [{"id": "ref1", "title": "Title", "type": "project", "excerpt": "Brief", "content": "Full content"}]}}
- key-insights: {"type": "key-insights", "data": {"insights": [{"title": "Insight", "description": "Description", "category": "category"}]}}
- timeline: {"type": "timeline", "data": {"events": [{"date": "2025", "title": "Event", "description": "Desc"}]}}

Use expandable-section for CoT reasoning, key-insights for analysis, and mix narrative with structured data."""


# Prebuilt shaping profiles
SHAPING_PROFILES = {
    "folio_aip": {
        "format": "multi-aip-json",
        "tone": "professional-approachable",
        "style": "technical-precision-human-warmth",
        "constraints": ["use-first-person", "include-reasoning"],
        "transformations": ["add-cot-expandable", "highlight-key-insights"]
    },
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