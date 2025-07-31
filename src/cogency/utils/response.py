"""Response formatting utilities - zero ceremony, maximum beauty."""

import json
from typing import Optional


def format_response(
    content: str,
    identity: Optional[str] = None,
    output_schema: Optional[str] = None,
) -> str:
    """Format response with identity and JSON validation if needed."""

    # Apply identity framing if provided
    if identity and not output_schema:
        # For early returns, content is already appropriately formatted
        pass

    # Handle JSON formatting if schema provided
    if output_schema:
        try:
            # Try to parse as JSON first
            json.loads(content)
            return content  # Already valid JSON
        except (json.JSONDecodeError, TypeError):
            # Wrap plain text in basic JSON structure
            return json.dumps({"response": content})

    return content


def apply_identity_template(content: str, identity: Optional[str] = None) -> str:
    """Apply identity framing to content."""
    if not identity:
        return content

    # Simple identity prefix for now - could be enhanced with templates
    return f"As {identity}: {content}"


def validate_json_response(content: str, schema: Optional[str] = None) -> str:
    """Validate and format JSON response."""
    if not schema:
        return content

    try:
        # Validate JSON structure
        parsed = json.loads(content)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        # Wrap in basic schema if invalid
        return json.dumps({"response": str(content)}, indent=2)
