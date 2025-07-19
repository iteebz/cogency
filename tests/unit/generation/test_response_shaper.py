"""Test ResponseShaper integration."""
import pytest
from cogency import Agent
from cogency.generation.shaper import ResponseShaper, SHAPING_PROFILES
from cogency.llm import GeminiLLM
from unittest.mock import Mock


class TestResponseShaper:
    """Test ResponseShaper functionality."""
    
    
        
    def test_shaping_profiles_exist(self):
        """Test that predefined shaping profiles exist."""
        assert "folio_aip" in SHAPING_PROFILES
        assert "markdown_clean" in SHAPING_PROFILES
        assert "conversational" in SHAPING_PROFILES
        
        # Test folio_aip profile structure
        folio_profile = SHAPING_PROFILES["folio_aip"]
        assert folio_profile["format"] == "multi-aip-json"
        assert "tone" in folio_profile
        assert "style" in folio_profile
        assert "constraints" in folio_profile
        assert "transformations" in folio_profile
        
    def test_response_shaper_build_prompt(self):
        """Test prompt building from config."""
        llm = GeminiLLM()
        shaper = ResponseShaper(llm)
        
        config = {
            "format": "markdown",
            "tone": "friendly",
            "style": "technical",
            "constraints": ["use-first-person"],
            "transformations": ["add-examples"]
        }
        
        prompt = shaper._build_shaping_prompt(config)
        
        assert "markdown" in prompt.lower()
        assert "friendly" in prompt.lower()
        assert "technical" in prompt.lower()
        assert "first person" in prompt.lower()
        assert "examples" in prompt.lower()
        
    def test_aip_format_instructions(self):
        """Test AIP format instructions are comprehensive."""
        llm = Mock()
        shaper = ResponseShaper(llm)
        
        aip_instructions = shaper._get_aip_format_instructions()
        
        # Check for key AIP component types
        assert "markdown" in aip_instructions
        assert "card-grid" in aip_instructions
        assert "expandable-section" in aip_instructions
        assert "key-insights" in aip_instructions
        assert "timeline" in aip_instructions
        assert "code-snippet" in aip_instructions
        assert "blog-post" in aip_instructions
        assert "inline-reference" in aip_instructions